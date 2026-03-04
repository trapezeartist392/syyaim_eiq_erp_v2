"""Celery application for background AI agent tasks.

NOTE: Celery + Redis is optional. The core ERP runs without it.
Agent tasks run synchronously when triggered via API endpoints.
To enable scheduled background tasks, set REDIS_URL in .env and
run a Celery worker + beat alongside the application.
"""
import logging

logger = logging.getLogger(__name__)

try:
    from celery import Celery
    from app.core.config import settings

    REDIS_URL = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    celery_app = Celery(
        "syyaimeiq",
        broker=REDIS_URL,
        backend=REDIS_URL,
        include=[
            "app.agents.tasks",
        ],
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="Asia/Kolkata",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        task_routes={
            "app.agents.tasks.*": {"queue": "agents"},
            "*": {"queue": "default"},
        },
        beat_schedule={
            "mrp-planning-agent": {
                "task": "app.agents.tasks.run_mrp_planning",
                "schedule": 21600.0,
            },
            "reorder-point-agent": {
                "task": "app.agents.tasks.check_reorder_points",
                "schedule": 7200.0,
            },
            "attendance-anomaly-agent": {
                "task": "app.agents.tasks.detect_attendance_anomalies",
                "schedule": 86400.0,
            },
            "ar-collection-agent": {
                "task": "app.agents.tasks.run_ar_collection_followup",
                "schedule": 86400.0,
            },
            "vendor-performance-agent": {
                "task": "app.agents.tasks.score_vendor_performance",
                "schedule": 604800.0,
            },
            "financial-anomaly-agent": {
                "task": "app.agents.tasks.detect_financial_anomalies",
                "schedule": 14400.0,
            },
        },
    )
except ImportError:
    logger.warning("Celery not available — background tasks disabled")
    celery_app = None
