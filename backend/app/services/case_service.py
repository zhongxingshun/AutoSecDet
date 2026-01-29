"""
Case service for test case management.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.case import Case
from app.models.category import Category
from app.schemas.case import CaseCreate, CaseUpdate, CaseFilter


class CaseService:
    """Service class for case-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, case_id: int, include_deleted: bool = False) -> Optional[Case]:
        """Get case by ID."""
        query = self.db.query(Case).filter(Case.id == case_id)
        if not include_deleted:
            query = query.filter(Case.is_deleted == False)
        return query.first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[CaseFilter] = None,
    ) -> List[Case]:
        """Get all cases with pagination and filtering."""
        query = self.db.query(Case).filter(Case.is_deleted == False)
        
        if filters:
            if filters.category_id is not None:
                query = query.filter(Case.category_id == filters.category_id)
            if filters.risk_level is not None:
                query = query.filter(Case.risk_level == filters.risk_level)
            if filters.is_enabled is not None:
                query = query.filter(Case.is_enabled == filters.is_enabled)
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                query = query.filter(
                    or_(
                        Case.name.ilike(keyword),
                        Case.description.ilike(keyword),
                    )
                )
        
        return query.order_by(Case.id.desc()).offset(skip).limit(limit).all()
    
    def count(self, filters: Optional[CaseFilter] = None) -> int:
        """Get total case count with optional filtering."""
        query = self.db.query(Case).filter(Case.is_deleted == False)
        
        if filters:
            if filters.category_id is not None:
                query = query.filter(Case.category_id == filters.category_id)
            if filters.risk_level is not None:
                query = query.filter(Case.risk_level == filters.risk_level)
            if filters.is_enabled is not None:
                query = query.filter(Case.is_enabled == filters.is_enabled)
            if filters.keyword:
                keyword = f"%{filters.keyword}%"
                query = query.filter(
                    or_(
                        Case.name.ilike(keyword),
                        Case.description.ilike(keyword),
                    )
                )
        
        return query.count()
    
    def get_enabled_cases(self) -> List[Case]:
        """Get all enabled cases for task execution."""
        return (
            self.db.query(Case)
            .filter(Case.is_deleted == False, Case.is_enabled == True)
            .order_by(Case.category_id, Case.id)
            .all()
        )
    
    def create(self, case_data: CaseCreate) -> Case:
        """Create a new case or restore a soft-deleted one with the same name."""
        # Check if there's a soft-deleted case with the same name and category
        existing_deleted = self.db.query(Case).filter(
            Case.name == case_data.name,
            Case.category_id == case_data.category_id,
            Case.is_deleted == True,
        ).first()
        
        if existing_deleted:
            # Restore and update the deleted case
            existing_deleted.is_deleted = False
            existing_deleted.deleted_at = None
            existing_deleted.risk_level = case_data.risk_level
            existing_deleted.description = case_data.description
            existing_deleted.fix_suggestion = case_data.fix_suggestion
            existing_deleted.script_path = case_data.script_path
            existing_deleted.is_enabled = True
            existing_deleted.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_deleted)
            return existing_deleted
        
        case = Case(
            name=case_data.name,
            category_id=case_data.category_id,
            risk_level=case_data.risk_level,
            description=case_data.description,
            fix_suggestion=case_data.fix_suggestion,
            script_path=case_data.script_path,
        )
        self.db.add(case)
        self.db.commit()
        self.db.refresh(case)
        return case
    
    def update(self, case: Case, case_data: CaseUpdate) -> Case:
        """Update case fields."""
        update_data = case_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(case, field, value)
        case.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(case)
        return case
    
    def soft_delete(self, case: Case) -> Case:
        """Soft delete a case."""
        case.is_deleted = True
        case.deleted_at = datetime.utcnow()
        case.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(case)
        return case
    
    def toggle_enabled(self, case: Case) -> Case:
        """Toggle case enabled status."""
        case.is_enabled = not case.is_enabled
        case.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(case)
        return case
    
    def check_name_unique(
        self,
        name: str,
        category_id: int,
        exclude_id: Optional[int] = None,
    ) -> bool:
        """Check if case name is unique within category."""
        query = self.db.query(Case).filter(
            Case.name == name,
            Case.category_id == category_id,
            Case.is_deleted == False,
        )
        if exclude_id:
            query = query.filter(Case.id != exclude_id)
        return query.first() is None
    
    def category_exists(self, category_id: int) -> bool:
        """Check if category exists."""
        return self.db.query(Category).filter(Category.id == category_id).first() is not None
