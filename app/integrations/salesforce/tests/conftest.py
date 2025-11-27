"""Pytest fixtures for Salesforce integration tests."""

import pytest

from app.integrations.salesforce.config import salesforce_settings
from app.integrations.salesforce.client import SalesforceClient
from app.integrations.salesforce.services.crud_service import CRUDService


def _get_salesforce_credentials() -> dict | None:
    """Get Salesforce credentials from settings."""
    try:
        consumer_key = salesforce_settings.SALESFORCE_CONSUMER_KEY
        consumer_secret = salesforce_settings.SALESFORCE_CONSUMER_SECRET
        domain = salesforce_settings.SALESFORCE_DOMAIN
    except Exception:
        return None

    if not all([consumer_key, consumer_secret, domain]):
        return None

    username = getattr(salesforce_settings, "SALESFORCE_USERNAME", None)
    password = getattr(salesforce_settings, "SALESFORCE_PASSWORD", None)

    return {
        "consumer_key": consumer_key,
        "consumer_secret": consumer_secret,
        "domain": domain,
        "username": username if username else None,
        "password": password if password else None,
    }


@pytest.fixture(scope="module")
def salesforce_client() -> SalesforceClient:
    """Provide real SalesforceClient for integration tests.

    Skips tests if credentials are not configured.
    """
    creds = _get_salesforce_credentials()
    if not creds:
        pytest.skip("Salesforce credentials not configured")

    return SalesforceClient(
        consumer_key=creds["consumer_key"],
        consumer_secret=creds["consumer_secret"],
        domain=creds["domain"],
        username=creds["username"],
        password=creds["password"],
    )


@pytest.fixture(scope="module")
def crud_service(salesforce_client: SalesforceClient) -> CRUDService:
    """Provide CRUDService with real Salesforce client."""
    return CRUDService(client=salesforce_client)
