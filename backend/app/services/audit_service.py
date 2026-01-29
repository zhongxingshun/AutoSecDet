"""
Audit log service for tracking user actions.
"""
from typing import Optional

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditService:
    """Service class for audit logging."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def log(
        self,
        action: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """
        Create an audit log entry.
        
        Args:
            action: Action type (login, logout, login_failed, create, update, delete)
            user_id: User ID performing the action
            username: Username (for login attempts where user may not exist)
            resource_type: Type of resource affected (case, category, user, task)
            resource_id: ID of the affected resource
            details: Additional details as JSON
            ip_address: Client IP address
            user_agent: Client user agent string
            
        Returns:
            Created AuditLog entry
        """
        audit_log = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log
    
    def log_login(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log successful login."""
        return self.log(
            action="login",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_login_failed(
        self,
        username: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> AuditLog:
        """Log failed login attempt."""
        return self.log(
            action="login_failed",
            username=username,
            details={"reason": reason},
            ip_address=ip_address,
            user_agent=user_agent,
        )
    
    def log_logout(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        """Log user logout."""
        return self.log(
            action="logout",
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )
