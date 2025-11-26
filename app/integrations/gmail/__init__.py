"""Gmail IMAP integration."""

from fastapi import APIRouter

from .client import GmailClient
from .dependencies import GmailClientDep, get_gmail_client
from .types import EmailAddress, EmailMessage

__all__ = [
    "EmailAddress",
    "EmailMessage",
    "GmailClient",
    "GmailClientDep",
    "get_gmail_client",
]


def setup_api(integration_router: APIRouter) -> None:
    """Setup API endpoints for Gmail integration.

    Args:
        integration_router: Main integration router to attach Gmail endpoints
    """
    from . import api

    integration_router.include_router(
        api.router,
        prefix="/gmail",
        tags=["Gmail Integration"],
    )
