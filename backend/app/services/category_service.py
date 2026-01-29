"""
Category service for test case classification management.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.case import Case
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    """Service class for category-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, category_id: int) -> Optional[Category]:
        """Get category by ID."""
        return self.db.query(Category).filter(Category.id == category_id).first()
    
    def get_by_name(self, name: str) -> Optional[Category]:
        """Get category by name."""
        return self.db.query(Category).filter(Category.name == name).first()
    
    def get_all(self) -> List[Category]:
        """Get all categories ordered by sort_order."""
        return self.db.query(Category).order_by(Category.sort_order, Category.id).all()
    
    def count(self) -> int:
        """Get total category count."""
        return self.db.query(Category).count()
    
    def get_case_counts(self) -> dict:
        """Get case count for each category."""
        results = (
            self.db.query(Category.id, func.count(Case.id))
            .outerjoin(Case, (Case.category_id == Category.id) & (Case.is_deleted == False))
            .group_by(Category.id)
            .all()
        )
        return {category_id: count for category_id, count in results}
    
    def create(self, category_data: CategoryCreate) -> Category:
        """Create a new category."""
        # Get max sort_order if not specified
        if category_data.sort_order == 0:
            max_order = self.db.query(func.max(Category.sort_order)).scalar() or 0
            sort_order = max_order + 1
        else:
            sort_order = category_data.sort_order
        
        category = Category(
            name=category_data.name,
            description=category_data.description,
            sort_order=sort_order,
        )
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def update(self, category: Category, category_data: CategoryUpdate) -> Category:
        """Update category fields."""
        update_data = category_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(category, field, value)
        category.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(category)
        return category
    
    def delete(self, category: Category) -> None:
        """Delete a category (hard delete)."""
        self.db.delete(category)
        self.db.commit()
    
    def has_cases(self, category_id: int) -> bool:
        """Check if category has any cases (including deleted)."""
        return (
            self.db.query(Case)
            .filter(Case.category_id == category_id, Case.is_deleted == False)
            .first() is not None
        )
    
    def check_name_unique(self, name: str, exclude_id: Optional[int] = None) -> bool:
        """Check if category name is unique."""
        query = self.db.query(Category).filter(Category.name == name)
        if exclude_id:
            query = query.filter(Category.id != exclude_id)
        return query.first() is None
    
    def reorder(self, category_orders: List[dict]) -> None:
        """
        Reorder categories.
        
        Args:
            category_orders: List of {"id": int, "sort_order": int}
        """
        for item in category_orders:
            category = self.get_by_id(item["id"])
            if category:
                category.sort_order = item["sort_order"]
                category.updated_at = datetime.utcnow()
        self.db.commit()
