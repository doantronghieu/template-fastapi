"""Example Celery tasks for background processing."""

from app.core.celery import celery_app
from app.core.config import settings

from .config import extension_settings


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.example_extension_task")
def process_example_data(data: str) -> dict:
    """Example background task demonstrating extension config usage.

    Args:
        data: Sample data to process

    Returns:
        Processing result with config values
    """
    api_key = extension_settings.EXAMPLE_API_KEY

    result = f"Processed: {data} (api_key={api_key[:8]}...)"
    return {
        "status": "completed",
        "result": result,
        "config": {
            "api_key_prefix": api_key[:8],
        },
    }
