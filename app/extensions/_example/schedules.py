"""Example beat schedules for _example extension.

Schedules are auto-discovered from schedules.py and prefixed with extension name.
"""

from celery.schedules import crontab

from app.core.config import settings

SCHEDULES = {
    # Example: Run every minute for testing
    "example-task-every-minute": {
        "task": f"{settings.CELERY_TASKS_MODULE}.example_extension_task",
        "schedule": crontab(),  # Every minute
        "args": ("scheduled-data",),
    },
}
