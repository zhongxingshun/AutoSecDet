"""
User management API endpoints (Admin only).
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import AdminUser, CurrentUser, DBSession
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListResponse,
    PasswordReset,
)
from app.services.user_service import UserService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("", response_model=UserListResponse)
async def list_users(
    current_user: AdminUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    List all users with pagination. (Admin only)
    """
    user_service = UserService(db)
    skip = (page - 1) * page_size
    
    users = user_service.get_all(skip=skip, limit=page_size)
    total = user_service.count()
    
    return UserListResponse(
        items=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Create a new user. (Admin only)
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    # Check if username already exists
    existing_user = user_service.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )
    
    user = user_service.create(user_data)
    
    # Log audit
    audit_service.log(
        action="create",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user.id,
        details={"created_username": user.username, "role": user.role},
    )
    
    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Get user by ID. (Admin only)
    """
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Update user information. (Admin only)
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Prevent admin from deactivating themselves
    if user_id == current_user.id and user_data.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account",
        )
    
    updated_user = user_service.update(user, user_data)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user_id,
        details=user_data.model_dump(exclude_unset=True),
    )
    
    return updated_user


@router.post("/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    password_data: PasswordReset,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Reset user password. (Admin only)
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user = user_service.get_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    user_service.reset_password(user, password_data.new_password)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=user_id,
        details={"action": "password_reset"},
    )
    
    return {"message": "Password reset successfully"}


@router.post("/me/change-password")
async def change_own_password(
    password_data: PasswordReset,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Change own password. (Any authenticated user)
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    user_service.reset_password(current_user, password_data.new_password)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="user",
        resource_id=current_user.id,
        details={"action": "password_change"},
    )
    
    return {"message": "Password changed successfully"}
