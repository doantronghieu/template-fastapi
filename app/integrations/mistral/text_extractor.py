"""Mistral text extractor implementation."""

import base64
import logging
import mimetypes
from typing import Annotated

from mistralai import Mistral

from app.integrations.mistral.config import mistral_settings
from app.lib.document_processing.base import TextExtractor
from app.lib.document_processing.schemas.dto import (
    BytesTextSource,
    PathTextSource,
    TextExtractionOptions,
    TextExtractionResult,
    TextSource,
    UrlTextSource,
)

logger = logging.getLogger(__name__)


class MistralTextExtractor(TextExtractor):
    """Text extractor using Mistral OCR API.

    Supports PDF, images. Features URL extraction.
    """

    def __init__(self):
        self._client: Mistral | None = None

    @property
    def client(self) -> Mistral:
        """Lazy-initialize Mistral client."""
        if self._client is None:
            if not mistral_settings.MISTRAL_API_KEY:
                raise ValueError("MISTRAL_API_KEY environment variable is required")
            self._client = Mistral(api_key=mistral_settings.MISTRAL_API_KEY)
        return self._client

    def _get_mime_type(
        self,
        filename: Annotated[str, "Filename for MIME type detection"],
    ) -> str:
        """Detect MIME type from filename."""
        mime_type, _ = mimetypes.guess_type(filename)
        return mime_type or "application/octet-stream"

    def _call_ocr(
        self,
        url: Annotated[str, "URL or data URL to process"],
        mime_type: Annotated[str, "MIME type for document type selection"],
    ) -> TextExtractionResult:
        """Call Mistral OCR API with appropriate document type."""
        is_image = mime_type.startswith("image/")

        document = (
            {"type": "image_url", "image_url": {"url": url}}
            if is_image
            else {"type": "document_url", "document_url": url}
        )

        response = self.client.ocr.process(
            model=mistral_settings.MISTRAL_OCR_MODEL,
            document=document,
        )

        markdown = "\n\n".join(page.markdown for page in response.pages)
        return TextExtractionResult(success=True, result=markdown)

    def extract_text(
        self,
        source: Annotated[TextSource, "Input source (path, bytes, or URL)"],
        options: Annotated[
            TextExtractionOptions | None, "Provider-specific options"
        ] = None,
    ) -> TextExtractionResult:
        """Extract text from source using Mistral OCR."""
        try:
            if isinstance(source, PathTextSource):
                return self._extract_from_path(source)
            elif isinstance(source, BytesTextSource):
                return self._extract_from_bytes(source)
            elif isinstance(source, UrlTextSource):
                return self._extract_from_url(source)
            else:
                return TextExtractionResult(
                    success=False,
                    message=f"Unsupported source type: {type(source).__name__}",
                )
        except Exception as e:
            logger.exception(f"Mistral extraction failed: {e}")
            return TextExtractionResult(success=False, message=str(e))

    def _extract_from_path(
        self,
        source: Annotated[PathTextSource, "Path source"],
    ) -> TextExtractionResult:
        """Extract from file path."""
        if not source.path.exists():
            return TextExtractionResult(
                success=False, message=f"File not found: {source.path}"
            )
        content = source.path.read_bytes()
        return self._extract_from_bytes(
            BytesTextSource(content=content, filename=source.path.name)
        )

    def _extract_from_bytes(
        self,
        source: Annotated[BytesTextSource, "Bytes source"],
    ) -> TextExtractionResult:
        """Extract from file bytes using data URL."""
        mime_type = self._get_mime_type(source.filename)
        encoded = base64.b64encode(source.content).decode()
        data_url = f"data:{mime_type};base64,{encoded}"
        return self._call_ocr(data_url, mime_type)

    def _extract_from_url(
        self,
        source: Annotated[UrlTextSource, "URL source"],
    ) -> TextExtractionResult:
        """Extract from URL."""
        mime_type = self._get_mime_type(source.url)
        return self._call_ocr(source.url, mime_type)
