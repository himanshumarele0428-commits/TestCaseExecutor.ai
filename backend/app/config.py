from pydantic_settings import BaseSettings
from functools import lru_cache
import os
from pathlib import Path


def _find_env_file() -> str:
    config_dir = Path(__file__).resolve().parent
    project_root = config_dir.parent.parent.parent
    backend_dir = config_dir.parent.parent
    for path in [project_root / ".env", backend_dir / ".env", config_dir / ".env"]:
        if path.is_file():
            return str(path)
    return str(project_root / ".env")


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./testcase_executor.db"
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"

    SCREENSHOTS_DIR: str = "./screenshots"
    FERNET_KEY: str = "ZmVybmV0LWtleS1mb3ItZGV2ZWxvcG1lbnQtb25seQ=="

    FRONTEND_URL: str = "http://localhost:5173"
    RESEND_API_KEY: str = ""
    RESEND_FROM_EMAIL: str = "Testcase Executor.AI <onboarding@resend.dev>"
    SENDGRID_API_KEY: str = ""
    SENDGRID_FROM_EMAIL: str = "Testcase Executor.AI <noreply@testcaseexecutor.app>"
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_USE_TLS: bool = True

    model_config = {"env_file": _find_env_file(), "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def resolved_frontend_url(self) -> str:
        import os
        vercel_url = os.environ.get("VERCEL_URL", "")
        if vercel_url and self.FRONTEND_URL == "http://localhost:5173":
            return f"https://{vercel_url}"
        return self.FRONTEND_URL


@lru_cache()
def get_settings() -> Settings:
    return Settings()
