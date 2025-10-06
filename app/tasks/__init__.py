"""Auto-import all task modules for Celery discovery."""

from app.utils.auto_import import auto_import

auto_import(__file__, "app.tasks")
