"""Text extraction module.

Provides text extraction from documents using various providers.
"""

from app.lib.document_processing.text_extraction.base import TextExtractor
from app.lib.document_processing.text_extraction.dependencies import (
    TextExtractionServiceDep,
    TextExtractorDep,
    get_text_extraction_service_dependency,
    get_text_extractor_dependency,
)
from app.lib.document_processing.text_extraction.factory import get_text_extractor
from app.lib.document_processing.text_extraction.schemas.dto import (
    BytesDocumentSource,
    DoclingTextExtractionMode,
    DoclingTextExtractionOptions,
    DocumentSource,
    MistralTextExtractionOptions,
    PathDocumentSource,
    TextExtractionOptions,
    TextExtractionProvider,
    TextExtractionResult,
    UrlDocumentSource,
)
from app.lib.document_processing.text_extraction.service import TextExtractionService

__all__ = [
    # Document sources
    "DocumentSource",
    "PathDocumentSource",
    "BytesDocumentSource",
    "UrlDocumentSource",
    # ABC
    "TextExtractor",
    # Service
    "TextExtractionService",
    # Options
    "TextExtractionOptions",
    "DoclingTextExtractionOptions",
    "DoclingTextExtractionMode",
    "MistralTextExtractionOptions",
    # Result
    "TextExtractionResult",
    # Enums
    "TextExtractionProvider",
    # Factory
    "get_text_extractor",
    # Dependency providers
    "get_text_extractor_dependency",
    "get_text_extraction_service_dependency",
    # Dependency type aliases
    "TextExtractorDep",
    "TextExtractionServiceDep",
]
