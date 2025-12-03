"""LLM provider factory for runtime provider selection.

Implements the Strategy pattern by selecting the appropriate LLM provider
based on application configuration.
"""

from functools import lru_cache

from app.lib.llm.base import LLMProvider
from app.lib.llm.config import LLMProviderType


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider based on LLM_PROVIDER setting."""
    # Import providers here to avoid circular dependency
    from app.core.config import settings
    from app.lib.langchain.llm import LangChainLLMProvider

    providers: dict[str, type[LLMProvider]] = {
        LLMProviderType.LANGCHAIN.value: LangChainLLMProvider,
    }

    provider_class = providers.get(settings.LLM_PROVIDER)
    if not provider_class:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown LLM provider: {settings.LLM_PROVIDER}. "
            f"Available providers: {available}"
        )

    return provider_class()
