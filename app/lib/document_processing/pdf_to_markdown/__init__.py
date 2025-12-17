"""PDF to Markdown conversion with bookmark preservation.

Provides PDF→Markdown conversion using PyMuPDF4LLM with bookmark injection.
Bookmarks are preserved as markdown headers for section-aware processing.
"""

from app.lib.document_processing.pdf_to_markdown.service import (
    convert_pdf_to_markdown,
    extract_bookmarks,
    get_document_sections,
)

__all__ = [
    "convert_pdf_to_markdown",
    "extract_bookmarks",
    "get_document_sections",
]
