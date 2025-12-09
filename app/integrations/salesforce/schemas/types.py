"""TypedDict definitions for Salesforce API structures."""

from typing import Annotated, TypedDict


class ContentWorkspace(TypedDict):
    """Salesforce Content Library (ContentWorkspace object)."""

    Id: Annotated[str, "Salesforce record ID"]
    Name: Annotated[str, "Library display name"]
    Description: Annotated[str | None, "Library description"]


class ContentVersion(TypedDict):
    """Salesforce file version with download URL."""

    Id: Annotated[str, "ContentVersion record ID"]
    Title: Annotated[str, "File title without extension"]
    VersionData: Annotated[str, "Relative URL path to download binary"]
    FileExtension: Annotated[str | None, "File extension (e.g., 'pdf')"]
    ContentDocumentId: Annotated[str, "Parent ContentDocument ID"]


class FileInfo(TypedDict):
    """Processed file metadata for API responses."""

    content_document_id: Annotated[str, "ContentDocument record ID"]
    title: Annotated[str, "File title (may include extension)"]
    file_extension: Annotated[str | None, "File extension (e.g., 'pdf')"]
    content_size: Annotated[int | None, "File size in bytes"]
    created_date: Annotated[str, "ISO 8601 creation timestamp"]
    latest_version_id: Annotated[str | None, "Latest ContentVersion ID for download"]
