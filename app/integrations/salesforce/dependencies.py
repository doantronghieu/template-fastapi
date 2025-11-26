"""Dependency injection providers for Salesforce integration."""

from typing import Annotated

from fastapi import Depends

from .client import SalesforceClient
from .config import salesforce_settings


def get_salesforce_client() -> SalesforceClient:
    """Provide SalesforceClient instance with credentials.

    Uses Client Credentials Flow by default (no username/password).
    Set SALESFORCE_USERNAME and SALESFORCE_PASSWORD to use legacy flow.
    """
    username = getattr(salesforce_settings, "SALESFORCE_USERNAME", None)
    password = getattr(salesforce_settings, "SALESFORCE_PASSWORD", None)

    # Use empty strings as None for Client Credentials Flow
    if username == "" or password == "":
        username = None
        password = None

    return SalesforceClient(
        consumer_key=salesforce_settings.SALESFORCE_CONSUMER_KEY,
        consumer_secret=salesforce_settings.SALESFORCE_CONSUMER_SECRET,
        domain=salesforce_settings.SALESFORCE_DOMAIN,
        username=username,
        password=password,
    )


SalesforceClientDep = Annotated[SalesforceClient, Depends(get_salesforce_client)]
