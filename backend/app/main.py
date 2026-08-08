import asyncio
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import init_db
from app.config import get_settings
import os

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    settings = get_settings()
    os.makedirs(settings.SCREENSHOTS_DIR, exist_ok=True)
    yield


app = FastAPI(
    title="Testcase Executor.AI",
    description="AI-powered test execution application",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.auth.router import router as auth_router
from app.routers.files import router as files_router
from app.routers.executions import router as executions_router
from app.routers.dashboard import router as dashboard_router
from app.routers.screenshots import router as screenshots_router
from app.routers.ai_config import router as ai_config_router

app.include_router(auth_router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(files_router, prefix="/api/v1/files", tags=["Files"])
app.include_router(executions_router, prefix="/api/v1/executions", tags=["Executions"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(screenshots_router, prefix="/api/v1/screenshots", tags=["Screenshots"])
app.include_router(ai_config_router, prefix="/api/v1/ai-config", tags=["AI Config"])

settings = get_settings()
screenshots_path = os.path.abspath(settings.SCREENSHOTS_DIR)
os.makedirs(screenshots_path, exist_ok=True)
app.mount("/api/v1/screenshots-files", StaticFiles(directory=screenshots_path), name="screenshots-files")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Testcase Executor.AI"}
