"""
Celery application setup.
Redis is used as both broker and result backend.
"""
from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

celery_app = Celery(
    "witness",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.transcription",
        "app.tasks.extraction",
        "app.tasks.missed_checker",
        "app.tasks.auto_activator",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    broker_connection_retry_on_startup=True,
    beat_schedule={
        # Har ghante missed commitments check karo
        "check-missed-commitments": {
            "task": "app.tasks.missed_checker.check_missed_commitments",
            "schedule": crontab(minute=0, hour="*"),
        },
        # Har 30 minute mein DETECTED → ACTIVE auto promote karo (2 hr baad)
        "auto-activate-commitments": {
            "task": "app.tasks.auto_activator.auto_activate_commitments",
            "schedule": crontab(minute="*/30"),
        },
    },
)