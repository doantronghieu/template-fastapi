"""Text extractor dependency injection.

FastAPI dependencies for text extraction.
"""

from typing import Annotated

from fastapi import Depends, Query

from app.lib.document_processing.base import TextExtractor
from app.lib.document_processing.factory import get_text_extractor
from app.lib.document_processing.schemas import ProviderType


def get_text_extractor_dep(
    provider: Annotated[
        ProviderType,
        Query(description="Text extraction provider"),
    ] = ProviderType.DOCLING,
) -> TextExtractor:
    """FastAPI dependency for text extractor with provider selection."""
    return get_text_extractor(provider)


TextExtractorDep = Annotated[TextExtractor, Depends(get_text_extractor_dep)]
