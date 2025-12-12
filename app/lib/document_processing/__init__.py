"""Document processing library with pluggable provider support.

Provides unified interfaces for document processing operations:
- Text extraction (via TextExtractionService)
- PDF conversion (via PdfConversionService)
"""

from app.lib.document_processing.pdf_conversion import (
    PdfConversionOptions,
    PdfConversionProvider,
    PdfConversionResult,
    PdfConversionService,
    PdfConversionServiceDep,
    PdfConverter,
    PdfConverterDep,
    get_pdf_conversion_service_dependency,
    get_pdf_converter,
    get_pdf_converter_dependency,
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
    # PDF conversion - ABC
    "PdfConverter",
    # PDF conversion - Service
    "PdfConversionService",
    # PDF conversion - Options
    "PdfConversionOptions",
    # PDF conversion - Result
    "PdfConversionResult",
    # PDF conversion - Enums
    "PdfConversionProvider",
    # PDF conversion - Factory
    "get_pdf_converter",
    # PDF conversion - Dependency providers
    "get_pdf_converter_dependency",
    "get_pdf_conversion_service_dependency",
    # PDF conversion - Dependency type aliases
    "PdfConverterDep",
    "PdfConversionServiceDep",
]
