"""
Category management API endpoints.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, AdminUser, DBSession
from app.schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    CategoryResponse,
    CategoryListResponse,
)
from app.services.category_service import CategoryService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/categories", tags=["Categories"])


class CategoryOrderItem(BaseModel):
    """Schema for category reorder item."""
    id: int
    sort_order: int = Field(..., ge=0)


class CategoryReorderRequest(BaseModel):
    """Schema for category reorder request."""
    orders: List[CategoryOrderItem]


@router.get("", response_model=CategoryListResponse)
async def list_categories(
    current_user: CurrentUser,
    db: DBSession,
):
    """
    List all categories with case counts.
    """
    category_service = CategoryService(db)
    
    categories = category_service.get_all()
    case_counts = category_service.get_case_counts()
    total = len(categories)
    
    items = []
    for cat in categories:
        items.append(CategoryResponse(
            id=cat.id,
            name=cat.name,
            description=cat.description,
            sort_order=cat.sort_order,
            case_count=case_counts.get(cat.id, 0),
            created_at=cat.created_at,
            updated_at=cat.updated_at,
        ))
    
    return CategoryListResponse(items=items, total=total)


@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Create a new category. (Admin only)
    """
    category_service = CategoryService(db)
    audit_service = AuditService(db)
    
    # Check name uniqueness
    if not category_service.check_name_unique(category_data.name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name already exists",
        )
    
    category = category_service.create(category_data)
    
    # Log audit
    audit_service.log(
        action="create",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=category.id,
        details={"name": category.name},
    )
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        sort_order=category.sort_order,
        case_count=0,
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Get category by ID.
    """
    category_service = CategoryService(db)
    category = category_service.get_by_id(category_id)
    
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    case_counts = category_service.get_case_counts()
    
    return CategoryResponse(
        id=category.id,
        name=category.name,
        description=category.description,
        sort_order=category.sort_order,
        case_count=case_counts.get(category.id, 0),
        created_at=category.created_at,
        updated_at=category.updated_at,
    )


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Update a category. (Admin only)
    """
    category_service = CategoryService(db)
    audit_service = AuditService(db)
    
    category = category_service.get_by_id(category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Check name uniqueness if name is being updated
    if category_data.name is not None:
        if not category_service.check_name_unique(category_data.name, exclude_id=category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name already exists",
            )
    
    updated_category = category_service.update(category, category_data)
    case_counts = category_service.get_case_counts()
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=category_id,
        details=category_data.model_dump(exclude_unset=True),
    )
    
    return CategoryResponse(
        id=updated_category.id,
        name=updated_category.name,
        description=updated_category.description,
        sort_order=updated_category.sort_order,
        case_count=case_counts.get(updated_category.id, 0),
        created_at=updated_category.created_at,
        updated_at=updated_category.updated_at,
    )


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Delete a category. (Admin only)
    
    Note: Cannot delete category that has cases.
    """
    category_service = CategoryService(db)
    audit_service = AuditService(db)
    
    category = category_service.get_by_id(category_id)
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found",
        )
    
    # Check if category has cases
    if category_service.has_cases(category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with existing cases",
        )
    
    category_name = category.name
    category_service.delete(category)
    
    # Log audit
    audit_service.log(
        action="delete",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        resource_id=category_id,
        details={"name": category_name},
    )
    
    return {"message": "Category deleted successfully"}


@router.post("/reorder")
async def reorder_categories(
    reorder_data: CategoryReorderRequest,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Reorder categories. (Admin only)
    """
    category_service = CategoryService(db)
    audit_service = AuditService(db)
    
    # Validate all category IDs exist
    for item in reorder_data.orders:
        if category_service.get_by_id(item.id) is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {item.id} not found",
            )
    
    category_service.reorder([item.model_dump() for item in reorder_data.orders])
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="category",
        details={"action": "reorder", "orders": [item.model_dump() for item in reorder_data.orders]},
    )
    
    return {"message": "Categories reordered successfully"}
