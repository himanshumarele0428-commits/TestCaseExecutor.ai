from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class FileUploadResponse(BaseModel):
    filename: str
    test_cases: List[dict]


class ExecutionCreateRequest(BaseModel):
    filename: str
    file_content: str
    parsed_test_cases: List[dict]


class ExecutionCreateResponse(BaseModel):
    id: str
    filename: str
    status: str
    total_test_cases: int
    created_at: datetime


class StepResponse(BaseModel):
    id: str
    order_index: int
    description: str
    intent: Optional[str]
    target: Optional[str]
    value: Optional[str]
    status: str
    error_message: Optional[str]
    duration_ms: Optional[float]
    screenshots: List[dict] = []

    model_config = {"from_attributes": True}


class TestCaseResponse(BaseModel):
    id: str
    name: str
    module: Optional[str]
    priority: Optional[str]
    order_index: int
    status: str
    total_steps: int
    passed_steps: int
    failed_steps: int
    steps: List[StepResponse] = []

    model_config = {"from_attributes": True}


class ExecutionResponse(BaseModel):
    id: str
    filename: str
    status: str
    total_test_cases: int
    passed: int
    failed: int
    blocked: int
    duration_seconds: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: Optional[datetime]
    test_cases: List[TestCaseResponse] = []

    model_config = {"from_attributes": True}


class ExecutionListItem(BaseModel):
    id: str
    filename: str
    status: str
    total_test_cases: int
    passed: int
    failed: int
    duration_seconds: Optional[float]
    created_at: Optional[datetime]

    model_config = {"from_attributes": True}
