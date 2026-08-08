import os
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.models.execution import Screenshot, Execution

router = APIRouter()


@router.get("")
async def list_execution_screenshots(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")

    result = await db.execute(
        select(Screenshot).where(Screenshot.execution_id == execution_id).order_by(Screenshot.captured_at)
    )
    screenshots = result.scalars().all()

    return [
        {
            "id": s.id,
            "step_id": s.step_id,
            "execution_id": s.execution_id,
            "filename": s.filename,
            "captured_at": s.captured_at.isoformat() if s.captured_at else None,
        }
        for s in screenshots
    ]


@router.get("/{execution_id}/{step_id}")
async def get_screenshot_file(
    execution_id: str,
    step_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Execution not found")

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
    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(screenshot.filepath, media_type="image/png")


@router.get("/download/{screenshot_id}")
async def download_screenshot(
    screenshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    screenshot = await db.get(Screenshot, screenshot_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    execution = await db.get(Execution, screenshot.execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(
        screenshot.filepath,
        media_type="image/png",
        filename=screenshot.filename,
    )
