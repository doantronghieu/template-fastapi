"""Base protocol for document converter implementations.

Defines the common interface that all document converters must implement,
enabling runtime provider switching via the Strategy pattern.
"""

from pathlib import Path
from typing import Annotated, Protocol

from app.lib.documentation.schemas import ConversionMode, ConversionResult


class DocumentConverter(Protocol):
    """Protocol defining the interface for document converter implementations.

    All document converter implementations must support:
    - File path-based conversion
    - Bytes-based conversion for uploaded files
    """

    def convert_from_path(
        self,
        file_path: Annotated[str | Path, "Path to the document file"],
        mode: Annotated[
            ConversionMode, "LOCAL (Tesseract, free) or REMOTE (VLM API, paid)"
        ] = ConversionMode.LOCAL,
        enable_ocr: Annotated[
            bool, "Enable OCR for scanned documents (LOCAL mode only)"
        ] = False,
    ) -> ConversionResult:
        """Convert document from file path to markdown."""
        ...

    def convert_from_bytes(
        self,
        content: Annotated[bytes, "Document file bytes"],
        filename: Annotated[str, "Original filename for format detection"],
        mode: Annotated[
            ConversionMode, "LOCAL (Tesseract, free) or REMOTE (VLM API, paid)"
        ] = ConversionMode.LOCAL,
        enable_ocr: Annotated[
            bool, "Enable OCR for scanned documents (LOCAL mode only)"
        ] = False,
    ) -> ConversionResult:
        """Convert document from bytes to markdown."""
        ...
