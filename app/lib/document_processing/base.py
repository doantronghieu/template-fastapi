"""Text extractor abstract base class.

Defines the interface for document text extraction providers.
"""

from abc import ABC, abstractmethod
from typing import Annotated

from app.lib.document_processing.schemas.dto import (
    TextExtractionOptions,
    TextExtractionResult,
    TextSource,
    UrlTextSource,
)


class TextExtractor(ABC):
    """Abstract base class for text extraction from documents."""

    @abstractmethod
    def extract_text(
        self,
        source: Annotated[TextSource, "Source document to extract text from"],
        options: Annotated[
            TextExtractionOptions | None, "Provider-specific extraction options"
        ] = None,
    ) -> TextExtractionResult:
        """Extract text from document source."""
        ...

    def _check_url_support(
        self,
        source: Annotated[TextSource, "Source to check for URL type"],
    ) -> None:
        """Raise NotImplementedError if source is URL and provider doesn't support it."""
        if isinstance(source, UrlTextSource):
            raise NotImplementedError(
                f"{self.__class__.__name__} does not support URL extraction"
            )
