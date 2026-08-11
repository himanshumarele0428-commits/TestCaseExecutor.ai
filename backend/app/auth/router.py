import uuid
import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.auth.schemas import UserCreate, UserLogin, TokenResponse, UserResponse, ForgotPasswordRequest, ResetPasswordRequest
from app.auth.service import register_user, authenticate_user
from app.auth.utils import get_current_user, hash_password
from app.auth.models import User
from app.services.email_service import send_password_reset_email
from app.config import get_settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/register", status_code=201)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    await register_user(db, data.model_dump())
    return {"message": "Account created successfully. Please login."}


@router.post("/login", response_model=TokenResponse)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    return await authenticate_user(db, data.username_or_email, data.password)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/forgot-password")
async def forgot_password(
    request: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db),
):
    frontend_url = request.origin or get_settings().resolved_frontend_url
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    if user:
        user.reset_token = str(uuid.uuid4())
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        reset_link = f"{frontend_url}/reset-password?token={user.reset_token}"
        sent, error_msg = await send_password_reset_email(
            request.email, user.reset_token, frontend_url=str(frontend_url)
        )
        if not sent:
            logger.warning(
                f"Failed to send reset email to {request.email}: {error_msg}. "
                f"Returning reset link directly for development: {reset_link}"
            )
            return {
                "message": "If the email exists, a reset link has been sent",
                "dev_reset_link": reset_link,
            }
        else:
            logger.info(f"Reset email dispatched to {request.email} (check spam folder)")
    return {"message": "If the email exists, a reset link has been sent"}


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.reset_token == request.token))
    user = result.scalar_one_or_none()

    if not user or not user.reset_token_expires:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    expires = user.reset_token_expires
    if expires.tzinfo is None:
        expires = expires.replace(tzinfo=timezone.utc)
    now_utc = datetime.now(timezone.utc)
    if expires < now_utc:
        logger.warning(f"Token expired: expires={expires}, now={now_utc}")
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user.hashed_password = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    await db.commit()
    return {"message": "Password reset successful"}
