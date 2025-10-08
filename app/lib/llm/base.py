"""Base protocol for LLM provider implementations.

Defines the common interface that all LLM providers must implement,
enabling runtime provider switching via the Strategy pattern.
"""

from collections.abc import AsyncIterator
from typing import Protocol

from langchain_core.language_models import BaseChatModel


class LLMProvider(Protocol):
    """Protocol defining the interface for LLM provider implementations.

    All provider implementations must support:
    - Model creation with configurable parameters
    - Three invocation modes: invoke, batch, stream
    """

    def create_chat_model(
        self,
        model: str,
        model_provider: str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> BaseChatModel:
        """Create a chat model instance.

        Args:
            model: Model identifier (e.g., "gpt-5-nano")
            model_provider: Provider identifier (e.g., "openai")
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            Configured chat model instance
        """
        ...

    async def invoke_model(
        self,
        prompt: str | list[str],
        mode: str = "invoke",
        model: BaseChatModel | None = None,
        model_name: str | None = None,
        model_provider: str | None = None,
        temperature: float = 0.0,
        **kwargs,
    ) -> str | list[str] | AsyncIterator[str]:
        """Invoke LLM with specified mode.

        Args:
            prompt: Single prompt or list of prompts (for batch mode)
            mode: Invocation mode ("invoke", "batch", or "stream")
            model: Pre-configured model instance (optional)
            model_name: Model identifier (required if model not provided)
            model_provider: Provider identifier (optional)
            temperature: Sampling temperature (0.0 to 1.0)
            **kwargs: Additional provider-specific parameters

        Returns:
            - "invoke" mode: Single response string
            - "batch" mode: List of response strings
            - "stream" mode: AsyncIterator yielding response chunks

        Raises:
            ValueError: If neither model nor model_name provided
        """
        ...
