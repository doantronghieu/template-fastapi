"""Dependency injection providers for Gmail integration."""

from typing import Annotated

from fastapi import Depends

from .client import GmailClient
from .config import gmail_settings


def get_gmail_client() -> GmailClient:
    """Provide GmailClient instance with credentials

    Returns:
        Configured GmailClient for IMAP operations
    """
    return GmailClient(
        email=gmail_settings.GMAIL_EMAIL,
        app_password=gmail_settings.GMAIL_APP_PASSWORD,
    )


GmailClientDep = Annotated[GmailClient, Depends(get_gmail_client)]
