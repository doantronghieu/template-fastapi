"""Document processing dependency injection.

FastAPI dependencies for document processing providers and services.
"""

from typing import TYPE_CHECKING, Annotated

from fastapi import Depends, Query

from app.lib.document_processing.schemas.dto import TextExtractionProvider

if TYPE_CHECKING:
    from app.lib.document_processing.base import TextExtractor
    from app.lib.document_processing.service import TextExtractionService


# --- Text Extraction Dependencies ---


def get_text_extractor_dependency(
    provider: Annotated[
        TextExtractionProvider,
        Query(description="Text extraction provider"),
    ] = TextExtractionProvider.DOCLING,
) -> "TextExtractor":
    """Provide text extractor instance for dependency injection."""
    from app.lib.document_processing.factory import get_text_extractor

    return get_text_extractor(provider)


def get_text_extraction_service_dependency(
    provider: Annotated[
        TextExtractionProvider,
        Query(description="Default text extraction provider"),
    ] = TextExtractionProvider.DOCLING,
) -> "TextExtractionService":
    """Provide text extraction service instance for dependency injection."""
    from app.lib.document_processing.service import TextExtractionService

    return TextExtractionService(default_provider=provider)


# --- Type Aliases ---

TextExtractorDep = Annotated["TextExtractor", Depends(get_text_extractor_dependency)]
TextExtractionServiceDep = Annotated[
    "TextExtractionService", Depends(get_text_extraction_service_dependency)
]
