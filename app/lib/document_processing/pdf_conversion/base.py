"""PDF converter base class."""

from abc import ABC, abstractmethod
from typing import Annotated

from app.lib.document_processing.pdf_conversion.schemas.dto import (
    PdfConversionOptions,
    PdfConversionResult,
)


class PdfConverter(ABC):
    """Abstract base class for PDF conversion from markdown."""

    @abstractmethod
    def convert_markdown(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        options: Annotated[
            PdfConversionOptions | None, "Conversion options"
        ] = None,
    ) -> PdfConversionResult:
        """Convert markdown string to PDF bytes."""
        ...
