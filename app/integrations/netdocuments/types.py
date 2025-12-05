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


class NetDocSearchResult(TypedDict):
    """Search result from NetDocuments API."""

    id: Annotated[str, "Document ID"]
    name: Annotated[str, "Document name"]
    extension: Annotated[str | None, "File extension"]
    version: Annotated[int, "Document version number"]
    size: Annotated[int | None, "File size in bytes"]
    modified: Annotated[str | None, "Last modified date"]
