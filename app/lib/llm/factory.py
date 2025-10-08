"""LLM provider factory for runtime provider selection.

Implements the Strategy pattern by selecting the appropriate LLM provider
based on application configuration.
"""

from app.lib.langchain.llm import LangChainLLMProvider
from app.lib.llm.base import LLMProvider
from app.lib.llm.config import LLMProviderType


def get_llm_provider() -> LLMProvider:
    # Import here to avoid circular dependency with app.core.config
    from app.core.config import settings

    """Factory function to get the configured LLM provider.

    Returns the provider implementation based on the LLM_PROVIDER setting.
    This enables runtime switching between different LLM libraries.

    Returns:
        Configured LLM provider instance

    Raises:
        ValueError: If LLM_PROVIDER setting specifies an unknown provider

    Example:
        >>> # In .env: LLM_PROVIDER=langchain
        >>> provider = get_llm_provider()
        >>> model = provider.create_chat_model("gpt-5-nano", "openai")
    """
    providers: dict[str, type[LLMProvider]] = {
        LLMProviderType.LANGCHAIN.value: LangChainLLMProvider,
        # Future providers can be added here:
        # LLMProviderType.OPENAI.value: OpenAIProvider,
    }

    provider_class = providers.get(settings.LLM_PROVIDER)
    if not provider_class:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown LLM provider: {settings.LLM_PROVIDER}. "
            f"Available providers: {available}"
        )

    return provider_class()
