import importlib
import logging

from celery import Celery, signals

from app.core.config import settings
from app.core.task_context import task_id_var

logger = logging.getLogger(__name__)

celery_app = Celery(
    settings.CELERY_APP_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[settings.CELERY_TASKS_MODULE],
)


def load_extension_beat_schedules() -> dict:
    """Discover and merge beat schedules from enabled extensions.

    Scans {extension}/tasks/schedules.py for SCHEDULES dictionary.
    Automatically prefixes schedule keys with extension name to prevent conflicts.

    Returns:
        dict: Merged schedules from all enabled extensions
    """
    schedules = {}

    for ext_name in settings.ENABLED_EXTENSIONS:
        try:
            schedule_module = importlib.import_module(
                f"app.extensions.{ext_name}.tasks.schedules"
            )

            if hasattr(schedule_module, "SCHEDULES"):
                for key, value in schedule_module.SCHEDULES.items():
                    prefixed_key = f"{ext_name}.{key}"
                    schedules[prefixed_key] = value
                    logger.info(f"Registered beat schedule: {prefixed_key}")
            else:
                logger.warning(
                    f"Extension '{ext_name}' has tasks/schedules.py but no SCHEDULES defined"
                )

        except ImportError:
            # Extension doesn't have schedules - that's fine
            pass
        except Exception as e:
            # Log but don't fail - lenient error handling
            logger.warning(
                f"Failed to load schedules from extension '{ext_name}': {e}",
                exc_info=True,
            )

    return schedules


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
    # Target: <10 connections (~33% usage) to stay well below 80% alert threshold
    # With concurrency=1 and pool=solo, minimal connections needed
    broker_pool_limit=1,
    redis_max_connections=5,
    # Result backend connection pooling
    result_backend_transport_options={
        "max_connections": 2,
        "socket_keepalive": True,
        "socket_keepalive_options": {1: 1, 2: 1, 3: 3},
        "socket_connect_timeout": 5,
    },
    # Broker transport connection pooling
    broker_transport_options={
        "max_connections": 2,
        "socket_keepalive": True,
        "visibility_timeout": 1800,  # 30 minutes
        "socket_connect_timeout": 5,
    },
    # Beat schedule from extensions
    beat_schedule=load_extension_beat_schedules(),
)

# Load extension tasks for Celery discovery
from app.extensions import load_extensions  # noqa: E402

load_extensions("tasks")


# Automatic task ID binding via signals
@signals.task_prerun.connect
def bind_task_id(task_id, **_kwargs):
    """Automatically bind task ID to contextvar before task execution."""
    task_id_var.set(task_id)


@signals.task_postrun.connect
def unbind_task_id(**_kwargs):
    """Clear task ID from contextvar after task execution."""
    task_id_var.set(None)
