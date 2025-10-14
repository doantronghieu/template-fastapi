"""Task context utilities for accessing task ID across Celery tasks.

This module avoids circular imports by separating context management
from the main celery.py module.
"""

from contextvars import ContextVar

# Context variable for task ID (automatically set via Celery signals)
task_id_var: ContextVar[str | None] = ContextVar("task_id", default=None)


def get_task_id() -> str:
    """Get current task ID prefix for logging.

    Returns formatted prefix like "[b83caca6] " or empty string if no task context.
    Usage: logger.info(f"{get_task_id()}Processing...")
    """
    task_id = task_id_var.get()
    return f"[{task_id[:8]}] " if task_id else ""
