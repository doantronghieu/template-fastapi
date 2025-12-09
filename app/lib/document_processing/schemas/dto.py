"""Document processing schemas.

Shared schemas for text extraction from documents.
"""

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Text extraction provider type."""

    DOCLING = "docling"
    MISTRAL = "mistral"


class DoclingTextExtractionMode(str, Enum):
    """Docling-specific extraction mode."""

    LOCAL = "local"
    REMOTE = "remote"


# --- Text Source Types ---


class TextSource(BaseModel):
    """Base class for text extraction sources."""

    @staticmethod
    def from_path(
        path: Annotated[str | Path, "File path to document"],
    ) -> "PathTextSource":
        """Create source from file path."""
        return PathTextSource(path=Path(path))

    @staticmethod
    def from_bytes(
        content: Annotated[bytes, "Raw file content"],
        filename: Annotated[str, "Original filename"],
    ) -> "BytesTextSource":
        """Create source from bytes content."""
        return BytesTextSource(content=content, filename=filename)

    @staticmethod
    def from_url(
        url: Annotated[str, "Document URL"],
    ) -> "UrlTextSource":
        """Create source from URL."""
        return UrlTextSource(url=url)


class PathTextSource(TextSource):
    """Text source from file path."""

    path: Annotated[Path, "Path to document file"]


class BytesTextSource(TextSource):
    """Text source from bytes content."""

    content: Annotated[bytes, "Raw file content"]
    filename: Annotated[str, "Original filename for type detection"]


class UrlTextSource(TextSource):
    """Text source from URL."""

    url: Annotated[str, "URL to document"]


# --- Extraction Options ---


class TextExtractionOptions(BaseModel):
    """Base class for provider-specific extraction options."""

    pass


class DoclingOptions(TextExtractionOptions):
    """Docling-specific extraction options."""

    mode: Annotated[
        DoclingTextExtractionMode,
        Field(
            default=DoclingTextExtractionMode.LOCAL,
            description="Extraction mode (local or remote)",
        ),
    ]
    enable_ocr: Annotated[
        bool,
        Field(default=False, description="Enable OCR for scanned documents"),
    ]


class MistralOptions(TextExtractionOptions):
    """Mistral-specific extraction options."""

    include_image_base64: Annotated[
        bool,
        Field(default=False, description="Include base64 images in response"),
    ]


# --- Extraction Result ---


class TextExtractionResult(BaseModel):
    """Result of text extraction."""

    success: Annotated[bool, Field(description="Whether extraction succeeded")]
    result: Annotated[
        str | None,
        Field(default=None, description="Extracted markdown content"),
    ]
    message: Annotated[
        str | None,
        Field(default=None, description="Error or status message"),
    ]
