"""Markdown to PDF conversion service."""

from pathlib import Path
from typing import Annotated

from app.lib.document_processing.markdown_to_pdf.factory import (
    get_markdown_to_pdf_converter,
)
from app.lib.document_processing.markdown_to_pdf.schemas.dto import (
    MarkdownToPdfOptions,
    MarkdownToPdfProvider,
    MarkdownToPdfResult,
)


class MarkdownToPdfService:
    """Service for converting markdown to PDF."""

    def __init__(
        self,
        default_provider: Annotated[
            MarkdownToPdfProvider, "Default conversion provider"
        ] = MarkdownToPdfProvider.WEASYPRINT,
    ) -> None:
        self._default_provider = default_provider

    def convert_from_string(
        self,
        markdown: Annotated[str, "Markdown content to convert"],
        provider: Annotated[MarkdownToPdfProvider | None, "Provider override"] = None,
        options: Annotated[MarkdownToPdfOptions | None, "Conversion options"] = None,
    ) -> MarkdownToPdfResult:
        """Convert markdown string to PDF bytes."""
        converter = get_markdown_to_pdf_converter(provider or self._default_provider)
        return converter.convert(markdown, options)

    def convert_from_file(
        self,
        path: Annotated[str | Path, "Path to markdown file"],
        provider: Annotated[MarkdownToPdfProvider | None, "Provider override"] = None,
        options: Annotated[MarkdownToPdfOptions | None, "Conversion options"] = None,
    ) -> MarkdownToPdfResult:
        """Convert markdown file to PDF bytes."""
        file_path = Path(path)
        if not file_path.exists():
            return MarkdownToPdfResult(
                success=False, message=f"File not found: {file_path}"
            )

        try:
            markdown = file_path.read_text()
        except Exception as e:
            return MarkdownToPdfResult(success=False, message=f"Read error: {e}")

        return self.convert_from_string(markdown, provider, options)

    def save_pdf(
        self,
        result: Annotated[MarkdownToPdfResult, "Conversion result"],
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
