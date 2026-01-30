"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "autosecdet",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Worker settings
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    
    # Task acknowledgment
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    
    # Result backend settings
    result_expires=3600,  # 1 hour
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Clean expired logs daily at 3:00 AM UTC
        "cleanup-expired-logs": {
            "task": "app.tasks.cleanup.cleanup_expired_logs",
            "schedule": crontab(hour=3, minute=0),
        },
        # Clean expired tasks daily at 4:00 AM UTC
        "cleanup-expired-tasks": {
            "task": "app.tasks.cleanup.cleanup_expired_tasks",
            "schedule": crontab(hour=4, minute=0),
        },
        # Archive audit logs weekly on Sunday at 5:00 AM UTC
        "archive-audit-logs": {
            "task": "app.tasks.cleanup.archive_audit_logs",
            "schedule": crontab(hour=5, minute=0, day_of_week=0),
        },
    },
)

# Auto-discover tasks from app.tasks package
celery_app.autodiscover_tasks(["app.tasks"])
