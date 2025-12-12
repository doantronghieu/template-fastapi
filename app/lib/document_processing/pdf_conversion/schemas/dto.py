"""PDF conversion data transfer objects."""

from enum import Enum

from pydantic import BaseModel, Field


class PdfConversionProvider(str, Enum):
    """PDF conversion provider type."""

    WEASYPRINT = "weasyprint"


class PdfConversionOptions(BaseModel):
    """Options for PDF conversion."""

    css: str | None = Field(default=None, description="Custom CSS string for styling")
    base_url: str | None = Field(
        default=None, description="Base URL for relative URLs in content"
    )


class PdfConversionResult(BaseModel):
    """Result of PDF conversion operation."""

    success: bool = Field(description="Whether conversion succeeded")
    content: bytes | None = Field(default=None, description="PDF bytes")
    message: str | None = Field(default=None, description="Error or status message")
