"""
Task management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.api.deps import CurrentUser, DBSession
from app.schemas.task import (
    TaskCreate,
    TaskResponse,
    TaskListResponse,
    TaskDetailResponse,
    TaskResultResponse,
    TaskFilter,
)
from app.services.task_service import TaskService
from app.services.case_service import CaseService
from app.services.audit_service import AuditService
from app.tasks.executor import execute_task

router = APIRouter(prefix="/tasks", tags=["Tasks"])


def task_to_response(task, db: Session) -> TaskResponse:
    """Convert task model to response."""
    task_service = TaskService(db)
    username = task_service.get_username(task.user_id)
    progress = (task.completed_cases / task.total_cases * 100) if task.total_cases > 0 else 0
    
    return TaskResponse(
        id=task.id,
        target_ip=task.target_ip,
        user_id=task.user_id,
        username=username,
        status=task.status,
        total_cases=task.total_cases,
        completed_cases=task.completed_cases,
        passed_count=task.passed_count,
        failed_count=task.failed_count,
        error_count=task.error_count,
        progress=round(progress, 1),
        start_time=task.start_time,
        end_time=task.end_time,
        created_at=task.created_at,
    )


@router.get("", response_model=TaskListResponse)
async def list_tasks(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status: str = Query(None, pattern="^(pending|running|completed|stopped|error)$"),
    target_ip: str = Query(None),
    my_tasks: bool = Query(False, description="Only show my tasks"),
):
    """
    List all tasks with pagination and filtering.
    """
    task_service = TaskService(db)
    skip = (page - 1) * page_size
    
    filters = TaskFilter(
        status=status,
        target_ip=target_ip,
        user_id=current_user.id if my_tasks else None,
    )
    
    tasks = task_service.get_all(skip=skip, limit=page_size, filters=filters)
    total = task_service.count(filters=filters)
    
    return TaskListResponse(
        items=[task_to_response(t, db) for t in tasks],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Create a new detection task.
    
    - **target_ip**: Target IP address to scan (IPv4 format)
    - **case_ids**: Optional list of specific case IDs. If not provided, runs all enabled cases.
    """
    task_service = TaskService(db)
    case_service = CaseService(db)
    audit_service = AuditService(db)
    
    # Validate case_ids if provided
    if task_data.case_ids:
        for case_id in task_data.case_ids:
            case = case_service.get_by_id(case_id)
            if case is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Case with ID {case_id} not found",
                )
            if not case.is_enabled:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Case with ID {case_id} is disabled",
                )
    else:
        # Check if there are any enabled cases
        enabled_cases = case_service.get_enabled_cases()
        if not enabled_cases:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No enabled cases available for execution",
            )
    
    # Create task
    task = task_service.create(task_data, current_user.id, task_data.case_ids)
    
    # Log audit
    audit_service.log(
        action="create",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="task",
        resource_id=task.id,
        details={"target_ip": task.target_ip, "total_cases": task.total_cases},
    )
    
    # Trigger async execution
    execute_task.delay(task.id)
    
    return task_to_response(task, db)


@router.get("/{task_id}", response_model=TaskDetailResponse)
async def get_task(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Get task details with results.
    """
    task_service = TaskService(db)
    task = task_service.get_by_id(task_id)
    
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    # Get task results
    results = task_service.get_task_results(task_id)
    result_responses = []
    for r in results:
        case_info = task_service.get_case_info(r.case_id)
        result_responses.append(TaskResultResponse(
            id=r.id,
            task_id=r.task_id,
            case_id=r.case_id,
            case_name=case_info["case_name"],
            category_name=case_info["category_name"],
            risk_level=case_info["risk_level"],
            status=r.status,
            retry_count=r.retry_count,
            start_time=r.start_time,
            end_time=r.end_time,
            error_message=r.error_message,
        ))
    
    username = task_service.get_username(task.user_id)
    progress = (task.completed_cases / task.total_cases * 100) if task.total_cases > 0 else 0
    
    return TaskDetailResponse(
        id=task.id,
        target_ip=task.target_ip,
        user_id=task.user_id,
        username=username,
        status=task.status,
        total_cases=task.total_cases,
        completed_cases=task.completed_cases,
        passed_count=task.passed_count,
        failed_count=task.failed_count,
        error_count=task.error_count,
        progress=round(progress, 1),
        start_time=task.start_time,
        end_time=task.end_time,
        created_at=task.created_at,
        results=result_responses,
    )


@router.post("/{task_id}/stop")
async def stop_task(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Stop a running task.
    """
    task_service = TaskService(db)
    audit_service = AuditService(db)
    
    task = task_service.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    if task.status not in ("pending", "running"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop task with status: {task.status}",
        )
    
    task_service.stop_task(task)
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="task",
        resource_id=task_id,
        details={"action": "stop"},
    )
    
    return {"message": "Task stopped successfully"}


@router.post("/{task_id}/retry")
async def retry_task(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Retry failed cases in a task.
    """
    from app.services.execution_service import ExecutionService
    
    task_service = TaskService(db)
    execution_service = ExecutionService(db)
    audit_service = AuditService(db)
    
    task = task_service.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    if task.status not in ("completed", "error", "stopped"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot retry task with status: {task.status}",
        )
    
    retry_count = execution_service.retry_failed_results(task_id)
    
    if retry_count == 0:
        return {"message": "No failed cases to retry", "retry_count": 0}
    
    # Log audit
    audit_service.log(
        action="update",
        user_id=current_user.id,
        username=current_user.username,
        resource_type="task",
        resource_id=task_id,
        details={"action": "retry", "retry_count": retry_count},
    )
    
    # Trigger async execution
    execute_task.delay(task_id)
    
    return {"message": f"Retrying {retry_count} failed cases", "retry_count": retry_count}
