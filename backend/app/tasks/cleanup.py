"""
Cleanup tasks for data lifecycle management.
"""
import os
from datetime import datetime, timedelta
from pathlib import Path

from app.core.celery import celery_app
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.logging import get_logger
from app.models import Task, TaskResult, AuditLog

logger = get_logger(__name__)


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_logs")
def cleanup_expired_logs():
    """
    Clean up execution log files older than LOG_RETENTION_DAYS (default: 30 days).
    Runs daily at 3:00 AM UTC.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=settings.LOG_RETENTION_DAYS)
    log_dir = Path(settings.LOGS_DIR)
    
    if not log_dir.exists():
        logger.warning(f"Log directory does not exist: {log_dir}")
        return {"deleted": 0, "errors": 0}
    
    deleted_count = 0
    error_count = 0
    
    for log_file in log_dir.glob("**/*.log"):
        try:
            file_mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                log_file.unlink()
                deleted_count += 1
                logger.debug(f"Deleted expired log: {log_file}")
        except Exception as e:
            error_count += 1
            logger.error(f"Failed to delete log file {log_file}: {e}")
    
    logger.info(f"Cleanup expired logs completed: deleted={deleted_count}, errors={error_count}")
    return {"deleted": deleted_count, "errors": error_count}


@celery_app.task(name="app.tasks.cleanup.cleanup_expired_tasks")
def cleanup_expired_tasks():
    """
    Clean up task records older than TASK_RETENTION_DAYS (default: 90 days).
    Also deletes associated task results and report files.
    Runs daily at 4:00 AM UTC.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=settings.TASK_RETENTION_DAYS)
    
    db = SessionLocal()
    try:
        # Find expired tasks
        expired_tasks = db.query(Task).filter(Task.created_at < cutoff_date).all()
        
        deleted_count = len(expired_tasks)
        
        # Delete associated report files
        reports_dir = Path(settings.REPORTS_DIR)
        for task in expired_tasks:
            report_pattern = f"task_{task.id}_*"
            for report_file in reports_dir.glob(report_pattern):
                try:
                    report_file.unlink()
                    logger.debug(f"Deleted report file: {report_file}")
                except Exception as e:
                    logger.error(f"Failed to delete report file {report_file}: {e}")
        
        # Delete tasks (cascade will delete task_results)
        for task in expired_tasks:
            db.delete(task)
        
        db.commit()
        logger.info(f"Cleanup expired tasks completed: deleted={deleted_count}")
        return {"deleted": deleted_count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to cleanup expired tasks: {e}")
        raise
    finally:
        db.close()


@celery_app.task(name="app.tasks.cleanup.archive_audit_logs")
def archive_audit_logs():
    """
    Archive audit logs older than AUDIT_LOG_RETENTION_DAYS (default: 180 days).
    Runs weekly on Sunday at 5:00 AM UTC.
    
    Note: In production, this could export to external storage before deletion.
    For now, we simply delete old records.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS)
    
    db = SessionLocal()
    try:
        # Count records to be archived/deleted
        count = db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).count()
        
        if count == 0:
            logger.info("No audit logs to archive")
            return {"archived": 0}
        
        # Delete old audit logs
        db.query(AuditLog).filter(AuditLog.created_at < cutoff_date).delete()
        db.commit()
        
        logger.info(f"Archive audit logs completed: archived={count}")
        return {"archived": count}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to archive audit logs: {e}")
        raise
    finally:
        db.close()
