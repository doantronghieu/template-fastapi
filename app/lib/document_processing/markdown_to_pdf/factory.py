"""Markdown to PDF converter factory."""

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from app.lib.document_processing.markdown_to_pdf.schemas.dto import (
    MarkdownToPdfProvider,
)

if TYPE_CHECKING:
    from app.lib.document_processing.markdown_to_pdf.base import MarkdownToPdfConverter


@lru_cache(maxsize=1)
def get_markdown_to_pdf_converter(
    provider: Annotated[
        MarkdownToPdfProvider, "Provider to use"
    ] = MarkdownToPdfProvider.WEASYPRINT,
) -> "MarkdownToPdfConverter":
    """Get cached markdown to PDF converter instance for provider."""
    providers = {
        MarkdownToPdfProvider.WEASYPRINT: _get_weasyprint_converter,
    }
    return providers[provider]()


def _get_weasyprint_converter() -> "MarkdownToPdfConverter":
    """Get WeasyPrint markdown to PDF converter."""
    from app.lib.document_processing.markdown_to_pdf.providers.weasyprint import (
        WeasyPrintMarkdownToPdfConverter,
    )

    return WeasyPrintMarkdownToPdfConverter()
