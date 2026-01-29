"""
Celery worker entry point.

Usage:
    # Start worker
    celery -A celery_worker.celery_app worker --loglevel=info
    
    # Start beat scheduler
    celery -A celery_worker.celery_app beat --loglevel=info
    
    # Start worker with beat (development only)
    celery -A celery_worker.celery_app worker --beat --loglevel=info
"""
from app.core.celery import celery_app

# Import tasks to register them
from app.tasks import (
    cleanup_expired_logs,
    cleanup_expired_tasks,
    archive_audit_logs,
    execute_task,
    test_celery,
)

__all__ = ["celery_app"]
