import json
import logging
import csv
import io
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from app.database import get_db, async_session
from app.auth.utils import get_current_user, get_current_user_from_query
from app.auth.models import User
from app.models.execution import Execution, TestCase, TestStep, Screenshot
from app.models.api_key import ApiKey
from app.services.parser import parse_test_file
from app.services.ai_planner import generate_execution_plan
from app.services.playwright_service import PlaywrightExecutor, SSEManager
from app.services.encryption import decrypt_value
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_user_groq_key(db: AsyncSession, user_id: int) -> str:
    settings = get_settings()
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == user_id, ApiKey.is_active == True)
    )
    api_key_row = result.scalar_one_or_none()
    if api_key_row:
        return decrypt_value(api_key_row.encrypted_key)
    return settings.GROQ_API_KEY


@router.post("")
async def create_execution(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    filename = request.get("filename", "unknown")
    file_content = request.get("file_content", "")
    parsed = request.get("parsed_test_cases", [])

    if not parsed:
        raise HTTPException(status_code=400, detail="No test cases provided")

    execution = Execution(
        user_id=current_user.id,
        filename=filename,
        file_content=file_content,
        status="QUEUED",
        total_test_cases=len(parsed),
    )
    db.add(execution)
    await db.flush()

    for idx, tc_data in enumerate(parsed):
        test_case = TestCase(
            execution_id=execution.id,
            name=tc_data.get("name", f"Test Case {idx + 1}"),
            module=tc_data.get("module"),
            priority=tc_data.get("priority"),
            environment=tc_data.get("environment"),
            order_index=idx,
            total_steps=len(tc_data.get("steps", [])),
            status="QUEUED",
        )
        db.add(test_case)

    await db.commit()
    await db.refresh(execution)

    return {
        "id": execution.id,
        "filename": execution.filename,
        "status": execution.status,
        "total_test_cases": execution.total_test_cases,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
    }


@router.post("/{execution_id}/execute")
async def execute_test_cases(
    execution_id: str,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await request.json() if await request.body() else {}
    headless = body.get("headless", False)
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if execution.status in ("RUNNING",):
        raise HTTPException(status_code=400, detail="Execution is already in progress")

    parsed = parse_test_file(execution.file_content or "", execution.filename)
    if not parsed:
        raise HTTPException(status_code=400, detail="No test cases found in the file")

    stored_test_cases = await db.execute(
        select(TestCase).where(TestCase.execution_id == execution_id).order_by(TestCase.order_index)
    )
    stored_tc_list = stored_test_cases.scalars().all()

    from app.services.step_mapper import build_execution_plan

    plan = build_execution_plan(parsed)

    unmapped_count = sum(
        1 for tc in plan.get("test_cases", [])
        for s in tc.get("steps", [])
        if not s.get("playwright_action")
    )

    if unmapped_count > 0:
        logger.warning(f"{unmapped_count} step(s) could not be directly mapped")

        groq_key = await _get_user_groq_key(db, current_user.id)
        if groq_key:
            settings = get_settings()
            result = await db.execute(
                select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
            )
            api_key_row = result.scalar_one_or_none()
            model = None
            if api_key_row and api_key_row.model_name:
                model = api_key_row.model_name

            try:
                parsed_list = [tc for tc in parsed]
                plan = await generate_execution_plan(parsed_list, groq_key, model or settings.GROQ_MODEL)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Failed to generate execution plan: {e}")
                raise HTTPException(status_code=500, detail=f"AI planning failed: {str(e)}")
        else:
            logger.info("No Groq API key — proceeding with heuristic fallback mapping for all steps")

    execution.status = "QUEUED"
    execution.file_content = execution.file_content or ""
    if parsed:
        execution.total_test_cases = len(parsed)
    plan_tcs = plan.get("test_cases", [])

    for idx, plan_tc in enumerate(plan_tcs):
        db_tc = stored_tc_list[idx] if idx < len(stored_tc_list) else None
        if db_tc:
            db_tc.name = plan_tc.get("name", db_tc.name)
            db_tc.module = plan_tc.get("module", db_tc.module)
            db_tc.total_steps = len(plan_tc.get("steps", []))
            db_tc.status = "QUEUED"
            db_tc.passed_steps = 0
            db_tc.failed_steps = 0

    await db.commit()

    executor = PlaywrightExecutor(async_session)
    background_tasks.add_task(executor.execute, execution_id, plan, headless)

    return {
        "execution_id": execution_id,
        "status": "QUEUED",
        "message": f"Execution started in {'headless' if headless else 'headed'} mode.",
        "total_test_cases": len(plan_tcs),
    }


@router.get("/{execution_id}")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.execution_id == execution_id)
        .order_by(TestCase.order_index)
    )
    test_cases = tc_result.scalars().all()

    tc_list = []
    for tc in test_cases:
        steps_result = await db.execute(
            select(TestStep).where(TestStep.test_case_id == tc.id).order_by(TestStep.order_index)
        )
        steps = steps_result.scalars().all()

        step_list = []
        for step in steps:
            ss_result = await db.execute(
                select(Screenshot).where(Screenshot.step_id == step.id)
            )
            screenshots = ss_result.scalars().all()
            step_list.append({
                "id": step.id,
                "order_index": step.order_index,
                "description": step.description,
                "intent": step.intent,
                "target": step.target,
                "value": step.value,
                "status": step.status,
                "error_message": step.error_message,
                "duration_ms": step.duration_ms,
                "screenshots": [
                    {"id": ss.id, "filename": ss.filename, "execution_id": ss.execution_id}
                    for ss in screenshots
                ],
            })

        tc_list.append({
            "id": tc.id,
            "name": tc.name,
            "module": tc.module,
            "priority": tc.priority,
            "order_index": tc.order_index,
            "status": tc.status,
            "total_steps": tc.total_steps,
            "passed_steps": tc.passed_steps,
            "failed_steps": tc.failed_steps,
            "steps": step_list,
        })

    return {
        "id": execution.id,
        "filename": execution.filename,
        "status": execution.status,
        "total_test_cases": execution.total_test_cases,
        "passed": execution.passed,
        "failed": execution.failed,
        "blocked": execution.blocked,
        "duration_seconds": execution.duration_seconds,
        "started_at": execution.started_at.isoformat() if execution.started_at else None,
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "test_cases": tc_list,
    }


