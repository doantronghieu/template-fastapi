"""Celery Task Queue Configuration.

Configures Celery with Redis broker/backend, Redbeat scheduler, and auto-discovery.

See docs/tech-stack.md for Celery configuration details.
See docs/patterns/logging.md for task ID context pattern.
"""

import logging
import sys
from contextvars import ContextVar

from celery import Celery, signals

from app.core.autodiscover import (
    ModuleType,
    autodiscover_beat_schedules,
    autodiscover_tasks,
)
from app.core.config import settings

# Context variable for task ID (automatically set via Celery signals)
task_id_var: ContextVar[str | None] = ContextVar("task_id", default=None)


def get_task_id() -> str:
    """Get current task ID prefix for logging.

    Returns formatted prefix like "[b83caca6] " or empty string if no task context.
    Usage: logger.info(f"{get_task_id()}Processing...")
    """
    task_id = task_id_var.get()
    return f"[{task_id[:8]}] " if task_id else ""


# Configure basic logging early for module-level initialization
# This ensures logs during import are visible before Celery's logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s/%(processName)s] %(message)s",
    stream=sys.stderr,
    force=True,  # Override any existing configuration
)

logger = logging.getLogger(__name__)


# === Discover Task Modules ===
task_modules = [settings.CELERY_TASKS_MODULE]  # Core tasks

for module_type in [
    ModuleType.FEATURES,
    ModuleType.INTEGRATIONS,
    ModuleType.EXTENSIONS,
]:
    task_modules += autodiscover_tasks(module_type)


celery_app = Celery(
    settings.CELERY_APP_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=task_modules,
)


# === Discover Beat Schedules ===
beat_schedules = {}

for module_type in [
    ModuleType.FEATURES,
    ModuleType.INTEGRATIONS,
    ModuleType.EXTENSIONS,
]:
    beat_schedules.update(autodiscover_beat_schedules(module_type))


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
    # Connection pooling
    broker_pool_limit=1,
    redis_max_connections=2,
    # Connection retry and resilience
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    # Result backend connection pooling (minimal for producer)
    result_backend_transport_options={
        "max_connections": 1,  # Single connection - producer rarely reads results
        "socket_keepalive": True,
        "socket_keepalive_options": {1: 1, 2: 1, 3: 3},
        "socket_connect_timeout": 5,
        "health_check_interval": 30,  # Check connection health every 30s
    },
    # Broker transport connection pooling (aggressive optimization for producer)
    broker_transport_options={
        "max_connections": 1,  # Single connection - producer only sends tasks
        "socket_keepalive": True,
        "visibility_timeout": 1800,  # 30 minutes
        "socket_connect_timeout": 5,
        "retry_on_timeout": True,
        "health_check_interval": 30,  # Check connection health every 30s
    },
    # Beat schedule from auto-discovery
    beat_schedule=beat_schedules,
)


# Automatic task ID binding via signals
@signals.task_prerun.connect
def bind_task_id(task_id, **_kwargs):
    """Automatically bind task ID to contextvar before task execution."""
    task_id_var.set(task_id)


@signals.task_postrun.connect
def unbind_task_id(**_kwargs):
    """Clear task ID from contextvar after task execution."""
    task_id_var.set(None)
