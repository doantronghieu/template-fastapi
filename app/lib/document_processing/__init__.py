"""Document processing library with pluggable provider support.

Provides a unified interface for text extraction from documents.
"""

from app.lib.document_processing.base import TextExtractor
from app.lib.document_processing.dependencies import (
    TextExtractorDep,
    get_text_extractor_dep,
)
from app.lib.document_processing.factory import get_text_extractor
from app.lib.document_processing.schemas.dto import (
    BytesTextSource,
    DoclingOptions,
    DoclingTextExtractionMode,
    MistralOptions,
    PathTextSource,
    ProviderType,
    TextExtractionOptions,
    TextExtractionResult,
    TextSource,
    UrlTextSource,
)

__all__ = [
    # ABC
    "TextExtractor",
    # Source types
    "TextSource",
    "PathTextSource",
    "BytesTextSource",
    "UrlTextSource",
    # Options
    "TextExtractionOptions",
    "DoclingOptions",
    "MistralOptions",
    "DoclingTextExtractionMode",
    # Result
    "TextExtractionResult",
    # Enums
    "ProviderType",
    # Factory
    "get_text_extractor",
    # Dependencies
    "get_text_extractor_dep",
    "TextExtractorDep",
]
