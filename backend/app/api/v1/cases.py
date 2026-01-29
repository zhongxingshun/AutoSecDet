"""
Case management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import CurrentUser, AdminUser, DBSession
from app.schemas.case import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseListResponse,
    CaseFilter,
)
from app.services.case_service import CaseService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/cases", tags=["Cases"])


def case_to_response(case, db: Session) -> CaseResponse:
    """Convert case model to response with category name."""
    from app.models.category import Category
    category = db.query(Category).filter(Category.id == case.category_id).first()
    return CaseResponse(
        id=case.id,
        name=case.name,
        category_id=case.category_id,
        category_name=category.name if category else None,
        risk_level=case.risk_level,
        description=case.description,
        fix_suggestion=case.fix_suggestion,
        script_path=case.script_path,
        is_enabled=case.is_enabled,
        created_at=case.created_at,
        updated_at=case.updated_at,
    )


@router.get("", response_model=CaseListResponse)
async def list_cases(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    category_id: int = Query(None, description="Filter by category"),
    risk_level: str = Query(None, pattern="^(high|medium|low)$", description="Filter by risk level"),
    is_enabled: bool = Query(None, description="Filter by enabled status"),
    keyword: str = Query(None, description="Search keyword"),
):
    """
    List all cases with pagination and filtering.
    """
    case_service = CaseService(db)
    skip = (page - 1) * page_size
    
    filters = CaseFilter(
        category_id=category_id,
        risk_level=risk_level,
        is_enabled=is_enabled,
        keyword=keyword,
    )
    
    cases = case_service.get_all(skip=skip, limit=page_size, filters=filters)
    total = case_service.count(filters=filters)
    
    return CaseListResponse(
        items=[case_to_response(c, db) for c in cases],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
async def create_case(
    case_data: CaseCreate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Create a new test case. (Admin only)
    """
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    # Check if category exists
    if not case_service.category_exists(case_data.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category not found",
        )
    
    # Check name uniqueness within category
    if not case_service.check_name_unique(case_data.name, case_data.category_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case name already exists in this category",
        )
    
    case = case_service.create(case_data)
    
    # Log audit
    audit_service.log(
        action="create",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="case",
        resource_id=case.id,
        details={"name": case.name, "category_id": case.category_id},
    )
    
    return case_to_response(case, db)


@router.get("/{case_id}", response_model=CaseResponse)
async def get_case(
    case_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Get case by ID.
    """
    case_service = CaseService(db)
    case = case_service.get_by_id(case_id)
    
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    return case_to_response(case, db)


@router.put("/{case_id}", response_model=CaseResponse)
async def update_case(
    case_id: int,
    case_data: CaseUpdate,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Update a test case. (Admin only)
    """
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    case = case_service.get_by_id(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    # Check category if being updated
    if case_data.category_id is not None:
        if not case_service.category_exists(case_data.category_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category not found",
            )
    
    # Check name uniqueness if name or category is being updated
    new_name = case_data.name or case.name
    new_category_id = case_data.category_id or case.category_id
    if not case_service.check_name_unique(new_name, new_category_id, exclude_id=case_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case name already exists in this category",
        )
    
    updated_case = case_service.update(case, case_data)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="case",
        resource_id=case_id,
        details=case_data.model_dump(exclude_unset=True),
    )
    
    return case_to_response(updated_case, db)


@router.delete("/{case_id}")
async def delete_case(
    case_id: int,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Soft delete a test case. (Admin only)
    """
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    case = case_service.get_by_id(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    case_service.soft_delete(case)
    
    # Log audit
    audit_service.log(
        action="delete",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="case",
        resource_id=case_id,
        details={"name": case.name},
    )
    
    return {"message": "Case deleted successfully"}


@router.post("/{case_id}/toggle")
async def toggle_case_status(
    case_id: int,
    current_user: AdminUser,
    db: DBSession,
):
    """
    Toggle case enabled/disabled status. (Admin only)
    """
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    case = case_service.get_by_id(case_id)
    if case is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )
    
    updated_case = case_service.toggle_enabled(case)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="case",
        resource_id=case_id,
        details={"is_enabled": updated_case.is_enabled},
    )
    
    return {
        "message": f"Case {'enabled' if updated_case.is_enabled else 'disabled'} successfully",
        "is_enabled": updated_case.is_enabled,
    }
