import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import init_db, get_db
from app.config import get_settings
from app.auth.utils import get_current_user_from_query
from app.auth.models import User
from app.models.execution import Execution, TestCase, TestStep, Screenshot

logger = logging.getLogger(__name__)


class SSEManager:
    _queues: dict[str, asyncio.Queue] = {}
    _locks: dict[str, asyncio.Lock] = {}
    _event_history: dict[str, list[dict]] = {}

    @classmethod
    def _ensure_queue(cls, execution_id: str):
        if execution_id not in cls._queues:
            cls._queues[execution_id] = asyncio.Queue()
            cls._locks[execution_id] = asyncio.Lock()
            cls._event_history[execution_id] = []

    @classmethod
    async def subscribe(cls, execution_id: str):
        cls._ensure_queue(execution_id)
        queue = cls._queues[execution_id]

        for event in cls._event_history.get(execution_id, []):
            yield f"data: {json.dumps(event)}\n\n"

        yield f"data: {json.dumps({'type': 'connected', 'execution_id': execution_id})}\n\n"

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            raise

    @classmethod
    async def emit(cls, execution_id: str, event: dict):
        cls._ensure_queue(execution_id)
        cls._event_history.setdefault(execution_id, []).append(event)
        await cls._queues[execution_id].put(event)

    @classmethod
    async def cleanup(cls, execution_id: str):
        await asyncio.sleep(30)
        cls._queues.pop(execution_id, None)
        cls._locks.pop(execution_id, None)
        cls._event_history.pop(execution_id, None)


