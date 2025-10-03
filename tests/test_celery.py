"""Tests for Celery tasks."""

from celery.result import AsyncResult
import pytest

from app.core.celery import celery_app
from app.tasks.example_tasks import add_numbers, send_email


def test_celery_app_configured():
    """Test that Celery app is properly configured."""
    assert celery_app.main == "app"
    assert "app.tasks" in celery_app.conf.include
    assert celery_app.conf.task_serializer == "json"
    assert celery_app.conf.result_serializer == "json"
    assert celery_app.conf.task_acks_late is True


def test_add_numbers_task_registered():
    """Test that add_numbers task is registered."""
    assert "app.tasks.add_numbers" in celery_app.tasks


def test_send_email_task_registered():
    """Test that send_email task is registered."""
    assert "app.tasks.send_email" in celery_app.tasks


def test_add_numbers_sync():
    """Test add_numbers task execution synchronously."""
    result = add_numbers(5, 3)
    assert result == 8


def test_send_email_sync():
    """Test send_email task execution synchronously."""
    result = send_email("test@example.com", "Test Subject", "Test Body")
    assert result["to"] == "test@example.com"
    assert result["subject"] == "Test Subject"
    assert result["body"] == "Test Body"
    assert result["status"] == "sent"


@pytest.mark.integration
def test_add_numbers_async():
    """Test add_numbers task execution asynchronously (requires running worker)."""
    task = add_numbers.delay(10, 20)
    assert isinstance(task, AsyncResult)
    assert task.id is not None


@pytest.mark.integration
def test_send_email_async():
    """Test send_email task execution asynchronously (requires running worker)."""
    task = send_email.delay("async@example.com", "Async Test", "This is async")
    assert isinstance(task, AsyncResult)
    assert task.id is not None
