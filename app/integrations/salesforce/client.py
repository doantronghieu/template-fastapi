"""Salesforce API client.

Low-level wrapper around simple-salesforce for API communication.
"""

import logging

import requests
from simple_salesforce import Salesforce

logger = logging.getLogger(__name__)


class SalesforceClient:
    """Low-level Salesforce API client."""

    def __init__(
        self,
        consumer_key: str,
        consumer_secret: str,
        domain: str,
        username: str | None = None,
        password: str | None = None,
    ):
        """Initialize Salesforce client.

        Uses Client Credentials Flow (recommended) if only consumer_key/secret provided.
        Falls back to Username-Password Flow if username/password also provided.
        """
        if username and password:
            self.sf = Salesforce(
                username=username,
                password=password,
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                domain=domain,
            )
        else:
            self.sf = Salesforce(
                consumer_key=consumer_key,
                consumer_secret=consumer_secret,
                domain=domain,
            )
        self.base_url = f"https://{self.sf.sf_instance}"
        self.session_id = self.sf.session_id

    def query(self, soql: str) -> dict:
        """Execute SOQL query."""
        return self.sf.query(soql)

    def query_all(self, soql: str) -> dict:
        """Execute SOQL query with pagination."""
        return self.sf.query_all(soql)

    def get(self, path: str) -> requests.Response:
        """Make authenticated GET request."""
        headers = {"Authorization": f"Bearer {self.session_id}"}
        return requests.get(f"{self.base_url}{path}", headers=headers)
