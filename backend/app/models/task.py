"""
Task model for detection tasks.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Task(Base):
    """Detection task model."""
    
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    target_ip = Column(String(15), nullable=False, index=True)
    description = Column(Text, nullable=True)  # 备注说明（版本、机型等）
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    # Status: 'pending' | 'running' | 'completed' | 'stopped' | 'error'
    total_cases = Column(Integer, nullable=False, default=0)
    completed_cases = Column(Integer, nullable=False, default=0)
    passed_count = Column(Integer, nullable=False, default=0)
    failed_count = Column(Integer, nullable=False, default=0)
    error_count = Column(Integer, nullable=False, default=0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP", index=True)
    
    # Relationships
    user = relationship("User")
    results = relationship("TaskResult", back_populates="task", cascade="all, delete-orphan")
