from app.core.celery import celery_app
from app.core.config import settings


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.add_numbers")
def add_numbers(x: int, y: int) -> int:
    """Example task: Add two numbers."""
    return x + y


@celery_app.task(name=f"{settings.CELERY_TASKS_MODULE}.send_email")
def send_email(to: str, subject: str, body: str) -> dict:
    """Example task: Send email (mock implementation)."""
    # Add your email sending logic here
    return {"to": to, "subject": subject, "body": body, "status": "sent"}
