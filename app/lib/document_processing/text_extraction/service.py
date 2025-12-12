"""Text extraction service.

Internal service for text extraction from documents.
"""

from pathlib import Path
from typing import Annotated

from app.lib.document_processing.text_extraction.factory import get_text_extractor
from app.lib.document_processing.text_extraction.schemas.dto import (
    DoclingTextExtractionMode,
    DoclingTextExtractionOptions,
    DocumentSource,
    MistralTextExtractionOptions,
    TextExtractionOptions,
    TextExtractionProvider,
    TextExtractionResult,
)


class TextExtractionService:
    """Service for text extraction from documents.

    Provides provider-agnostic text extraction from files, bytes, or URLs.
    """

    def __init__(
        self,
        default_provider: Annotated[
            TextExtractionProvider, "Default extraction provider"
        ] = TextExtractionProvider.DOCLING,
    ) -> None:
        self._default_provider = default_provider

    def extract_from_file(
        self,
        path: Annotated[str | Path, "Path to document file"],
        provider: Annotated[TextExtractionProvider | None, "Provider override"] = None,
        options: Annotated[TextExtractionOptions | None, "Provider options"] = None,
    ) -> TextExtractionResult:
        """Extract text from file path."""
        source = DocumentSource.from_path(path)
        return self._extract(source, provider, options)

    def extract_from_bytes(
        self,
        content: Annotated[bytes, "Raw file content"],
        filename: Annotated[str, "Original filename for type detection"],
        provider: Annotated[TextExtractionProvider | None, "Provider override"] = None,
        options: Annotated[TextExtractionOptions | None, "Provider options"] = None,
    ) -> TextExtractionResult:
        """Extract text from bytes content."""
        source = DocumentSource.from_bytes(content, filename)
        return self._extract(source, provider, options)

    def extract_from_url(
        self,
        url: Annotated[str, "Document URL"],
        provider: Annotated[TextExtractionProvider | None, "Provider override"] = None,
        options: Annotated[TextExtractionOptions | None, "Provider options"] = None,
    ) -> TextExtractionResult:
        """Extract text from URL (provider must support URL extraction)."""
        source = DocumentSource.from_url(url)
        return self._extract(source, provider, options)

    def _extract(
        self,
        source: DocumentSource,
        provider: TextExtractionProvider | None,
        options: TextExtractionOptions | None,
    ) -> TextExtractionResult:
        """Internal extraction dispatcher."""
        extractor = get_text_extractor(provider or self._default_provider)
        return extractor.extract_text(source, options)

    @staticmethod
    def create_docling_options(
        mode: str = "local",
        enable_ocr: bool = False,
    ) -> DoclingTextExtractionOptions:
        """Create Docling-specific extraction options."""
        return DoclingTextExtractionOptions(
            mode=DoclingTextExtractionMode(mode),
            enable_ocr=enable_ocr,
        )

    @staticmethod
    def create_mistral_options(
        include_image_base64: bool = False,
    ) -> MistralTextExtractionOptions:
        """Create Mistral-specific extraction options."""
        return MistralTextExtractionOptions(include_image_base64=include_image_base64)
