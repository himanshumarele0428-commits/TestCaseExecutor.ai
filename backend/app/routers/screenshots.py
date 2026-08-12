import os
import shutil
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.utils import get_current_user, get_current_user_from_query, get_current_user_from_query_or_header
from app.auth.models import User
from app.models.execution import Screenshot, Execution
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


def _build_screenshot_response(s: Screenshot) -> dict:
    settings = get_settings()
    data = {
        "id": s.id,
        "step_id": s.step_id,
        "execution_id": s.execution_id,
        "filename": s.filename,
        "captured_at": s.captured_at.isoformat() if s.captured_at else None,
    }
    if settings.PLAYWRIGHT_SERVICE_URL:
        data["external_url"] = f"{settings.PLAYWRIGHT_SERVICE_URL}/screenshots/{s.execution_id}/{s.step_id}" if s.step_id else None
    return data


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

    return [_build_screenshot_response(s) for s in screenshots]


@router.get("/download/{screenshot_id}")
async def download_screenshot(
    screenshot_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_query_or_header),
):
    screenshot = await db.get(Screenshot, screenshot_id)
    if not screenshot:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    execution = await db.get(Execution, screenshot.execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    settings = get_settings()
    if settings.PLAYWRIGHT_SERVICE_URL:
        import httpx
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.PLAYWRIGHT_SERVICE_URL}/screenshots/{screenshot.execution_id}/{screenshot.step_id}",
                headers={"X-Internal-Secret": settings.RAILWAY_INTERNAL_SECRET},
            )
        from fastapi.responses import Response
        return Response(content=resp.content, media_type="image/png")

    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(
        screenshot.filepath,
        media_type="image/png",
        filename=screenshot.filename,
    )


@router.get("/{execution_id}/{step_id}")
async def get_screenshot_file(
    execution_id: str,
    step_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_query),
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
    settings = get_settings()
    if settings.PLAYWRIGHT_SERVICE_URL:
        import httpx
        from fastapi.responses import Response
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{settings.PLAYWRIGHT_SERVICE_URL}/screenshots/{execution_id}/{step_id}",
                headers={"X-Internal-Secret": settings.RAILWAY_INTERNAL_SECRET},
            )
        if resp.status_code >= 400:
            raise HTTPException(status_code=404, detail="Screenshot file not found on disk")
        return Response(content=resp.content, media_type="image/png")

    if not os.path.exists(screenshot.filepath):
        raise HTTPException(status_code=404, detail="Screenshot file not found on disk")

    return FileResponse(screenshot.filepath, media_type="image/png")


@router.delete("/{screenshot_id}")
async def delete_single_screenshot(
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

    if os.path.exists(screenshot.filepath):
        os.remove(screenshot.filepath)

    exec_dir = os.path.dirname(screenshot.filepath)
    await db.delete(screenshot)
    await db.commit()

    if os.path.isdir(exec_dir) and not os.listdir(exec_dir):
        os.rmdir(exec_dir)

    return {"message": "Screenshot deleted successfully"}


@router.delete("/execution/{execution_id}")
async def delete_all_screenshots(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    execution = await db.get(Execution, execution_id)
    if not execution or execution.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    result = await db.execute(
        select(Screenshot).where(Screenshot.execution_id == execution_id)
    )
    screenshots = result.scalars().all()

    deleted_count = 0
    exec_dir = ""
    for screenshot in screenshots:
        if os.path.exists(screenshot.filepath):
            os.remove(screenshot.filepath)
        if not exec_dir:
            exec_dir = os.path.dirname(screenshot.filepath)
        await db.delete(screenshot)
        deleted_count += 1

    await db.commit()

    if exec_dir and os.path.isdir(exec_dir):
        try:
            shutil.rmtree(exec_dir, ignore_errors=True)
        except Exception:
            pass

    return {"message": f"{deleted_count} screenshot(s) deleted successfully"}
