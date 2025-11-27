"""Docling conversion schemas."""

from enum import Enum

from pydantic import BaseModel, Field


class ConversionMode(str, Enum):
    """Document conversion mode."""

    LOCAL = "local"
    REMOTE = "remote"


class ConversionResult(BaseModel):
    """Result of document conversion."""

    success: bool
    markdown: str | None = Field(default=None, description="Converted markdown content")
    error: str | None = None
    filename: str | None = None
    mode: ConversionMode | None = None
