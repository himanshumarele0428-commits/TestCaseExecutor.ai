from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import get_settings

_engine = None
_async_session = None


def _get_engine():
    global _engine, _async_session
    if _engine is None:
        settings = get_settings()
        connect_args = {}
        if settings.DATABASE_URL.startswith("sqlite"):
            _engine = create_async_engine(settings.DATABASE_URL, echo=False, connect_args={"check_same_thread": False})
        else:
            if "postgresql" in settings.DATABASE_URL:
                # Railway internal hostnames don't support SSL; public endpoints do.
                if ".railway.internal" in settings.DATABASE_URL:
                    connect_args = {}
                else:
                    connect_args = {"ssl": "require"}
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                pool_size=5,
                max_overflow=10,
                pool_pre_ping=True,
                pool_recycle=300,
                connect_args=connect_args,
            )
        _async_session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
    return _engine


def _get_session_factory():
    _get_engine()
    return _async_session


class Base(DeclarativeBase):
    pass


async def get_db():
    session_factory = _get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from app.auth.models import User
    from app.models.api_key import ApiKey
    from app.models.execution import Execution, TestCase, TestStep, Screenshot

    engine = _get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def get_async_session():
    return _get_session_factory()
