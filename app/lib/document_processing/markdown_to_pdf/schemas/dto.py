"""Markdown to PDF conversion data transfer objects."""

from enum import Enum

from pydantic import BaseModel, Field


class MarkdownToPdfProvider(str, Enum):
    """Markdown to PDF conversion provider type."""

    WEASYPRINT = "weasyprint"


class MarkdownToPdfOptions(BaseModel):
    """Options for markdown to PDF conversion."""

    css: str | None = Field(default=None, description="Custom CSS string for styling")
    base_url: str | None = Field(
        default=None, description="Base URL for relative URLs in content"
    )
    html_template: str | None = Field(
        default=None,
        description="Custom HTML template with {content} placeholder for markdown",
    )


class MarkdownToPdfResult(BaseModel):
    """Result of markdown to PDF conversion operation."""

    success: bool = Field(description="Whether conversion succeeded")
    content: bytes | None = Field(default=None, description="PDF bytes")
    message: str | None = Field(default=None, description="Error or status message")
