"""
Task execution module for running security detection tasks.
"""
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.engine.executor import ScriptExecutor
from app.services.execution_service import ExecutionService, TaskStatus, ResultStatus
from app.models.case import Case

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.executor.execute_task", bind=True)
def execute_task(self, task_id: int):
    """
    Execute a detection task asynchronously.
    
    Args:
        task_id: The ID of the task to execute
        
    Returns:
        dict: Execution result summary
    """
    logger.info(f"Starting execution of task {task_id}")
    
    db = SessionLocal()
    try:
        execution_service = ExecutionService(db)
        script_executor = ScriptExecutor()
        
        # Start task
        task = execution_service.start_task(task_id)
        if not task:
            logger.error(f"Task {task_id} not found")
            return {"task_id": task_id, "status": "error", "message": "Task not found"}
        
        # Get pending results
        pending_results = execution_service.get_pending_results(task_id)
        logger.info(f"Task {task_id}: {len(pending_results)} cases to execute")
        
        for result in pending_results:
            # Check if task was stopped
            if execution_service.is_task_stopped(task_id):
                logger.info(f"Task {task_id} was stopped, aborting execution")
                break
            
            # Get case info
            case = db.query(Case).filter(Case.id == result.case_id).first()
            if not case:
                execution_service.complete_result(
                    result.id,
                    ResultStatus.ERROR,
                    error_message="Case not found",
                )
                continue
            
            # Mark result as running
            execution_service.start_result(result.id)
            
            # Execute script
            logger.info(f"Task {task_id}: Executing case {case.id} - {case.name}")
            status, error_message, log_path = script_executor.execute(
                script_path=case.script_path,
                target_ip=task.target_ip,
                task_id=task_id,
                result_id=result.id,
            )
            
            # Update result
            execution_service.complete_result(
                result.id,
                status,
                error_message=error_message,
                log_path=log_path,
            )
            
            logger.info(f"Task {task_id}: Case {case.id} completed with status: {status}")
        
        # Get final stats
        stats = execution_service.get_task_stats(task_id)
        logger.info(f"Task {task_id} execution completed: {stats}")
        
        return {
            "task_id": task_id,
            "status": stats.get("status", "completed"),
            "passed": stats.get("passed_count", 0),
            "failed": stats.get("failed_count", 0),
            "errors": stats.get("error_count", 0),
        }
        
    except Exception as e:
        logger.exception(f"Task {task_id} execution failed: {e}")
        try:
            execution_service.complete_task_with_error(task_id, str(e))
        except Exception:
            pass
        return {"task_id": task_id, "status": "error", "message": str(e)}
    finally:
        db.close()


@celery_app.task(name="app.tasks.executor.test_celery")
def test_celery():
    """
    Test task to verify Celery is working correctly.
    
    Returns:
        dict: Test result
    """
    logger.info("Celery test task executed successfully")
    return {
        "status": "success",
        "message": "Celery is working correctly",
    }
