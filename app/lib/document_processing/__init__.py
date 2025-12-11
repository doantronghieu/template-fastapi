"""Document processing library with pluggable provider support.

Provides unified interfaces for document processing operations:
- Text extraction (via TextExtractionService)
- Future: conversion, OCR, metadata extraction, etc.
"""

from app.lib.document_processing.base import TextExtractor
from app.lib.document_processing.dependencies import (
    TextExtractionServiceDep,
    TextExtractorDep,
    get_text_extraction_service_dependency,
    get_text_extractor_dependency,
)
from app.lib.document_processing.factory import get_text_extractor
from app.lib.document_processing.schemas.dto import (
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
from app.lib.document_processing.service import TextExtractionService

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
]
