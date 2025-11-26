"""Dependency injection providers for Messenger client."""

from typing import Annotated

from fastapi import Depends

from .client import MessengerClient
from .config import messenger_settings


def get_messenger_client() -> MessengerClient:
    """
    Provide MessengerClient instance

    Returns:
        MessengerClient: Initialized client with credentials from messenger settings
    """
    return MessengerClient(
        page_access_token=messenger_settings.FACEBOOK_PAGE_ACCESS_TOKEN,
        app_secret=messenger_settings.FACEBOOK_APP_SECRET,
        graph_api_version=messenger_settings.FACEBOOK_GRAPH_API_VERSION,
    )


# Type alias for cleaner endpoint signatures
MessengerClientDep = Annotated[MessengerClient, Depends(get_messenger_client)]
