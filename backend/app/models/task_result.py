"""
TaskResult model for individual case execution results.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskResult(Base):
    """Task result model for individual case execution."""
    
    __tablename__ = "task_results"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(Integer, ForeignKey("cases.id"), nullable=False)
    status = Column(String(20), nullable=False, default="pending", index=True)
    # Status: 'pending' | 'running' | 'pass' | 'fail' | 'error'
    retry_count = Column(Integer, nullable=False, default=0)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    log_path = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default="CURRENT_TIMESTAMP")
    
    # Relationships
    task = relationship("Task", back_populates="results")
    case = relationship("Case", back_populates="task_results")