class PlaywrightExecutor:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.settings = get_settings()

    async def execute(self, execution_id: str, plan: dict, headless: bool = True):
        from playwright.async_api import async_playwright

        async with self.db_session_factory() as db:
            execution = await db.get(Execution, execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return

            try:
                execution.status = "RUNNING"
                execution.started_at = datetime.now(timezone.utc)
                await db.commit()

                await SSEManager.emit(execution_id, {
                    "type": "execution_started",
                    "execution_id": execution_id,
                    "total_test_cases": len(plan.get("test_cases", [])),
                })

                plan_test_cases = plan.get("test_cases", [])
                passed_count = 0
                failed_count = 0
                blocked_count = 0

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=headless)
                    context = await browser.new_context(
                        viewport={"width": 1280, "height": 720},
                        ignore_https_errors=True,
                    )

                    steps_order = 0
                    for tc_index, plan_tc in enumerate(plan_test_cases):
                        tc_name = plan_tc.get("name", f"Test Case {tc_index + 1}")
                        tc_module = plan_tc.get("module", "Default")

                        tc_db = await db.execute(
                            select(TestCase).where(
                                TestCase.execution_id == execution_id,
                                TestCase.order_index == tc_index,
                            )
                        )
                        tc_db = tc_db.scalar_one_or_none()

                        if not tc_db:
                            tc_db = TestCase(
                                execution_id=execution_id,
                                name=tc_name,
                                module=tc_module,
                                order_index=tc_index,
                                total_steps=len(plan_tc.get("steps", [])),
                                status="RUNNING",
                                started_at=datetime.now(timezone.utc),
                            )
                            db.add(tc_db)
                            await db.flush()

                        tc_db.status = "RUNNING"
                        tc_db.started_at = datetime.now(timezone.utc)
                        await db.commit()

                        await SSEManager.emit(execution_id, {
                            "type": "test_case_started",
                            "test_case_index": tc_index,
                            "test_case_name": tc_name,
                            "total_steps": len(plan_tc.get("steps", [])),
                        })

                        page = await context.new_page()
                        tc_failed = False
                        steps_passed = 0
                        steps_failed = 0

                        for step_data in plan_tc.get("steps", []):
                            step_order = step_data.get("order", steps_order + 1)
                            steps_order = step_order
                            step_desc = step_data.get("description", "")
                            intent = step_data.get("intent", "")
                            pw_action = step_data.get("playwright_action", {})

                            step_db = TestStep(
                                test_case_id=tc_db.id,
                                order_index=step_order,
                                description=step_desc,
                                intent=intent,
                                target=step_data.get("target"),
                                value=step_data.get("value"),
                                playwright_action=json.dumps(pw_action),
                                status="RUNNING",
                                started_at=datetime.now(timezone.utc),
                            )
                            db.add(step_db)
                            await db.flush()

                            await SSEManager.emit(execution_id, {
                                "type": "step_started",
                                "test_case_index": tc_index,
                                "step_order": step_order,
                                "step_description": step_desc,
                                "intent": intent,
                            })

                            step_start = datetime.now(timezone.utc)

                            try:
                                await self._execute_step(page, pw_action, step_db)
                                step_db.status = "PASSED"
                                steps_passed += 1

                                duration = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
                                step_db.duration_ms = duration
                                step_db.completed_at = datetime.now(timezone.utc)

                                screenshot_info = await self._capture_screenshot(page, execution_id, step_db.id, db)

                                await SSEManager.emit(execution_id, {
                                    "type": "step_completed",
                                    "test_case_index": tc_index,
                                    "step_order": step_order,
                                    "status": "PASSED",
                                    "screenshot_id": screenshot_info["id"],
                                    "screenshot_filename": screenshot_info["filename"],
                                    "duration_ms": duration,
                                })

                            except Exception as e:
                                step_db.status = "FAILED"
                                step_db.error_message = str(e)
                                steps_failed += 1
                                tc_failed = True

                                duration = (datetime.now(timezone.utc) - step_start).total_seconds() * 1000
                                step_db.duration_ms = duration
                                step_db.completed_at = datetime.now(timezone.utc)

                                try:
                                    screenshot_info = await self._capture_screenshot(page, execution_id, step_db.id, db)
                                except Exception:
                                    screenshot_info = None

                                await SSEManager.emit(execution_id, {
                                    "type": "step_completed",
                                    "test_case_index": tc_index,
                                    "step_order": step_order,
                                    "status": "FAILED",
                                    "error": str(e),
                                    "screenshot_id": screenshot_info["id"] if screenshot_info else None,
                                    "screenshot_filename": screenshot_info["filename"] if screenshot_info else None,
                                    "duration_ms": duration,
                                })

                                for remaining in plan_tc.get("steps", [])[step_order:]:
                                    skip_db = TestStep(
                                        test_case_id=tc_db.id,
                                        order_index=remaining.get("order", step_order + 1),
                                        description=remaining.get("description", ""),
                                        intent=remaining.get("intent", ""),
                                        target=remaining.get("target"),
                                        value=remaining.get("value"),
                                        playwright_action=json.dumps(remaining.get("playwright_action", {})),
                                        status="SKIPPED",
                                    )
                                    db.add(skip_db)
                                    await SSEManager.emit(execution_id, {
                                        "type": "step_completed",
                                        "test_case_index": tc_index,
                                        "step_order": remaining.get("order"),
                                        "status": "SKIPPED",
                                    })
                                break

                            await db.commit()

                        await page.close()

                        tc_db.passed_steps = steps_passed
                        tc_db.failed_steps = steps_failed
                        tc_db.status = "FAILED" if tc_failed else "PASSED"
                        tc_db.completed_at = datetime.now(timezone.utc)

                        if tc_failed:
                            failed_count += 1
                        else:
                            passed_count += 1

                        await SSEManager.emit(execution_id, {
                            "type": "test_case_completed",
                            "test_case_index": tc_index,
                            "test_case_name": tc_name,
                            "status": tc_db.status,
                            "passed": steps_passed,
                            "failed": steps_failed,
                        })

                        await db.commit()

                    await context.close()
                    await browser.close()

                start_time = execution.started_at
                end_time = datetime.now(timezone.utc)
                duration = (end_time - start_time).total_seconds() if start_time else 0

                execution.status = "COMPLETED"
                execution.passed = passed_count
                execution.failed = failed_count
                execution.blocked = blocked_count
                execution.completed_at = end_time
                execution.duration_seconds = duration
                execution.total_test_cases = len(plan_test_cases)
                await db.commit()

                await SSEManager.emit(execution_id, {
                    "type": "execution_completed",
                    "execution_id": execution_id,
                    "status": "COMPLETED",
                    "passed": passed_count,
                    "failed": failed_count,
                    "blocked": blocked_count,
                    "duration_seconds": duration,
                })

            except Exception as e:
                logger.exception(f"Execution {execution_id} failed: {e}")
                execution.status = "FAILED"
                execution.error_message = str(e)
                execution.completed_at = datetime.now(timezone.utc)
                await db.commit()
                await SSEManager.emit(execution_id, {
                    "type": "execution_completed",
                    "execution_id": execution_id,
                    "status": "FAILED",
                    "passed": 0,
                    "failed": 0,
                    "blocked": 0,
                    "error": str(e),
                    "duration_seconds": 0,
                })

            await SSEManager.cleanup(execution_id)

    async def _execute_step(self, page, pw_action: dict, step_db: TestStep):
        method = pw_action.get("method", "")

        if method == "goto":
            url = pw_action.get("url", "")
            if not url:
                raise ValueError("No URL provided for goto action")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_load_state("networkidle")

        elif method == "reload":
            await page.reload(wait_until="domcontentloaded")
            await page.wait_for_load_state("networkidle")

        elif method == "go_back":
            await page.go_back()
            await page.wait_for_load_state("networkidle")

        elif method == "fill":
            text = pw_action.get("text", "")
            await self._smart_fill(page, pw_action.get("locator", {}), text)

        elif method == "type_text":
            text = pw_action.get("text", "")
            await page.keyboard.type(text, delay=50)

        elif method == "type":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            text = pw_action.get("text", "")
            await locator.type(text, delay=50)

        elif method == "click":
            await self._smart_click(page, pw_action.get("locator", {}))

        elif method == "dblclick":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.dblclick(timeout=10000)

        elif method == "select_option":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            option = pw_action.get("option", "")
            await locator.select_option(option)

        elif method == "check":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.check(timeout=10000)

        elif method == "uncheck":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.uncheck(timeout=10000)

        elif method == "press":
            key = pw_action.get("key", "")
            await page.keyboard.press(key)

        elif method == "wait_for_selector":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.wait_for(state="visible", timeout=15000)

        elif method == "wait_for_timeout":
            ms = pw_action.get("ms", 2000)
            await page.wait_for_timeout(ms)

        elif method == "assert_text_visible":
            text = pw_action.get("text", "")
            try:
                await page.locator(f"text={text}").first.wait_for(state="visible", timeout=12000)
            except Exception:
                try:
                    visible_text = await page.locator("body").inner_text()
                    snippet = visible_text[:500] if len(visible_text) > 500 else visible_text
                except Exception:
                    snippet = "(could not read page content)"
                raise AssertionError(
                    f"Expected text '{text}' to be visible, but it was not found on page. "
                    f"Page visible text: {snippet[:300]}"
                )

        elif method == "assert_text_not_visible":
            text = pw_action.get("text", "")
            try:
                await page.locator(f"text={text}").first.wait_for(state="visible", timeout=8000)
                raise AssertionError(
                    f"Expected text '{text}' to NOT be visible, but it IS currently visible on the page."
                )
            except AssertionError:
                raise
            except Exception:
                pass

        elif method == "assert_url_contains":
            expected = pw_action.get("text", "")
            current_url = page.url
            if expected not in current_url:
                raise AssertionError(
                    f"Expected URL to contain '{expected}', but current URL is '{current_url}'"
                )

        elif method == "assert_url_equals":
            expected = pw_action.get("text", "")
            current_url = page.url
            if expected != current_url:
                raise AssertionError(
                    f"Expected URL to be '{expected}', but current URL is '{current_url}'"
                )

        elif method == "assert_title_contains":
            expected = pw_action.get("text", "")
            try:
                title = await page.title()
            except Exception:
                title = "(could not read page title)"
            if expected.lower() not in title.lower():
                raise AssertionError(
                    f"Expected page title to contain '{expected}', but title is '{title}'"
                )

        elif method == "assert_title_equals":
            expected = pw_action.get("text", "")
            try:
                title = await page.title()
            except Exception:
                title = "(could not read page title)"
            if expected.lower() != title.lower():
                raise AssertionError(
                    f"Expected page title to be '{expected}', but title is '{title}'"
                )

        elif method == "assert_element_visible":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            try:
                await locator.wait_for(state="visible", timeout=12000)
            except Exception:
                try:
                    visible_text = await page.locator("body").inner_text()
                    snippet = visible_text[:500] if len(visible_text) > 500 else visible_text
                except Exception:
                    snippet = "(could not read page content)"
                raise AssertionError(
                    f"Expected element to be visible, but it was not found on page. "
                    f"Page visible text: {snippet[:300]}"
                )

        elif method == "hover":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.hover()

        elif method == "scroll_into_view":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.scroll_into_view_if_needed()

        else:
            raise ValueError(f"Unknown Playwright method: {method}")

    async def _smart_fill(self, page, locator_info: dict, text: str):
        value = locator_info.get("value", "").strip() if locator_info else ""
        strategies = []
        if value:
            lower_val = value.lower()
            if "password" in lower_val:
                strategies = [
                    lambda: page.get_by_placeholder(value),
                    lambda: page.get_by_label(value),
                    lambda: page.locator("input[type='password']"),
                    lambda: page.get_by_role("textbox", name=value),
                ]
            elif "user" in lower_val or "username" in lower_val or "email" in lower_val:
                strategies = [
                    lambda: page.get_by_placeholder(value),
                    lambda: page.get_by_label(value),
                    lambda: page.locator("input[type='text']"),
                    lambda: page.locator("input[type='email']"),
                    lambda: page.get_by_role("textbox", name=value),
                ]
            else:
                strategies = [
                    lambda: page.get_by_placeholder(value),
                    lambda: page.get_by_label(value),
                    lambda: page.get_by_role("textbox", name=value),
                    lambda: page.locator(f"[name*='{value}']"),
                ]
        strategies.append(lambda: None)

        last_error = None
        for strategy in strategies:
            try:
                locator = strategy()
                if locator is None:
                    await page.keyboard.type(text, delay=30)
                    return
                await locator.click(timeout=3000)
                await locator.fill("")
                await locator.type(text, delay=30)
                return
            except Exception as e:
                last_error = e
                continue
        raise last_error or ValueError(f"Could not find field to fill with text '{text}'")

    async def _smart_click(self, page, locator_info: dict):
        value = locator_info.get("value", "").strip() if locator_info else ""
        name = locator_info.get("name", "").strip() if locator_info else ""
        search = name or value or ""
        if not search:
            raise ValueError("No element description provided for click action")

        strategies = [
            lambda: page.get_by_role("button", name=search),
            lambda: page.get_by_text(search, exact=False),
            lambda: page.get_by_role("link", name=search),
            lambda: page.get_by_label(search),
            lambda: page.get_by_placeholder(search),
            lambda: page.get_by_test_id(search),
            lambda: page.locator(f"text={search}"),
            lambda: page.locator(f"button:has-text('{search}')"),
            lambda: page.locator(f"a:has-text('{search}')"),
        ]

        last_error = None
        for strategy_fn in strategies:
            try:
                locator = strategy_fn()
                await locator.first.click(timeout=5000)
                try:
                    await page.wait_for_load_state("networkidle")
                except Exception:
                    pass
                return
            except Exception as e:
                last_error = e
                continue
        raise last_error or ValueError(f"Could not find clickable element '{search}' on page")

    def _resolve_locator(self, page, locator_info: dict):
        strategy = locator_info.get("strategy", "text")
        value = locator_info.get("value", "")
        if strategy == "role":
            name = locator_info.get("name", value)
            return page.get_by_role(value, name=name)
        elif strategy == "label":
            return page.get_by_label(value)
        elif strategy == "placeholder":
            return page.get_by_placeholder(value)
        elif strategy == "text":
            return page.get_by_text(value, exact=False)
        elif strategy == "alt":
            return page.get_by_alt_text(value)
        elif strategy == "title":
            return page.get_by_title(value)
        elif strategy == "testid":
            return page.get_by_test_id(value)
        elif strategy == "css":
            return page.locator(value)
        else:
            return page.get_by_text(value, exact=False)

    async def _capture_screenshot(self, page, execution_id: str, step_id: str, db: AsyncSession) -> dict:
        settings = get_settings()
        os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
        exec_dir = os.path.join(settings.SCREENSHOTS_DIR, execution_id)
        os.makedirs(exec_dir, exist_ok=True)

        filename = f"{step_id}.png"
        filepath = os.path.join(exec_dir, filename)
        await page.screenshot(path=filepath, full_page=False)

        screenshot = Screenshot(
            step_id=step_id,
            execution_id=execution_id,
            filename=filename,
            filepath=filepath,
            captured_at=datetime.now(timezone.utc),
        )
        db.add(screenshot)
        await db.flush()
        return {"id": screenshot.id, "filename": filename, "filepath": filepath}


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings = get_settings()
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
    yield


