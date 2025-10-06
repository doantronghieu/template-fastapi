"""Example Celery tasks for background processing."""

from app.core.celery import celery_app
from app.core.config import settings


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.example_extension_task")
def process_example_data(data: str) -> dict:
    """Example background task.

    Args:
        data: Sample data to process

    Returns:
        Processing result
    """
    # Simulate processing
    result = f"Processed: {data}"
    return {"status": "completed", "result": result}
