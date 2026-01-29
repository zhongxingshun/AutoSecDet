"""
Case model for security test cases.
"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class Case(Base, TimestampMixin):
    """Security test case model."""
    
    __tablename__ = "cases"
    __table_args__ = (
        UniqueConstraint("name", "category_id", name="uq_cases_name_category"),
    )
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False, index=True)
    risk_level = Column(String(10), nullable=False)  # 'high' | 'medium' | 'low'
    description = Column(Text, nullable=True)
    fix_suggestion = Column(Text, nullable=True)
    script_path = Column(String(500), nullable=False)
    is_enabled = Column(Boolean, nullable=False, default=True, index=True)
    is_deleted = Column(Boolean, nullable=False, default=False, index=True)
    deleted_at = Column(DateTime, nullable=True)
    
    # Relationships
    category = relationship("Category", back_populates="cases")
    task_results = relationship("TaskResult", back_populates="case")
