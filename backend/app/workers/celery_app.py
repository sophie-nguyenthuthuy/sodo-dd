from celery import Celery

from app.config import settings
from app.logging import configure_logging

configure_logging()

celery_app = Celery(
    "sodo_dd",
    broker=str(settings.celery_broker_url),
    backend=str(settings.celery_result_backend),
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_default_retry_delay=10,
    task_time_limit=600,
    task_soft_time_limit=540,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=200,
    beat_schedule={
        "purge-stale-jobs": {
            "task": "app.workers.tasks.purge_stale_jobs",
            "schedule": 300.0,
        },
    },
)
