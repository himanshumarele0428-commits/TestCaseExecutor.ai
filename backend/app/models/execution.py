import uuid
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Execution(Base):
    __tablename__ = "executions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_content = Column(Text)
    status = Column(String(20), default="NOT_EXECUTED", index=True)
    total_test_cases = Column(Integer, default=0)
    passed = Column(Integer, default=0)
    failed = Column(Integer, default=0)
    blocked = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    error_message = Column(Text)
    created_at = Column(DateTime, server_default=func.now())

    test_cases = relationship("TestCase", back_populates="execution", order_by="TestCase.order_index")


class TestCase(Base):
    __tablename__ = "test_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    module = Column(String(100))
    priority = Column(String(20))
    environment = Column(String(50))
    order_index = Column(Integer, default=0)
    status = Column(String(20), default="NOT_EXECUTED")
    total_steps = Column(Integer, default=0)
    passed_steps = Column(Integer, default=0)
    failed_steps = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())

    execution = relationship("Execution", back_populates="test_cases")
    steps = relationship("TestStep", back_populates="test_case", order_by="TestStep.order_index")


class TestStep(Base):
    __tablename__ = "test_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    test_case_id = Column(String(36), ForeignKey("test_cases.id", ondelete="CASCADE"), nullable=False)
    order_index = Column(Integer, default=0)
    description = Column(Text, nullable=False)
    intent = Column(String(20))
    target = Column(String(255))
    value = Column(String(500))
    playwright_action = Column(Text)
    status = Column(String(20), default="PENDING")
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)
    created_at = Column(DateTime, server_default=func.now())

    test_case = relationship("TestCase", back_populates="steps")
    screenshots = relationship("Screenshot", back_populates="step")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    step_id = Column(String(36), ForeignKey("test_steps.id", ondelete="CASCADE"), nullable=False)
    execution_id = Column(String(36), ForeignKey("executions.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    filepath = Column(String(500), nullable=False)
    external_url = Column(String(500), nullable=True)
    captured_at = Column(DateTime, server_default=func.now())

    step = relationship("TestStep", back_populates="screenshots")
