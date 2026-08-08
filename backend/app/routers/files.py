import os
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from app.auth.utils import get_current_user
from app.auth.models import User
from app.services.parser import parse_test_file, ParsedTestCase

router = APIRouter()
logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {".txt", ".md"}
MAX_FILE_SIZE = 5 * 1024 * 1024


@router.post("/upload")
async def upload_test_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext}'. Only .txt and .md files are accepted.",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")

    if not content.strip():
        raise HTTPException(status_code=400, detail="File is empty.")

    try:
        text_content = content.decode("utf-8")
    except UnicodeDecodeError:
        text_content = content.decode("latin-1")

    parsed = parse_test_file(text_content, file.filename or "unknown")

    if not parsed:
        raise HTTPException(status_code=400, detail="No test cases found in the file.")

    test_cases_data = []
    for tc in parsed:
        tc_data = {
            "name": tc.name,
            "module": tc.module,
            "priority": tc.priority,
            "environment": tc.environment,
            "browser": tc.browser,
            "total_steps": len(tc.steps),
            "steps": [{"order": s.order, "description": s.description} for s in tc.steps],
        }
        test_cases_data.append(tc_data)

    logger.info(f"Parsed {len(parsed)} test cases from '{file.filename}'")
    return {
        "filename": file.filename,
        "file_content": text_content,
        "test_cases_count": len(parsed),
        "total_steps": sum(len(tc.steps) for tc in parsed),
        "test_cases": test_cases_data,
    }
