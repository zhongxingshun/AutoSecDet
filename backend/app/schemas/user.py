"""
User Pydantic schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class UserBase(BaseModel):
    """Base user schema with common fields."""
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=6, max_length=100)
    role: str = Field(default="tester", pattern="^(tester|admin)$")
    
    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username must be alphanumeric (with _ or - allowed)")
        return v.lower()


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    role: Optional[str] = Field(None, pattern="^(tester|admin)$")
    is_active: Optional[bool] = None


class UserInDB(UserBase):
    """Schema for user stored in database."""
    id: int
    role: str
    is_active: bool
    login_attempts: int
    locked_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response (public fields only)."""
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""
    items: list[UserResponse]
    total: int
    page: int
    page_size: int


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    new_password: str = Field(..., min_length=6, max_length=100)
