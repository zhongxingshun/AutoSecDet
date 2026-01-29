"""
Task service for detection task management.
"""
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_result import TaskResult
from app.models.case import Case
from app.models.user import User
from app.schemas.task import TaskCreate, TaskFilter


class TaskService:
    """Service class for task-related operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID."""
        return self.db.query(Task).filter(Task.id == task_id).first()
    
    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[TaskFilter] = None,
    ) -> List[Task]:
        """Get all tasks with pagination and filtering."""
        query = self.db.query(Task)
        
        if filters:
            if filters.status is not None:
                query = query.filter(Task.status == filters.status)
            if filters.target_ip is not None:
                query = query.filter(Task.target_ip == filters.target_ip)
            if filters.user_id is not None:
                query = query.filter(Task.user_id == filters.user_id)
        
        return query.order_by(Task.created_at.desc()).offset(skip).limit(limit).all()
    
    def count(self, filters: Optional[TaskFilter] = None) -> int:
        """Get total task count with optional filtering."""
        query = self.db.query(Task)
        
        if filters:
            if filters.status is not None:
                query = query.filter(Task.status == filters.status)
            if filters.target_ip is not None:
                query = query.filter(Task.target_ip == filters.target_ip)
            if filters.user_id is not None:
                query = query.filter(Task.user_id == filters.user_id)
        
        return query.count()
    
    def create(self, task_data: TaskCreate, user_id: int, case_ids: Optional[List[int]] = None) -> Task:
        """
        Create a new task with task results for each case.
        
        Args:
            task_data: Task creation data
            user_id: ID of the user creating the task
            case_ids: Optional list of specific case IDs. If None, uses all enabled cases.
            
        Returns:
            Created task
        """
        # Get cases to execute
        if case_ids:
            cases = (
                self.db.query(Case)
                .filter(Case.id.in_(case_ids), Case.is_deleted == False, Case.is_enabled == True)
                .all()
            )
        else:
            cases = (
                self.db.query(Case)
                .filter(Case.is_deleted == False, Case.is_enabled == True)
                .order_by(Case.category_id, Case.id)
                .all()
            )
        
        # Create task
        task = Task(
            target_ip=task_data.target_ip,
            user_id=user_id,
            status="pending",
            total_cases=len(cases),
            completed_cases=0,
            passed_count=0,
            failed_count=0,
            error_count=0,
        )
        self.db.add(task)
        self.db.flush()  # Get task ID
        
        # Create task results for each case
        for case in cases:
            task_result = TaskResult(
                task_id=task.id,
                case_id=case.id,
                status="pending",
                retry_count=0,
            )
            self.db.add(task_result)
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_task_results(self, task_id: int) -> List[TaskResult]:
        """Get all results for a task."""
        return (
            self.db.query(TaskResult)
            .filter(TaskResult.task_id == task_id)
            .order_by(TaskResult.id)
            .all()
        )
    
    def update_status(self, task: Task, status: str) -> Task:
        """Update task status."""
        task.status = status
        if status == "running" and task.start_time is None:
            task.start_time = datetime.utcnow()
        elif status in ("completed", "stopped", "error"):
            task.end_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def stop_task(self, task: Task) -> Task:
        """Stop a running task."""
        if task.status not in ("pending", "running"):
            return task
        
        task.status = "stopped"
        task.end_time = datetime.utcnow()
        
        # Mark pending results as stopped
        self.db.query(TaskResult).filter(
            TaskResult.task_id == task.id,
            TaskResult.status == "pending",
        ).update({"status": "error", "error_message": "Task stopped by user"})
        
        self.db.commit()
        self.db.refresh(task)
        return task
    
    def get_username(self, user_id: int) -> Optional[str]:
        """Get username by user ID."""
        user = self.db.query(User).filter(User.id == user_id).first()
        return user.username if user else None
    
    def get_case_info(self, case_id: int) -> dict:
        """Get case info for result display."""
        case = self.db.query(Case).filter(Case.id == case_id).first()
        if case:
            from app.models.category import Category
            category = self.db.query(Category).filter(Category.id == case.category_id).first()
            return {
                "case_name": case.name,
                "category_name": category.name if category else None,
                "risk_level": case.risk_level,
            }
        return {"case_name": None, "category_name": None, "risk_level": None}
