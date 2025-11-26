"""Salesforce integration for Content Library operations."""

from fastapi import APIRouter

from .client import SalesforceClient
from .dependencies import SalesforceClientDep, get_salesforce_client
from .schemas import FileResponse, LibraryFilesResponse, LibraryResponse
from .types import ContentVersion, ContentWorkspace, FileInfo

__all__ = [
    "SalesforceClient",
    "SalesforceClientDep",
    "get_salesforce_client",
    "ContentVersion",
    "ContentWorkspace",
    "FileInfo",
    "FileResponse",
    "LibraryFilesResponse",
    "LibraryResponse",
]


def setup_api(integration_router: APIRouter) -> None:
    """Setup Salesforce API endpoints."""
    from . import api

    integration_router.include_router(api.router)
