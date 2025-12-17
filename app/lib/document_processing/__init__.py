"""Document processing library with pluggable provider support.

Provides unified interfaces for document processing operations:
- Text extraction (via TextExtractionService)
- Markdown to PDF (via MarkdownToPdfService)
- PDF to Markdown - with bookmark preservation (via convert_pdf_to_markdown)
"""

from app.lib.document_processing.markdown_to_pdf import (
    MarkdownToPdfConverter,
    MarkdownToPdfConverterDep,
    MarkdownToPdfOptions,
    MarkdownToPdfProvider,
    MarkdownToPdfResult,
    MarkdownToPdfService,
    MarkdownToPdfServiceDep,
    get_markdown_to_pdf_converter,
    get_markdown_to_pdf_converter_dependency,
    get_markdown_to_pdf_service_dependency,
)
from app.lib.document_processing.pdf_to_markdown import (
    convert_pdf_to_markdown,
    extract_bookmarks,
    get_document_sections,
)
from app.lib.document_processing.text_extraction import (
    BytesDocumentSource,
    DoclingTextExtractionMode,
    DoclingTextExtractionOptions,
    DocumentSource,
    MistralTextExtractionOptions,
    PathDocumentSource,
    TextExtractionOptions,
    TextExtractionProvider,
    TextExtractionResult,
    TextExtractionService,
    TextExtractionServiceDep,
    TextExtractor,
    TextExtractorDep,
    UrlDocumentSource,
    get_text_extraction_service_dependency,
    get_text_extractor,
    get_text_extractor_dependency,
)

__all__ = [
    # Document sources (shared)
    "DocumentSource",
    "PathDocumentSource",
    "BytesDocumentSource",
    "UrlDocumentSource",
    # Text extraction - ABC
    "TextExtractor",
    # Text extraction - Service
    "TextExtractionService",
    # Text extraction - Options
    "TextExtractionOptions",
    "DoclingTextExtractionOptions",
    "DoclingTextExtractionMode",
    "MistralTextExtractionOptions",
    # Text extraction - Result
    "TextExtractionResult",
    # Text extraction - Enums
    "TextExtractionProvider",
    # Text extraction - Factory
    "get_text_extractor",
    # Text extraction - Dependency providers
    "get_text_extractor_dependency",
    "get_text_extraction_service_dependency",
    # Text extraction - Dependency type aliases
    "TextExtractorDep",
    "TextExtractionServiceDep",
    # Markdown to PDF - ABC
    "MarkdownToPdfConverter",
    # Markdown to PDF - Service
    "MarkdownToPdfService",
    # Markdown to PDF - Options
    "MarkdownToPdfOptions",
    # Markdown to PDF - Result
    "MarkdownToPdfResult",
    # Markdown to PDF - Enums
    "MarkdownToPdfProvider",
    # Markdown to PDF - Factory
    "get_markdown_to_pdf_converter",
    # Markdown to PDF - Dependency providers
    "get_markdown_to_pdf_converter_dependency",
    "get_markdown_to_pdf_service_dependency",
    # Markdown to PDF - Dependency type aliases
    "MarkdownToPdfConverterDep",
    "MarkdownToPdfServiceDep",
    # PDF to Markdown - Functions
    "convert_pdf_to_markdown",
    "extract_bookmarks",
    "get_document_sections",
]
