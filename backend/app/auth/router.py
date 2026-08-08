from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.auth.schemas import UserCreate, UserLogin, TokenResponse, UserResponse
from app.auth.service import register_user, authenticate_user
from app.auth.utils import get_current_user
from app.auth.models import User

router = APIRouter()


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
