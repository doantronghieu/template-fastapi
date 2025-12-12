"""Text extraction data transfer objects."""

from enum import Enum
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field


# --- Document Source Types ---


class DocumentSource(BaseModel):
    """Base class for document sources."""

    @staticmethod
    def from_path(
        path: Annotated[str | Path, "File path to document"],
    ) -> "PathDocumentSource":
        """Create source from file path."""
        return PathDocumentSource(path=Path(path))

    @staticmethod
    def from_bytes(
        content: Annotated[bytes, "Raw file content"],
        filename: Annotated[str, "Original filename"],
    ) -> "BytesDocumentSource":
        """Create source from bytes content."""
        return BytesDocumentSource(content=content, filename=filename)

    @staticmethod
    def from_url(
        url: Annotated[str, "Document URL"],
    ) -> "UrlDocumentSource":
        """Create source from URL."""
        return UrlDocumentSource(url=url)


class PathDocumentSource(DocumentSource):
    """Document source from file path."""

    path: Annotated[Path, "Path to document file"]


class BytesDocumentSource(DocumentSource):
    """Document source from bytes content."""

    content: Annotated[bytes, "Raw file content"]
    filename: Annotated[str, "Original filename for type detection"]


class UrlDocumentSource(DocumentSource):
    """Document source from URL."""

    url: Annotated[str, "URL to document"]


# --- Text Extraction Types ---


class TextExtractionProvider(str, Enum):
    """Text extraction provider type."""

    DOCLING = "docling"
    MISTRAL = "mistral"


class DoclingTextExtractionMode(str, Enum):
    """Docling-specific extraction mode."""

    LOCAL = "local"
    REMOTE = "remote"


class TextExtractionOptions(BaseModel):
    """Base class for text extraction options."""

    pass


class DoclingTextExtractionOptions(TextExtractionOptions):
    """Docling-specific text extraction options."""

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


class MistralTextExtractionOptions(TextExtractionOptions):
    """Mistral-specific text extraction options."""

    include_image_base64: Annotated[
        bool,
        Field(default=False, description="Include base64 images in response"),
    ]


class TextExtractionResult(BaseModel):
    """Result of text extraction operation."""

    success: Annotated[bool, Field(description="Whether extraction succeeded")]
    result: Annotated[
        str | None,
        Field(default=None, description="Extracted markdown content"),
    ]
    message: Annotated[
        str | None,
        Field(default=None, description="Error or status message"),
    ]
