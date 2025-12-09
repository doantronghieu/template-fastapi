"""Text extractor factory for provider selection."""

from functools import lru_cache
from typing import TYPE_CHECKING, Annotated

from app.core.autodiscover import ModuleType, require_module
from app.lib.document_processing.schemas.dto import ProviderType

if TYPE_CHECKING:
    from app.lib.document_processing.base import TextExtractor


@lru_cache(maxsize=2)
def get_text_extractor(
    provider: Annotated[ProviderType, "Provider to use"],
) -> "TextExtractor":
    """Get cached text extractor for provider."""
    providers = {
        ProviderType.DOCLING: _get_docling_text_extractor,
        ProviderType.MISTRAL: _get_mistral_text_extractor,
    }
    return providers[provider]()


@require_module(ModuleType.INTEGRATIONS, "docling")
def _get_docling_text_extractor() -> "TextExtractor":
    from app.integrations.docling.text_extractor import DoclingTextExtractor

    return DoclingTextExtractor()


@require_module(ModuleType.INTEGRATIONS, "mistral")
def _get_mistral_text_extractor() -> "TextExtractor":
    from app.integrations.mistral.text_extractor import MistralTextExtractor

    return MistralTextExtractor()
