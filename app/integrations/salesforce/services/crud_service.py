"""Generic CRUD service for Salesforce objects."""

import logging
from typing import Annotated

from fastapi import Depends
from simple_salesforce.exceptions import SalesforceError as SFError

from ..client import SalesforceClient
from ..dependencies import SalesforceClientDep
from ..exceptions import (
    SalesforceError,
    SalesforcePermissionError,
    SalesforceRecordNotFound,
    SalesforceSessionExpired,
    SalesforceValidationError,
)

logger = logging.getLogger(__name__)


class CRUDService:
    """Generic CRUD operations for any Salesforce object."""

    def __init__(self, client: SalesforceClient):
        self.client = client

    def _handle_error(
        self, e: SFError, object_type: str, record_id: str | None = None
    ) -> None:
        """Translate simple-salesforce exceptions to custom exceptions."""
        status = getattr(e, "status", None)
        content = getattr(e, "content", str(e))

        if status == 404:
            raise SalesforceRecordNotFound(object_type, record_id or "unknown")
        elif status == 400:
            raise SalesforceValidationError(str(content))
        elif status == 401:
            raise SalesforceSessionExpired()
        elif status == 403:
            raise SalesforcePermissionError(str(content))
        else:
            raise SalesforceError(str(content), status_code=status)

    def _get_sobject(self, object_type: str):
        """Get SObject accessor for the given type."""
        return getattr(self.client.sf, object_type)

    def create(self, object_type: str, data: dict) -> str:
        """Create a record and return its ID."""
        try:
            result = self._get_sobject(object_type).create(data)
            if not result.get("success"):
                raise SalesforceValidationError(
                    f"Failed to create {object_type}",
                    errors=result.get("errors", []),
                )
            logger.info(f"Created {object_type}: {result['id']}")
            return result["id"]
        except SFError as e:
            logger.error(f"Create {object_type} failed: {e}")
            self._handle_error(e, object_type)

    def get(self, object_type: str, record_id: str) -> dict:
        """Get a record by ID."""
        try:
            return self._get_sobject(object_type).get(record_id)
        except SFError as e:
            logger.error(f"Get {object_type}/{record_id} failed: {e}")
            self._handle_error(e, object_type, record_id)

    def update(self, object_type: str, record_id: str, data: dict) -> bool:
        """Update a record. Returns True on success."""
        try:
            status = self._get_sobject(object_type).update(record_id, data)
            if status == 204:
                logger.info(f"Updated {object_type}: {record_id}")
            return status == 204
        except SFError as e:
            logger.error(f"Update {object_type}/{record_id} failed: {e}")
            self._handle_error(e, object_type, record_id)

    def delete(self, object_type: str, record_id: str) -> bool:
        """Delete a record. Returns True on success."""
        try:
            status = self._get_sobject(object_type).delete(record_id)
            if status == 204:
                logger.info(f"Deleted {object_type}: {record_id}")
            return status == 204
        except SFError as e:
            logger.error(f"Delete {object_type}/{record_id} failed: {e}")
            self._handle_error(e, object_type, record_id)

    def query(self, soql: str) -> list[dict]:
        """Execute SOQL query and return records."""
        try:
            result = self.client.query(soql)
            return result.get("records", [])
        except SFError as e:
            logger.error(f"Query failed: {e}")
            self._handle_error(e, "Query")


def get_crud_service(client: SalesforceClientDep) -> CRUDService:
    """Provide CRUDService instance with injected client."""
    return CRUDService(client=client)


CRUDServiceDep = Annotated[CRUDService, Depends(get_crud_service)]
