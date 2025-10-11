from celery import Celery

from app.core.config import settings

celery_app = Celery(
    settings.CELERY_APP_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[settings.CELERY_TASKS_MODULE],
)

celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    # Timezone
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    # Task configuration
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    result_expires=settings.CELERY_RESULT_EXPIRES,
    task_acks_late=settings.CELERY_TASK_ACKS_LATE,
    # Worker configuration
    worker_prefetch_multiplier=settings.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    # Redis Cloud free tier optimization (30 connection limit)
    # Target: <15 connections (~50% usage) to stay well below 80% alert threshold
    broker_pool_limit=1,  # Single connection pool for broker
    redis_max_connections=10,  # Global connection cap across all pools
    # Result backend connection pooling
    result_backend_transport_options={
        "max_connections": 5,
        "socket_keepalive": True,  # enabled for connection reuse
        "socket_keepalive_options": {1: 1, 2: 1, 3: 3},
    },
    # Broker transport connection pooling
    broker_transport_options={
        "max_connections": 5,
        "socket_keepalive": True,
        "visibility_timeout": 1800,  # 30 minutes
    },
)

# Load extension tasks for Celery discovery
from app.extensions import load_extensions  # noqa: E402

load_extensions("tasks")
