"""Text extractor base class.

Defines the interface for text extraction providers.
"""

from abc import ABC, abstractmethod
from typing import Annotated

from app.lib.document_processing.schemas.dto import (
    DocumentSource,
    TextExtractionOptions,
    TextExtractionResult,
    UrlDocumentSource,
)


class TextExtractor(ABC):
    """Abstract base class for text extraction from documents."""

    @abstractmethod
    def extract_text(
        self,
        source: Annotated[DocumentSource, "Document source to extract text from"],
        options: Annotated[
            TextExtractionOptions | None, "Provider-specific extraction options"
        ] = None,
    ) -> TextExtractionResult:
        """Extract text from document source."""
        ...

    def _check_url_support(
        self,
        source: Annotated[DocumentSource, "Source to check for URL type"],
    ) -> None:
        """Raise NotImplementedError if source is URL and provider doesn't support it."""
        if isinstance(source, UrlDocumentSource):
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support URL extraction"
            )
