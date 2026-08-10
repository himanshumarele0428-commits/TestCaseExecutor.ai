import asyncio
import json
import logging
import os
from datetime import datetime, timezone
from typing import AsyncGenerator, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.execution import Execution, TestCase, TestStep, Screenshot
from app.config import get_settings

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
    async def subscribe(cls, execution_id: str) -> AsyncGenerator[str, None]:
        cls._ensure_queue(execution_id)
        queue = cls._queues[execution_id]

        for event in cls._event_history.get(execution_id, []):
            yield f"data: {json.dumps(event)}\n\n"

        yield "data: {\"type\": \"connected\", \"execution_id\": \"" + execution_id + "\"}\n\n"

        try:
            while True:
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=30)
                    yield f"data: {json.dumps(data)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keepalive\n\n"
        except asyncio.CancelledError:
            logger.debug(f"SSE subscription cancelled for {execution_id}")
            raise

    @classmethod
    async def emit(cls, execution_id: str, event: dict):
        cls._ensure_queue(execution_id)
        cls._event_history.setdefault(execution_id, []).append(event)
        await cls._queues[execution_id].put(event)

    @classmethod
    async def cleanup(cls, execution_id: str):
        await asyncio.sleep(30)
        if execution_id in cls._queues:
            del cls._queues[execution_id]
        if execution_id in cls._locks:
            del cls._locks[execution_id]
        if execution_id in cls._event_history:
            del cls._event_history[execution_id]


class PlaywrightExecutor:
    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.settings = get_settings()

    async def execute(self, execution_id: str, plan: dict, headless: bool = False):
        from playwright.async_api import async_playwright

        async with self.db_session_factory() as db:
            execution = await db.get(Execution, execution_id)
            if not execution:
                logger.error(f"Execution {execution_id} not found")
                return

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
                        step_order = step_data.get("order", 1)
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

                            screenshot_info = await self._capture_screenshot(
                                page, execution_id, step_db.id, db
                            )

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
                                screenshot_info = await self._capture_screenshot(
                                    page, execution_id, step_db.id, db
                                )
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

            await SSEManager.cleanup(execution_id)

    async def _execute_step(self, page, pw_action: dict, step_db: TestStep):
        method = pw_action.get("method", "")

        if method == "goto":
            url = pw_action.get("url", "")
            if not url:
                raise ValueError("No URL provided for goto action")
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)

        elif method == "reload":
            await page.reload(wait_until="domcontentloaded")

        elif method == "go_back":
            await page.go_back()

        elif method == "fill":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            text = pw_action.get("text", "")
            await locator.click()
            await locator.fill("")
            await locator.type(text, delay=30)

        elif method == "type_text":
            text = pw_action.get("text", "")
            await page.keyboard.type(text, delay=50)

        elif method == "type":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            text = pw_action.get("text", "")
            await locator.type(text, delay=50)

        elif method == "click":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.click(timeout=10000)

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
            await page.get_by_text(text).first.wait_for(state="visible", timeout=10000)

        elif method == "hover":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.hover()

        elif method == "scroll_into_view":
            locator = self._resolve_locator(page, pw_action.get("locator", {}))
            await locator.scroll_into_view_if_needed()

        else:
            raise ValueError(f"Unknown Playwright method: {method}")

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

    async def _capture_screenshot(
        self, page, execution_id: str, step_id: str, db: AsyncSession
    ) -> dict:
        os.makedirs(self.settings.SCREENSHOTS_DIR, exist_ok=True)
        exec_dir = os.path.join(self.settings.SCREENSHOTS_DIR, execution_id)
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
