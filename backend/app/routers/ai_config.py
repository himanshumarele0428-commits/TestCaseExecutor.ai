import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.utils import get_current_user
from app.auth.models import User
from app.models.api_key import ApiKey
from app.services.encryption import encrypt_value, decrypt_value
from app.services.ai_planner import test_groq_connection

router = APIRouter()
logger = logging.getLogger(__name__)


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "*" * (len(key) - 8) + key[-4:]


@router.get("")
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id, ApiKey.is_active == True)
    )
    api_key_row = result.scalar_one_or_none()

    if api_key_row:
        return {
            "configured": True,
            "provider": api_key_row.provider,
            "model": api_key_row.model_name,
            "key_preview": mask_key(decrypt_value(api_key_row.encrypted_key)),
        }
    return {"configured": False, "provider": None, "model": None, "key_preview": None}


@router.post("")
async def save_ai_config(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key_value = request.get("api_key", "").strip()
    model_name = request.get("model", "llama-3.3-70b-versatile")

    if not api_key_value:
        raise HTTPException(status_code=400, detail="API key is required")

    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()

    encrypted = encrypt_value(api_key_value)

    if existing:
        existing.encrypted_key = encrypted
        existing.model_name = model_name
        existing.is_active = True
    else:
        api_key = ApiKey(
            user_id=current_user.id,
            encrypted_key=encrypted,
            provider="groq",
            model_name=model_name,
            is_active=True,
        )
        db.add(api_key)

    await db.commit()
    return {"message": "API key saved successfully", "key_preview": mask_key(api_key_value)}


@router.post("/test")
async def test_ai_connection(
    request: dict,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    api_key_value = request.get("api_key", "").strip()
    model_name = request.get("model", "llama-3.3-70b-versatile")

    if not api_key_value:
        raise HTTPException(status_code=400, detail="API key is required")

    try:
        await test_groq_connection(api_key_value, model_name)
        return {"status": "connected", "message": "Successfully connected to Groq API"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Connection failed: {str(e)}")


@router.delete("")
async def remove_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ApiKey).where(ApiKey.user_id == current_user.id)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.is_active = False
        await db.commit()

    return {"message": "API key removed successfully"}
