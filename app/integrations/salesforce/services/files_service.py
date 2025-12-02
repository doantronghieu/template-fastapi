"""Salesforce files service for Content Library operations."""

import logging
from typing import Annotated

from fastapi import Depends

from ..client import SalesforceClient
from ..dependencies import SalesforceClientDep
from ..types import ContentVersion, FileInfo

logger = logging.getLogger(__name__)


class FilesService:
    """Service for Salesforce Content Library file operations."""

    def __init__(self, client: SalesforceClient):
        self.client = client

    def _get_library_id(self, library_name: str) -> str | None:
        query = f"SELECT Id FROM ContentWorkspace WHERE Name = '{library_name}'"
        result = self.client.query(query)
        return result["records"][0]["Id"] if result["records"] else None

    def _get_content_version(self, version_id: str) -> ContentVersion | None:
        query = f"""
            SELECT Id, Title, VersionData, FileExtension, ContentDocumentId
            FROM ContentVersion WHERE Id = '{version_id}'
        """
        result = self.client.query(query)
        return result["records"][0] if result["records"] else None

    def _build_filename(self, title: str, ext: str | None) -> str:
        if ext and not title.lower().endswith(f".{ext.lower()}"):
            return f"{title}.{ext}"
        return title

    def list_files_in_library(
        self, library_name: Annotated[str, "Content Library name"]
    ) -> list[FileInfo]:
        """List all files in a Content Library."""
        library_id = self._get_library_id(library_name)
        if not library_id:
            logger.warning(f"Library not found: {library_name}")
            return []

        query = f"""
            SELECT ContentDocumentId, ContentDocument.Title,
                   ContentDocument.FileExtension, ContentDocument.ContentSize,
                   ContentDocument.CreatedDate, ContentDocument.LatestPublishedVersionId
            FROM ContentWorkspaceDoc
            WHERE ContentWorkspaceId = '{library_id}'
        """
        result = self.client.query(query)

        return [
            FileInfo(
                content_document_id=record["ContentDocumentId"],
                title=record["ContentDocument"]["Title"],
                file_extension=record["ContentDocument"].get("FileExtension"),
                content_size=record["ContentDocument"].get("ContentSize"),
                created_date=record["ContentDocument"]["CreatedDate"],
                latest_version_id=record["ContentDocument"].get(
                    "LatestPublishedVersionId"
                ),
            )
            for record in result["records"]
        ]

    def download_by_name(
        self,
        library_name: Annotated[str, "Content Library name"],
        file_name: Annotated[str, "File title to match"],
    ) -> tuple[bytes, str] | None:
        """Download file by library and file name."""
        files = self.list_files_in_library(library_name)
        target = next((f for f in files if f["title"] == file_name), None)
        if not target or not target.get("latest_version_id"):
            return None

        version = self._get_content_version(target["latest_version_id"])
        if not version:
            return None

        response = self.client.get(version["VersionData"])
        if response.status_code != 200:
            logger.error(f"Download failed: {response.status_code}")
            return None

        filename = self._build_filename(version["Title"], version.get("FileExtension"))
        return response.content, filename


def get_files_service(client: SalesforceClientDep) -> FilesService:
    """Provide FilesService instance with injected client."""
    return FilesService(client=client)


FilesServiceDep = Annotated[FilesService, Depends(get_files_service)]
