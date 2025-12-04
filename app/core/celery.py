"""Celery Task Queue Configuration.

Configures Celery with Redis Cloud broker/backend, Redbeat scheduler, and auto-discovery.
Optimized for Redis Cloud free tier (30 connection limit, ~33% usage target).

See docs/tech-stack.md for Celery configuration and connection optimization details.
See docs/patterns/logging.md for task ID context pattern.
"""

import importlib
import logging
import sys

from celery import Celery, signals

from app.core.config import settings
from app.core.task_context import task_id_var

# Configure basic logging early for module-level initialization
# This ensures logs during import are visible before Celery's logging setup
logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s/%(processName)s] %(message)s",
    stream=sys.stderr,
    force=True,  # Override any existing configuration
)

logger = logging.getLogger(__name__)


def _get_task_modules() -> list[str]:
    """Discover all task modules from core, features, and extensions.

    Returns:
        list: Task module paths for Celery include parameter
    """
    from pathlib import Path

    modules = [settings.CELERY_TASKS_MODULE]  # Core tasks

    # Discover feature task modules
    features_path = Path(__file__).parent.parent / "features"
    if features_path.exists():
        for feature_dir in features_path.iterdir():
            if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
                continue

            tasks_package = feature_dir / "tasks" / "__init__.py"
            tasks_file = feature_dir / "tasks.py"

            if tasks_package.exists() or tasks_file.exists():
                module_name = f"app.features.{feature_dir.name}.tasks"
                modules.append(module_name)
                logger.debug(f"Discovered feature tasks: {module_name}")

    return modules


celery_app = Celery(
    settings.CELERY_APP_NAME,
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=_get_task_modules(),
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
    # Connection budget breakdown (target: <10 total, ~33% usage):
    #   - FastAPI Producer: 2 connections (1 broker + 1 result backend)
    #   - Celery Worker: 3 connections (1 broker + 1 result + 1 worker pool)
    #   - Celery Beat: 3 connections (1 broker + 1 Redbeat scheduler + 1 result)
    #   - Flower: 2 connections (1 broker + 1 result for monitoring)
    #   = ~10 connections total (leaves 20 connections buffer for spikes)
    broker_pool_limit=1,  # Limit broker connection pool size per process
    redis_max_connections=2,  # Max Redis connections per process (broker + result)
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
