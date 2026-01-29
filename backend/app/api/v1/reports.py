"""
Report API endpoints.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse

from app.api.deps import CurrentUser, DBSession
from app.services.report_service import ReportService
from app.services.task_service import TaskService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/tasks/{task_id}")
async def get_task_report(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Get task report data as JSON.
    """
    task_service = TaskService(db)
    report_service = ReportService(db)
    
    task = task_service.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    data = report_service.get_task_report_data(task_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report data not found",
        )
    
    return data


@router.get("/tasks/{task_id}/export/json")
async def export_task_report_json(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Export task report as JSON file.
    """
    task_service = TaskService(db)
    report_service = ReportService(db)
    
    task = task_service.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    filepath = report_service.export_json(task_id)
    if filepath is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        )
    
    return FileResponse(
        path=filepath,
        filename=Path(filepath).name,
        media_type="application/json",
    )


@router.get("/tasks/{task_id}/export/html")
async def export_task_report_html(
    task_id: int,
    current_user: CurrentUser,
    db: DBSession,
):
    """
    Export task report as HTML file.
    """
    task_service = TaskService(db)
    report_service = ReportService(db)
    
    task = task_service.get_by_id(task_id)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    filepath = report_service.export_html(task_id)
    if filepath is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate report",
        )
    
    return FileResponse(
        path=filepath,
        filename=Path(filepath).name,
        media_type="text/html",
    )
