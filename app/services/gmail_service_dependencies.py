"""Dependency injection for Gmail service."""

from typing import Annotated

from fastapi import Depends

from app.integrations.gmail import GmailClientDep

from .gmail_service import GmailService


def get_gmail_service(client: GmailClientDep) -> GmailService:
    """Provide GmailService instance with injected client.

    Args:
        client: GmailClient from dependency injection

    Returns:
        Configured GmailService instance
    """
    return GmailService(client=client)


GmailServiceDep = Annotated[GmailService, Depends(get_gmail_service)]
