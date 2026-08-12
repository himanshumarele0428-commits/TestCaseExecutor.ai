import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, Date
from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.models.execution import Execution, TestCase, TestStep

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats")
async def get_dashboard_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(Execution).where(Execution.user_id == current_user.id)
    )
    executions = result.scalars().all()

    total_executions = len(executions)
    total_test_cases = sum(e.total_test_cases or 0 for e in executions)
    passed = sum(e.passed or 0 for e in executions)
    failed = sum(e.failed or 0 for e in executions)
    blocked = sum(e.blocked or 0 for e in executions)
    running = sum(1 for e in executions if e.status == "RUNNING")

    total_results = passed + failed
    pass_pct = round((passed / total_results) * 100, 1) if total_results > 0 else 0.0
    fail_pct = round((failed / total_results) * 100, 1) if total_results > 0 else 0.0

    return {
        "total_executions": total_executions,
        "total_test_cases": total_test_cases,
        "passed": passed,
        "failed": failed,
        "running": running,
        "blocked": blocked,
        "pass_percentage": pass_pct,
        "fail_percentage": fail_pct,
    }


@router.get("/module-stats")
async def get_module_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    exec_result = await db.execute(
        select(Execution.id).where(Execution.user_id == current_user.id)
    )
    execution_ids = [r[0] for r in exec_result.all()]

    if not execution_ids:
        return []

    tc_result = await db.execute(
        select(TestCase).where(TestCase.execution_id.in_(execution_ids))
    )
    test_cases = tc_result.scalars().all()

    module_map: dict[str, dict] = {}
    for tc in test_cases:
        module = tc.module or "Default"
        if module not in module_map:
            module_map[module] = {"module": module, "total": 0, "passed": 0, "failed": 0}
        module_map[module]["total"] += 1
        if tc.status == "PASSED":
            module_map[module]["passed"] += 1
        elif tc.status == "FAILED":
            module_map[module]["failed"] += 1

    return sorted(module_map.values(), key=lambda x: x["total"], reverse=True)


@router.get("/trend")
async def get_execution_trend(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    result = await db.execute(
        select(
            func.cast(Execution.created_at, Date).label("date"),
            func.count(Execution.id).label("executed"),
            func.coalesce(func.sum(Execution.passed), 0).label("passed"),
            func.coalesce(func.sum(Execution.failed), 0).label("failed"),
        )
        .where(
            Execution.user_id == current_user.id,
            Execution.created_at >= thirty_days_ago,
        )
        .group_by(func.cast(Execution.created_at, Date))
        .order_by(func.cast(Execution.created_at, Date))
    )

    trends = []
    for row in result.all():
        trends.append({
            "date": str(row.date),
            "executed": row.executed,
            "passed": row.passed or 0,
            "failed": row.failed or 0,
        })

    return trends


@router.get("/execution/{execution_id}")
async def get_execution_dashboard(
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

    total = len(test_cases)
    passed = sum(1 for tc in test_cases if tc.status == "PASSED")
    failed = sum(1 for tc in test_cases if tc.status == "FAILED")
    blocked = sum(1 for tc in test_cases if tc.status == "BLOCKED")
    skipped = sum(1 for tc in test_cases if tc.status == "SKIPPED")
    executed = sum(1 for tc in test_cases if tc.status not in ("QUEUED", "NOT_EXECUTED", "PENDING"))
    pending = total - executed

    executed_for_pct = passed + failed + blocked
    pass_pct = round((passed / total) * 100, 1) if total > 0 else 0.0
    fail_pct = round((failed / total) * 100, 1) if total > 0 else 0.0
    blocked_pct = round((blocked / total) * 100, 1) if total > 0 else 0.0
    skipped_pct = round((skipped / total) * 100, 1) if total > 0 else 0.0
    executed_pct = round((executed / total) * 100, 1) if total > 0 else 0.0
    pending_pct = round((pending / total) * 100, 1) if total > 0 else 0.0

    module_map: dict[str, dict] = {}
    pass_pct_of_executed = round((passed / executed_for_pct) * 100, 1) if executed_for_pct > 0 else 0.0

    tc_list = []
    for tc in test_cases:
        module = tc.module or "Default"
        if module not in module_map:
            module_map[module] = {"module": module, "total": 0, "passed": 0, "failed": 0, "pending": 0, "blocked": 0}
        module_map[module]["total"] += 1
        if tc.status == "PASSED":
            module_map[module]["passed"] += 1
        elif tc.status == "FAILED":
            module_map[module]["failed"] += 1
        elif tc.status in ("QUEUED", "NOT_EXECUTED", "PENDING"):
            module_map[module]["pending"] += 1
        elif tc.status == "BLOCKED":
            module_map[module]["blocked"] += 1

        error_message = None
        if tc.status == "FAILED":
            failed_step_result = await db.execute(
                select(TestStep)
                .where(TestStep.test_case_id == tc.id, TestStep.status == "FAILED")
                .order_by(TestStep.order_index)
                .limit(1)
            )
            failed_step = failed_step_result.scalar_one_or_none()
            if failed_step:
                error_message = failed_step.error_message

        tc_list.append({
            "id": tc.id,
            "name": tc.name,
            "module": tc.module,
            "priority": tc.priority,
            "status": tc.status,
            "total_steps": tc.total_steps,
            "passed_steps": tc.passed_steps,
            "failed_steps": tc.failed_steps,
            "error_message": error_message,
        })

    mod_list = []
    for m in sorted(module_map.values(), key=lambda x: x["total"], reverse=True):
        m["pass_pct"] = round((m["passed"] / m["total"]) * 100, 1) if m["total"] > 0 else 0.0
        mod_list.append(m)

    started_at = execution.started_at.isoformat() if execution.started_at else None
    completed_at = execution.completed_at.isoformat() if execution.completed_at else None
    duration = None
    if execution.duration_seconds:
        h = int(execution.duration_seconds // 3600)
        m = int((execution.duration_seconds % 3600) // 60)
        s = int(execution.duration_seconds % 60)
        duration = f"{h:02d}:{m:02d}:{s:02d}"

    return {
        "execution_id": execution.id,
        "filename": execution.filename,
        "status": execution.status,
        "created_at": execution.created_at.isoformat() if execution.created_at else None,
        "total_test_cases": total,
        "executed": executed,
        "passed": passed,
        "failed": failed,
        "blocked": blocked,
        "skipped": skipped,
        "pending": pending,
        "executed_percentage": executed_pct,
        "pass_percentage": pass_pct,
        "fail_percentage": fail_pct,
        "blocked_percentage": blocked_pct,
        "skipped_percentage": skipped_pct,
        "pending_percentage": pending_pct,
        "pass_rate_of_executed": pass_pct_of_executed,
        "started_at": started_at,
        "completed_at": completed_at,
        "duration": duration,
        "duration_seconds": execution.duration_seconds,
        "test_cases": tc_list,
        "module_breakdown": mod_list,
    }
