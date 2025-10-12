"""Dependency injection providers for Messenger client."""

from typing import Annotated

from fastapi import Depends

from app.core.config import settings

from .client import MessengerClient


def get_messenger_client() -> MessengerClient:
    """
    Provide MessengerClient instance configured from environment settings.

    Returns:
        MessengerClient: Initialized client with credentials from .env
    """
    return MessengerClient(
        page_access_token=settings.FACEBOOK_PAGE_ACCESS_TOKEN,
        app_secret=settings.FACEBOOK_APP_SECRET,
        graph_api_version=settings.FACEBOOK_GRAPH_API_VERSION,
    )


# Type alias for cleaner endpoint signatures
MessengerClientDep = Annotated[MessengerClient, Depends(get_messenger_client)]
