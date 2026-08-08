from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DashboardStats(BaseModel):
    total_executions: int = 0
    total_test_cases: int = 0
    passed: int = 0
    failed: int = 0
    running: int = 0
    blocked: int = 0
    pass_percentage: float = 0.0
    fail_percentage: float = 0.0


class ModuleStat(BaseModel):
    module: str
    total: int
    passed: int
    failed: int


class DailyTrend(BaseModel):
    date: str
    executed: int
    passed: int
    failed: int
