"""
Case Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class CaseBase(BaseModel):
    """Base case schema with common fields."""
    name: str = Field(..., min_length=1, max_length=200)
    category_id: int = Field(..., gt=0)
    risk_level: str = Field(..., pattern="^(high|medium|low)$")
    description: Optional[str] = None
    fix_suggestion: Optional[str] = None
    script_path: str = Field(..., min_length=1, max_length=500)


class CaseCreate(CaseBase):
    """Schema for creating a new case."""
    pass


class CaseUpdate(BaseModel):
    """Schema for updating a case."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category_id: Optional[int] = Field(None, gt=0)
    risk_level: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    description: Optional[str] = None
    fix_suggestion: Optional[str] = None
    script_path: Optional[str] = Field(None, min_length=1, max_length=500)
    is_enabled: Optional[bool] = None


class CaseResponse(BaseModel):
    """Schema for case response."""
    id: int
    name: str
    category_id: int
    category_name: Optional[str] = None
    risk_level: str
    description: Optional[str] = None
    fix_suggestion: Optional[str] = None
    script_path: str
    is_enabled: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CaseListResponse(BaseModel):
    """Schema for paginated case list response."""
    items: list[CaseResponse]
    total: int
    page: int
    page_size: int


class CaseFilter(BaseModel):
    """Schema for case filtering."""
    category_id: Optional[int] = None
    risk_level: Optional[str] = Field(None, pattern="^(high|medium|low)$")
    is_enabled: Optional[bool] = None
    keyword: Optional[str] = None
