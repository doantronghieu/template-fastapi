"""Document conversion schemas.

Shared schemas used across all document converter implementations.
"""

from enum import Enum

from pydantic import BaseModel, Field


class ConversionMode(str, Enum):
    """Document conversion mode."""

    LOCAL = "local"
    REMOTE = "remote"


class ConversionResult(BaseModel):
    """Result of document conversion."""

    success: bool = Field(description="Whether conversion succeeded")
    markdown: str | None = Field(
        default=None, description="Converted markdown content"
    )
    error: str | None = Field(default=None, description="Error message if failed")
    filename: str | None = Field(default=None, description="Original filename")
    mode: ConversionMode | None = Field(default=None, description="Conversion mode used")
