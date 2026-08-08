from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi import HTTPException, status
from app.auth.models import User
from app.auth.utils import hash_password, verify_password, create_access_token


async def register_user(db: AsyncSession, data: dict) -> User:
    existing = await db.execute(
        select(User).where(
            or_(User.username == data["username"], User.email == data["email"])
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or username already exists",
        )

    user = User(
        full_name=data["full_name"],
        username=data["username"],
        email=data["email"],
        hashed_password=hash_password(data["password"]),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def authenticate_user(db: AsyncSession, username_or_email: str, password: str) -> dict:
    result = await db.execute(
        select(User).where(
            or_(User.username == username_or_email, User.email == username_or_email)
        )
    )
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username/email or password",
        )

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}
