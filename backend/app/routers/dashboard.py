import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.models.execution import Execution, TestCase

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
            func.substr(Execution.created_at, 1, 10).label("date"),
            func.count(Execution.id).label("executed"),
            func.coalesce(func.sum(Execution.passed), 0).label("passed"),
            func.coalesce(func.sum(Execution.failed), 0).label("failed"),
        )
        .where(
            Execution.user_id == current_user.id,
            Execution.created_at >= thirty_days_ago.isoformat(),
        )
        .group_by(func.substr(Execution.created_at, 1, 10))
        .order_by(func.substr(Execution.created_at, 1, 10))
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
