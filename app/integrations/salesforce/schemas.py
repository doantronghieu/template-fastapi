"""Pydantic schemas for Salesforce API endpoints."""

from pydantic import BaseModel, Field


class LibraryResponse(BaseModel):
    """Content Library metadata."""

    id: str = Field(alias="Id", description="Salesforce record ID")
    name: str = Field(alias="Name", description="Library display name")
    description: str | None = Field(default=None, alias="Description")

    model_config = {"populate_by_name": True}


class FileResponse(BaseModel):
    """File metadata from Content Library."""

    content_document_id: str = Field(description="ContentDocument record ID")
    title: str = Field(description="File title (may include extension)")
    file_extension: str | None = Field(default=None, description="e.g., 'pdf'")
    content_size: int | None = Field(default=None, description="File size in bytes")
    created_date: str = Field(description="ISO 8601 creation timestamp")
    latest_version_id: str | None = Field(
        default=None, description="ContentVersion ID for download"
    )


class LibraryFilesResponse(BaseModel):
    """Response for listing files in a library."""

    library_name: str = Field(description="Content Library name")
    total_files: int = Field(description="Number of files in library")
    files: list[FileResponse] = Field(description="File metadata list")