@router.get("")
async def list_executions(
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count(Execution.id)).where(Execution.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(Execution)
        .where(Execution.user_id == current_user.id)
        .order_by(desc(Execution.created_at))
        .offset(offset)
        .limit(page_size)
    )
    executions = result.scalars().all()

    return {
        "items": [
            {
                "id": e.id,
                "filename": e.filename,
                "status": e.status,
                "total_test_cases": e.total_test_cases,
                "passed": e.passed,
                "failed": e.failed,
                "duration_seconds": e.duration_seconds,
                "created_at": e.created_at.isoformat() if e.created_at else None,
            }
            for e in executions
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.post("/{execution_id}/rerun")
async def rerun_execution(
    execution_id: str,
    background_tasks: BackgroundTasks,
    mode_req: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    body = await mode_req.json() if await mode_req.body() else {}
    headless = body.get("headless", False)
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not execution.file_content:
        raise HTTPException(status_code=400, detail="No file content stored for this execution")

    parsed = parse_test_file(execution.file_content, execution.filename)
    if not parsed:
        raise HTTPException(status_code=400, detail="No test cases found in stored file content")

    from app.services.step_mapper import build_execution_plan

    plan = build_execution_plan(parsed)
    parsed_list = [tc for tc in parsed]

    unmapped_count = sum(
        1 for tc in plan.get("test_cases", [])
        for s in tc.get("steps", [])
        if not s.get("playwright_action")
    )

    if unmapped_count > 0:
        groq_key = await _get_user_groq_key(db, current_user.id)
        if groq_key:
            model = None
            settings = get_settings()
            api_key_result = await db.execute(
                select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
            )
            api_key_row = api_key_result.scalar_one_or_none()
            if api_key_row and api_key_row.model_name:
                model = api_key_row.model_name

            try:
                plan = await generate_execution_plan(parsed_list, groq_key, model or settings.GROQ_MODEL)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Failed to generate execution plan: {e}")
                raise HTTPException(status_code=500, detail=f"AI planning failed: {str(e)}")
        else:
            logger.info("No Groq API key — proceeding with heuristic fallback mapping for rerun")

    new_execution = Execution(
        user_id=current_user.id,
        filename=execution.filename,
        file_content=execution.file_content,
        status="QUEUED",
        total_test_cases=len(parsed_list),
    )
    db.add(new_execution)
    await db.flush()

    for idx, tc_data in enumerate(parsed_list):
        plan_tc = plan["test_cases"][idx] if idx < len(plan["test_cases"]) else {}
        test_case = TestCase(
            execution_id=new_execution.id,
            name=plan_tc.get("name", tc_data.name),
            module=plan_tc.get("module", tc_data.module),
            priority=tc_data.priority,
            environment=tc_data.environment,
            order_index=idx,
            total_steps=len(plan_tc.get("steps", tc_data.steps)),
            status="QUEUED",
        )
        db.add(test_case)

    await db.commit()

    executor = PlaywrightExecutor(async_session)
    background_tasks.add_task(executor.execute, new_execution.id, plan, headless)

    return {
        "execution_id": new_execution.id,
        "status": "QUEUED",
        "message": "Re-execution started with a new execution entry.",
        "total_test_cases": len(plan["test_cases"]),
    }


@router.delete("/{execution_id}")
async def delete_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    test_cases = (await db.execute(
        select(TestCase).where(TestCase.execution_id == execution_id)
    )).scalars().all()

    for tc in test_cases:
        steps = (await db.execute(
            select(TestStep).where(TestStep.test_case_id == tc.id)
        )).scalars().all()
        for step in steps:
            screenshots = (await db.execute(
                select(Screenshot).where(Screenshot.step_id == step.id)
            )).scalars().all()
            for ss in screenshots:
                await db.delete(ss)
            await db.delete(step)
        await db.delete(tc)

    await db.delete(execution)
    await db.commit()

    return {"message": "Execution deleted successfully"}


@router.get("/{execution_id}/stream")
async def stream_execution(
    execution_id: str,
    request: Request,
    current_user: User = Depends(get_current_user_from_query),
):
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


@router.get("/{execution_id}/export")
async def export_execution_csv(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    if execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    tc_result = await db.execute(
        select(TestCase)
        .where(TestCase.execution_id == execution_id)
        .order_by(TestCase.order_index)
    )
    test_cases = tc_result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "Execution ID", "File", "Status", "Total TCs", "Passed", "Failed",
        "Duration (s)", "Started", "Completed",
    ])
    writer.writerow([
        execution.id, execution.filename, execution.status,
        execution.total_test_cases, execution.passed, execution.failed,
        f"{execution.duration_seconds:.1f}" if execution.duration_seconds else "-",
        execution.started_at.isoformat() if execution.started_at else "-",
        execution.completed_at.isoformat() if execution.completed_at else "-",
    ])

    writer.writerow([])
    writer.writerow([
        "TC Name", "Module", "Priority", "TC Status", "Total Steps",
        "Passed Steps", "Failed Steps", "Step #", "Step Description",
        "Intent", "Target", "Value", "Step Status", "Duration (ms)", "Error",
    ])

    for tc in test_cases:
        steps_result = await db.execute(
            select(TestStep).where(TestStep.test_case_id == tc.id).order_by(TestStep.order_index)
        )
        steps = steps_result.scalars().all()

        if not steps:
            writer.writerow([
                tc.name, tc.module or "-", tc.priority or "-", tc.status,
                tc.total_steps, tc.passed_steps, tc.failed_steps,
                "-", "-", "-", "-", "-", "-", "-", "-",
            ])
        else:
            for step in steps:
                writer.writerow([
                    tc.name, tc.module or "-", tc.priority or "-", tc.status,
                    tc.total_steps, tc.passed_steps, tc.failed_steps,
                    step.order_index, step.description,
                    step.intent or "-", step.target or "-", step.value or "-",
                    step.status,
                    f"{step.duration_ms:.0f}" if step.duration_ms else "-",
                    step.error_message or "-",
                ])

    csv_content = output.getvalue()
    filename = f"execution_{execution_id[:8]}_{execution.filename.replace('.txt','').replace('.md','')}.csv"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