app = FastAPI(title="Testcase Executor — Playwright Service", version="1.0.0", lifespan=lifespan)

settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "playwright-executor"}


@app.post("/execute")
async def trigger_execution(request: Request, db: AsyncSession = Depends(get_db)):
    internal_secret = request.headers.get("X-Internal-Secret", "")
    if internal_secret != settings.RAILWAY_INTERNAL_SECRET:
        raise HTTPException(status_code=403, detail="Unauthorized")

    body = await request.json()
    execution_id = body.get("execution_id")
    plan = body.get("plan", {})
    headless = body.get("headless", True)

    if not execution_id:
        raise HTTPException(status_code=400, detail="execution_id is required")

    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")

    from app.database import async_session as session_factory
    executor = PlaywrightExecutor(session_factory)
    asyncio.create_task(executor.execute(execution_id, plan, headless))

    return {"status": "RUNNING", "execution_id": execution_id}


@app.get("/sse/{execution_id}")
async def stream_execution(execution_id: str, request: Request, current_user: User = Depends(get_current_user_from_query)):
    async def event_generator():
        async for event in SSEManager.subscribe(execution_id):
            if await request.is_disconnected():
                break
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/screenshots/{execution_id}/{step_id}")
async def serve_screenshot(
    execution_id: str,
    step_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    settings = get_settings()
    internal_secret = request.headers.get("X-Internal-Secret", "")

    if internal_secret == settings.RAILWAY_INTERNAL_SECRET and internal_secret:
        pass
    else:
        token = request.query_params.get("token", "")
        if not token:
            raise HTTPException(status_code=401)
        from jose import jwt, JWTError
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = int(payload.get("sub"))
        except (JWTError, ValueError):
            raise HTTPException(status_code=401)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=401)

    result = await db.execute(
        select(Screenshot).where(
            Screenshot.execution_id == execution_id,
            Screenshot.step_id == step_id,
        )
    )
    screenshots = result.scalars().all()
    if not screenshots:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    screenshot = screenshots[0]

    if internal_secret == settings.RAILWAY_INTERNAL_SECRET and internal_secret:
        execution = await db.get(Execution, execution_id)
    else:
        execution = await db.get(Execution, execution_id)
        if not execution or execution.user_id != user.id:
            raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(screenshot.filepath, media_type="image/png")
