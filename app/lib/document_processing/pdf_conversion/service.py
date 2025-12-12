"""PDF conversion service."""

from pathlib import Path
from typing import Annotated

from app.lib.document_processing.pdf_conversion.factory import get_pdf_converter
from app.lib.document_processing.pdf_conversion.schemas.dto import (
    PdfConversionOptions,
    PdfConversionProvider,
    PdfConversionResult,
)


class PdfConversionService:
    """Service for PDF conversion from markdown."""

    def __init__(
        self,
        default_provider: Annotated[
            PdfConversionProvider, "Default conversion provider"
        ] = PdfConversionProvider.WEASYPRINT,
    ) -> None:
        self._default_provider = default_provider

    def convert_from_markdown(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        provider: Annotated[PdfConversionProvider | None, "Provider override"] = None,
        options: Annotated[PdfConversionOptions | None, "Conversion options"] = None,
    ) -> PdfConversionResult:
        """Convert markdown string to PDF bytes."""
        converter = get_pdf_converter(provider or self._default_provider)
        return converter.convert_markdown(markdown, options)

    def convert_from_file(
        self,
        path: Annotated[str | Path, "Path to markdown file"],
        provider: Annotated[PdfConversionProvider | None, "Provider override"] = None,
        options: Annotated[PdfConversionOptions | None, "Conversion options"] = None,
    ) -> PdfConversionResult:
        """Convert markdown file to PDF bytes."""
        file_path = Path(path)
        if not file_path.exists():
            return PdfConversionResult(
                success=False, message=f"File not found: {file_path}"
            )

        try:
            markdown = file_path.read_text()
        except Exception as e:
            return PdfConversionResult(success=False, message=f"Read error: {e}")

        return self.convert_from_markdown(markdown, provider, options)

    def save_pdf(
        self,
        result: Annotated[PdfConversionResult, "Conversion result"],
        output_path: Annotated[str | Path, "Output PDF path"],
    ) -> bool:
        """Save PDF bytes to file. Returns True on success."""
        if not result.success or not result.content:
            return False

        try:
            Path(output_path).write_bytes(result.content)
            return True
        except Exception:
            return False
