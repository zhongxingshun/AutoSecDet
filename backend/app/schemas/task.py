"""
Task Pydantic schemas for request/response validation.
"""
import re
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, field_validator


class TaskBase(BaseModel):
    """Base task schema with common fields."""
    target_ip: str = Field(..., min_length=7, max_length=15)
    
    @field_validator("target_ip")
    @classmethod
    def validate_ip(cls, v: str) -> str:
        """Validate IPv4 address format."""
        pattern = r"^((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
        if not re.match(pattern, v):
            raise ValueError("Invalid IPv4 address format")
        return v


class TaskCreate(TaskBase):
    """Schema for creating a new task."""
    case_ids: Optional[List[int]] = Field(None, description="Specific case IDs to run. If empty, runs all enabled cases.")


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: int
    target_ip: str
    user_id: int
    username: Optional[str] = None
    status: str
    total_cases: int
    completed_cases: int
    passed_count: int
    failed_count: int
    error_count: int
    progress: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Schema for paginated task list response."""
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int


class TaskResultResponse(BaseModel):
    """Schema for task result response."""
    id: int
    task_id: int
    case_id: int
    case_name: Optional[str] = None
    category_name: Optional[str] = None
    risk_level: Optional[str] = None
    status: str
    retry_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskDetailResponse(TaskResponse):
    """Schema for task detail with results."""
    results: List[TaskResultResponse] = []


class TaskFilter(BaseModel):
    """Schema for task filtering."""
    status: Optional[str] = Field(None, pattern="^(pending|running|completed|stopped|error)$")
    target_ip: Optional[str] = None
    user_id: Optional[int] = None
