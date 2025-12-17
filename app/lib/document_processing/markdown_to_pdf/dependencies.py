"""Markdown to PDF dependency injection."""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.document_processing.markdown_to_pdf.base import MarkdownToPdfConverter
    from app.lib.document_processing.markdown_to_pdf.service import MarkdownToPdfService


def get_markdown_to_pdf_converter_dependency() -> "MarkdownToPdfConverter":
    """Get markdown to PDF converter for dependency injection."""
    from app.lib.document_processing.markdown_to_pdf.factory import (
        get_markdown_to_pdf_converter,
    )

    return get_markdown_to_pdf_converter()


def get_markdown_to_pdf_service_dependency() -> "MarkdownToPdfService":
    """Get markdown to PDF service for dependency injection."""
    from app.lib.document_processing.markdown_to_pdf.service import MarkdownToPdfService

    return MarkdownToPdfService()


MarkdownToPdfConverterDep = Annotated[
    "MarkdownToPdfConverter", Depends(get_markdown_to_pdf_converter_dependency)
]
MarkdownToPdfServiceDep = Annotated[
    "MarkdownToPdfService", Depends(get_markdown_to_pdf_service_dependency)
]
