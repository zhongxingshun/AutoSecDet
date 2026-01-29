"""
AuditLog model for tracking sensitive operations.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from app.core.database import Base


class AuditLog(Base):
    """Audit log model for tracking user actions."""
    
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    username = Column(String(50), nullable=True)  # Redundant for easy querying
    action = Column(String(50), nullable=False, index=True)
    # Action: 'login' | 'logout' | 'login_failed' | 'create' | 'update' | 'delete'
    resource_type = Column(String(50), nullable=True, index=True)
    # Resource type: 'case' | 'category' | 'user' | 'task'
    resource_id = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(45), nullable=True)  # Supports IPv6
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP", index=True)
