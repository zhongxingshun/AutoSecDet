"""
Execution service for managing task execution state and progress.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.task import Task
from app.models.task_result import TaskResult
from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    ERROR = "error"


class ResultStatus:
    """Task result status constants."""
    PENDING = "pending"
    RUNNING = "running"
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"


class ExecutionService:
    """Service class for task execution state management."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def start_task(self, task_id: int) -> Optional[Task]:
        """
        Start a task execution.
        
        Args:
            task_id: Task ID to start
            
        Returns:
            Updated task or None if not found
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            logger.error(f"Task {task_id} not found")
            return None
        
        if task.status != TaskStatus.PENDING:
            logger.warning(f"Task {task_id} is not in pending state: {task.status}")
            return task
        
        task.status = TaskStatus.RUNNING
        task.start_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        
        logger.info(f"Task {task_id} started")
        return task
    
    def start_result(self, result_id: int) -> Optional[TaskResult]:
        """
        Mark a task result as running.
        
        Args:
            result_id: TaskResult ID
            
        Returns:
            Updated result or None
        """
        result = self.db.query(TaskResult).filter(TaskResult.id == result_id).first()
        if not result:
            return None
        
        result.status = ResultStatus.RUNNING
        result.start_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def complete_result(
        self,
        result_id: int,
        status: str,
        error_message: Optional[str] = None,
        log_path: Optional[str] = None,
    ) -> Optional[TaskResult]:
        """
        Complete a task result with final status.
        
        Args:
            result_id: TaskResult ID
            status: Final status (pass, fail, error)
            error_message: Optional error message
            log_path: Optional path to execution log
            
        Returns:
            Updated result or None
        """
        result = self.db.query(TaskResult).filter(TaskResult.id == result_id).first()
        if not result:
            return None
        
        result.status = status
        result.end_time = datetime.utcnow()
        result.error_message = error_message
        result.log_path = log_path
        self.db.commit()
        self.db.refresh(result)
        
        # Update task progress
        self._update_task_progress(result.task_id)
        
        return result
    
    def retry_result(self, result_id: int) -> Optional[TaskResult]:
        """
        Increment retry count for a result.
        
        Args:
            result_id: TaskResult ID
            
        Returns:
            Updated result or None
        """
        result = self.db.query(TaskResult).filter(TaskResult.id == result_id).first()
        if not result:
            return None
        
        result.retry_count += 1
        result.status = ResultStatus.PENDING
        result.start_time = None
        result.end_time = None
        result.error_message = None
        self.db.commit()
        self.db.refresh(result)
        return result
    
    def _update_task_progress(self, task_id: int) -> None:
        """
        Update task progress based on completed results.
        
        Args:
            task_id: Task ID to update
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return
        
        # Count results by status
        results = self.db.query(TaskResult).filter(TaskResult.task_id == task_id).all()
        
        completed = 0
        passed = 0
        failed = 0
        errors = 0
        
        for r in results:
            if r.status in (ResultStatus.PASS, ResultStatus.FAIL, ResultStatus.ERROR):
                completed += 1
                if r.status == ResultStatus.PASS:
                    passed += 1
                elif r.status == ResultStatus.FAIL:
                    failed += 1
                elif r.status == ResultStatus.ERROR:
                    errors += 1
        
        task.completed_cases = completed
        task.passed_count = passed
        task.failed_count = failed
        task.error_count = errors
        
        # Check if task is complete
        if completed >= task.total_cases:
            task.status = TaskStatus.COMPLETED
            task.end_time = datetime.utcnow()
            logger.info(f"Task {task_id} completed: passed={passed}, failed={failed}, errors={errors}")
        
        self.db.commit()
    
    def complete_task_with_error(self, task_id: int, error_message: str) -> Optional[Task]:
        """
        Mark a task as failed with error.
        
        Args:
            task_id: Task ID
            error_message: Error description
            
        Returns:
            Updated task or None
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        task.status = TaskStatus.ERROR
        task.end_time = datetime.utcnow()
        self.db.commit()
        self.db.refresh(task)
        
        logger.error(f"Task {task_id} failed: {error_message}")
        return task
    
    def get_pending_results(self, task_id: int) -> list[TaskResult]:
        """
        Get all pending results for a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            List of pending TaskResult objects
        """
        return (
            self.db.query(TaskResult)
            .filter(TaskResult.task_id == task_id, TaskResult.status == ResultStatus.PENDING)
            .order_by(TaskResult.id)
            .all()
        )
    
    def is_task_stopped(self, task_id: int) -> bool:
        """
        Check if a task has been stopped.
        
        Args:
            task_id: Task ID
            
        Returns:
            True if task is stopped
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        return task is not None and task.status == TaskStatus.STOPPED
    
    def get_task_stats(self, task_id: int) -> dict:
        """
        Get task execution statistics.
        
        Args:
            task_id: Task ID
            
        Returns:
            Dictionary with task statistics
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return {}
        
        progress = (task.completed_cases / task.total_cases * 100) if task.total_cases > 0 else 0
        
        return {
            "task_id": task.id,
            "status": task.status,
            "total_cases": task.total_cases,
            "completed_cases": task.completed_cases,
            "passed_count": task.passed_count,
            "failed_count": task.failed_count,
            "error_count": task.error_count,
            "progress": round(progress, 1),
        }
    
    def can_retry_result(self, result: TaskResult, max_retries: int = 3) -> bool:
        """
        Check if a result can be retried.
        
        Args:
            result: TaskResult to check
            max_retries: Maximum retry attempts
            
        Returns:
            True if retry is allowed
        """
        return result.retry_count < max_retries and result.status == ResultStatus.ERROR
    
    def retry_failed_results(self, task_id: int, max_retries: int = 3) -> int:
        """
        Retry all failed results for a task.
        
        Args:
            task_id: Task ID
            max_retries: Maximum retry attempts
            
        Returns:
            Number of results queued for retry
        """
        results = (
            self.db.query(TaskResult)
            .filter(
                TaskResult.task_id == task_id,
                TaskResult.status == ResultStatus.ERROR,
                TaskResult.retry_count < max_retries,
            )
            .all()
        )
        
        retry_count = 0
        for result in results:
            self.retry_result(result.id)
            retry_count += 1
        
        # Reset task status if there are retries
        if retry_count > 0:
            task = self.db.query(Task).filter(Task.id == task_id).first()
            if task and task.status in (TaskStatus.COMPLETED, TaskStatus.ERROR):
                task.status = TaskStatus.PENDING
                task.end_time = None
                self.db.commit()
        
        logger.info(f"Task {task_id}: {retry_count} results queued for retry")
        return retry_count
    
    def mark_task_stopped(self, task_id: int) -> Optional[Task]:
        """
        Mark a task as stopped and cancel pending results.
        
        Args:
            task_id: Task ID
            
        Returns:
            Updated task or None
        """
        task = self.db.query(Task).filter(Task.id == task_id).first()
        if not task:
            return None
        
        if task.status not in (TaskStatus.PENDING, TaskStatus.RUNNING):
            return task
        
        task.status = TaskStatus.STOPPED
        task.end_time = datetime.utcnow()
        
        # Mark all pending/running results as cancelled
        self.db.query(TaskResult).filter(
            TaskResult.task_id == task_id,
            TaskResult.status.in_([ResultStatus.PENDING, ResultStatus.RUNNING]),
        ).update(
            {"status": ResultStatus.ERROR, "error_message": "Task stopped by user"},
            synchronize_session=False,
        )
        
        self.db.commit()
        self.db.refresh(task)
        
        # Update final counts
        self._update_task_progress(task_id)
        
        logger.info(f"Task {task_id} stopped")
        return task
