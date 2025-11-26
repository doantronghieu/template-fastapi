"""Salesforce libraries service for Content Workspace operations."""

from typing import Annotated

from fastapi import Depends

from ..client import SalesforceClient
from ..dependencies import SalesforceClientDep
from ..types import ContentWorkspace


class LibrariesService:
    """Service for Salesforce Content Library operations."""

    def __init__(self, client: SalesforceClient):
        self.client = client

    def list_libraries(self) -> list[ContentWorkspace]:
        """List all Content Libraries."""
        query = "SELECT Id, Name, Description FROM ContentWorkspace ORDER BY Name"
        result = self.client.query(query)
        return result["records"]


def get_libraries_service(client: SalesforceClientDep) -> LibrariesService:
    return LibrariesService(client=client)


LibrariesServiceDep = Annotated[LibrariesService, Depends(get_libraries_service)]
