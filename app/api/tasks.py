"""Task management endpoints."""

from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter
from pydantic import BaseModel

from app.core.celery import celery_app
from app.tasks.example_tasks import add_numbers, send_email

router = APIRouter()


class AddNumbersRequest(BaseModel):
    x: int
    y: int


class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str


class TaskResponse(BaseModel):
    task_id: str
    status: str


class TaskResultResponse(BaseModel):
    task_id: str
    status: str
    result: Any | None


@router.post("/add", response_model=TaskResponse)
def trigger_add_numbers(request: AddNumbersRequest) -> TaskResponse:
    """Trigger add_numbers task."""
    task = add_numbers.delay(request.x, request.y)  # type: ignore[attr-defined]
    return TaskResponse(task_id=task.id, status="queued")


@router.post("/email", response_model=TaskResponse)
def trigger_send_email(request: SendEmailRequest) -> TaskResponse:
    """Trigger send_email task."""
    task = send_email.delay(request.to, request.subject, request.body)  # type: ignore[attr-defined]
    return TaskResponse(task_id=task.id, status="queued")


@router.get("/result/{task_id}", response_model=TaskResultResponse)
def get_task_result(task_id: str) -> TaskResultResponse:
    """Get task result by ID."""
    result = AsyncResult(task_id, app=celery_app)
    return TaskResultResponse(
        task_id=task_id,
        status=result.state,
        result=result.result if result.ready() else None,
    )
