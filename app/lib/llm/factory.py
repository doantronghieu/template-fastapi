"""LLM provider factory for runtime provider selection.

Implements the Strategy pattern by selecting the appropriate LLM provider
based on application configuration.
"""

from collections.abc import Callable
from functools import lru_cache

from app.core.autodiscover import ModuleType, require_module
from app.lib.llm.base import LLMProvider
from app.lib.llm.config import LLMProviderType


@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    """Get the configured LLM provider based on LLM_PROVIDER setting."""
    from app.lib.llm.settings import llm_settings

    providers: dict[str, Callable[[], LLMProvider]] = {
        LLMProviderType.LANGCHAIN.value: _get_langchain_provider,
    }

    provider_factory = providers.get(llm_settings.LLM_PROVIDER)
    if not provider_factory:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown LLM provider: {llm_settings.LLM_PROVIDER}. "
            f"Available providers: {available}"
        )

    return provider_factory()


@require_module(ModuleType.INTEGRATIONS, "langchain")
def _get_langchain_provider() -> LLMProvider:
    """Lazy import LangChain provider."""
    from app.integrations.langchain.llm import LangChainLLMProvider

    return LangChainLLMProvider()
