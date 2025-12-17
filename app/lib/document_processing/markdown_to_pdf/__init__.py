"""Markdown to PDF conversion module.

Provides markdown-to-PDF conversion using WeasyPrint + markdown-it-py.
"""

from app.lib.document_processing.markdown_to_pdf.base import MarkdownToPdfConverter
from app.lib.document_processing.markdown_to_pdf.dependencies import (
    MarkdownToPdfConverterDep,
    MarkdownToPdfServiceDep,
    get_markdown_to_pdf_converter_dependency,
    get_markdown_to_pdf_service_dependency,
)
from app.lib.document_processing.markdown_to_pdf.factory import (
    get_markdown_to_pdf_converter,
)
from app.lib.document_processing.markdown_to_pdf.schemas.dto import (
    MarkdownToPdfOptions,
    MarkdownToPdfProvider,
    MarkdownToPdfResult,
)
from app.lib.document_processing.markdown_to_pdf.service import MarkdownToPdfService

__all__ = [
    # ABC
    "MarkdownToPdfConverter",
    # Service
    "MarkdownToPdfService",
    # Schemas
    "MarkdownToPdfOptions",
    "MarkdownToPdfProvider",
    "MarkdownToPdfResult",
    # Factory
    "get_markdown_to_pdf_converter",
    # Dependencies
    "get_markdown_to_pdf_converter_dependency",
    "get_markdown_to_pdf_service_dependency",
    "MarkdownToPdfConverterDep",
    "MarkdownToPdfServiceDep",
]
