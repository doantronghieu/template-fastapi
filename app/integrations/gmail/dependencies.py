"""Dependency injection providers for Gmail integration."""

import logging
import os
from typing import Annotated

from fastapi import Depends, HTTPException, status

from .client import GmailClient

logger = logging.getLogger(__name__)

# Load Gmail credentials from environment (loaded by main.py via python-dotenv)
_gmail_credentials_checked = False


def get_gmail_client() -> GmailClient:
    """Provide GmailClient instance with credentials from environment variables.

    Loads credentials directly from environment (GMAIL_EMAIL, GMAIL_APP_PASSWORD).
    These are loaded into os.environ by python-dotenv in app/main.py.

    Returns:
        Configured GmailClient for IMAP operations

    Raises:
        HTTPException: If Gmail credentials are not configured
    """
    global _gmail_credentials_checked

    gmail_email = os.getenv("GMAIL_EMAIL")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")

    if not gmail_email or not gmail_password:
        # Log warning only once
        if not _gmail_credentials_checked:
            logger.warning(
                "Gmail credentials not configured. Gmail integration endpoints will be unavailable. "
                "Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in .env to enable."
            )
            _gmail_credentials_checked = True

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Gmail integration not configured. Set GMAIL_EMAIL and GMAIL_APP_PASSWORD in environment.",
        )

    _gmail_credentials_checked = True
    return GmailClient(email=gmail_email, app_password=gmail_password)


GmailClientDep = Annotated[GmailClient, Depends(get_gmail_client)]
