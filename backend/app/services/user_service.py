"""
User service for authentication and user management.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.core.security import (
    hash_password,
    verify_password,
    is_account_locked,
    get_lockout_time,
    should_lock_account,
)
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate


class UserService:
    """Service class for user-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        return self.db.query(User).filter(User.username == username.lower()).first()
    
    def get_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        """Get all users with pagination."""
        return self.db.query(User).offset(skip).limit(limit).all()
    
    def count(self) -> int:
        """Get total user count."""
        return self.db.query(User).count()
    
    def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        user = User(
            username=user_data.username.lower(),
            password_hash=hash_password(user_data.password),
            role=user_data.role,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def update(self, user: User, user_data: UserUpdate) -> User:
        """Update user fields."""
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def reset_password(self, user: User, new_password: str) -> User:
        """Reset user password."""
        user.password_hash = hash_password(new_password)
        user.login_attempts = 0
        user.locked_until = None
        user.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(user)
        return user
    
    def authenticate(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.
        
        Returns:
            User if authentication successful, None otherwise
        """
        user = self.get_by_username(username)
        if not user:
            return None
        
        # Check if account is locked
        if is_account_locked(user.locked_until):
            return None
        
        # Check if account is active
        if not user.is_active:
            return None
        
        # Verify password
        if not verify_password(password, user.password_hash):
            self._handle_failed_login(user)
            return None
        
        # Reset login attempts on successful login
        self._handle_successful_login(user)
        return user
    
    def _handle_failed_login(self, user: User) -> None:
        """Handle failed login attempt."""
        user.login_attempts += 1
        
        if should_lock_account(user.login_attempts):
            user.locked_until = get_lockout_time()
        
        self.db.commit()
    
    def _handle_successful_login(self, user: User) -> None:
        """Handle successful login."""
        user.login_attempts = 0
        user.locked_until = None
        self.db.commit()
    
    def is_locked(self, user: User) -> bool:
        """Check if user account is locked."""
        return is_account_locked(user.locked_until)
