"""
Security utilities for password hashing and verification.
"""
from datetime import datetime, timedelta
from typing import Optional

from passlib.context import CryptContext

from app.core.config import settings

# Password hashing context with bcrypt
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=settings.BCRYPT_ROUNDS,
)


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    
    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against
        
    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def is_account_locked(locked_until: Optional[datetime]) -> bool:
    """
    Check if an account is currently locked.
    
    Args:
        locked_until: Timestamp when the lock expires
        
    Returns:
        True if account is locked, False otherwise
    """
    if locked_until is None:
        return False
    return datetime.utcnow() < locked_until


def get_lockout_time() -> datetime:
    """
    Get the lockout expiration time based on settings.
    
    Returns:
        Datetime when the lockout expires
    """
    return datetime.utcnow() + timedelta(minutes=settings.LOGIN_LOCKOUT_MINUTES)


def should_lock_account(login_attempts: int) -> bool:
    """
    Check if account should be locked based on failed login attempts.
    
    Args:
        login_attempts: Number of failed login attempts
        
    Returns:
        True if account should be locked, False otherwise
    """
    return login_attempts >= settings.LOGIN_MAX_ATTEMPTS
