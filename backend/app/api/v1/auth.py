"""
Authentication API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)
from app.api.deps import CurrentUser
from app.schemas.auth import LoginRequest, TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.user_service import UserService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def get_user_agent(request: Request) -> str:
    """Extract user agent from request."""
    return request.headers.get("User-Agent", "unknown")[:500]


@router.post("/login", response_model=TokenResponse)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Authenticate user and return JWT tokens.
    
    - **username**: User's username
    - **password**: User's password
    
    Returns access token (30 min) and refresh token (7 days).
    """
    user_service = UserService(db)
    audit_service = AuditService(db)
    
    ip_address = get_client_ip(request)
    user_agent = get_user_agent(request)
    
    # Check if user exists first
    user = user_service.get_by_username(login_data.username)
    
    if user is None:
        audit_service.log_login_failed(
            username=login_data.username,
            reason="User not found",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if account is locked
    if user_service.is_locked(user):
        audit_service.log_login_failed(
            username=login_data.username,
            reason="Account locked",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is locked. Please try again later.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Authenticate
    authenticated_user = user_service.authenticate(
        login_data.username,
        login_data.password,
    )
    
    if authenticated_user is None:
        audit_service.log_login_failed(
            username=login_data.username,
            reason="Invalid password",
            ip_address=ip_address,
            user_agent=user_agent,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate tokens
    access_token = create_access_token(
        subject=authenticated_user.username,
        user_id=authenticated_user.id,
        role=authenticated_user.role,
    )
    refresh_token = create_refresh_token(
        subject=authenticated_user.username,
        user_id=authenticated_user.id,
    )
    
    # Log successful login
    audit_service.log_login(
        user_id=authenticated_user.id,
        username=authenticated_user.username,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserResponse.model_validate(authenticated_user),
    )


@router.post("/logout")
async def logout(
    request: Request,
    current_user: CurrentUser,
    db: Session = Depends(get_db),
):
    """
    Logout current user.
    
    Note: JWT tokens are stateless, so this endpoint mainly logs the action.
    Client should discard tokens on their side.
    """
    audit_service = AuditService(db)
    ip_address = get_client_ip(request)
    
    audit_service.log_logout(
        user_id=current_user.id,
        username=current_user.username,
        ip_address=ip_address,
    )
    
    return {"message": "Successfully logged out"}


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db),
):
    """
    Refresh access token using refresh token.
    
    - **refresh_token**: Valid refresh token
    
    Returns new access token and refresh token.
    """
    payload = verify_refresh_token(refresh_data.refresh_token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("user_id")
    user_service = UserService(db)
    user = user_service.get_by_id(user_id)
    
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate new tokens
    access_token = create_access_token(
        subject=user.username,
        user_id=user.id,
        role=user.role,
    )
    new_refresh_token = create_refresh_token(
        subject=user.username,
        user_id=user.id,
    )
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: CurrentUser):
    """
    Get current authenticated user information.
    """
    return current_user
