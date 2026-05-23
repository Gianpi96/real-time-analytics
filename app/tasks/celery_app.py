from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "analytics",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.scheduled_tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    enable_utc=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    beat_schedule={
        "aggregate-events-hourly": {
            "task": "app.tasks.scheduled_tasks.aggregate_events",
            # Runs at minute 0 of every hour
            "schedule": crontab(minute=0),
        },
        "generate-daily-insights": {
            "task": "app.tasks.scheduled_tasks.generate_daily_insights",
            # Runs every day at 01:00 UTC
            "schedule": crontab(hour=1, minute=0),
        },
    },
)
