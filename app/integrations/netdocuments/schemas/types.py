"""TypedDict definitions for NetDocuments API structures."""

from typing import Annotated, TypedDict


class DownloadResult(TypedDict):
    """Result of a document download operation."""

    success: Annotated[bool, "Whether download succeeded"]
    file_path: Annotated[str | None, "Local path where file was saved"]
    doc_id: Annotated[str | None, "NetDocuments document ID"]
    filename: Annotated[str | None, "Downloaded filename"]
    file_size: Annotated[int | None, "File size in bytes"]
    error: Annotated[str | None, "Error message if failed"]


class UploadResult(TypedDict):
    """Result of a document upload operation."""

    success: Annotated[bool, "Whether upload succeeded"]
    doc_id: Annotated[str | None, "NetDocuments document ID"]
    filename: Annotated[str | None, "Uploaded filename"]
    file_size: Annotated[int | None, "File size in bytes"]
    is_new_version: Annotated[bool, "True if created new version of existing doc"]
    version_number: Annotated[int | None, "Version number if new version created"]
    error: Annotated[str | None, "Error message if failed"]
