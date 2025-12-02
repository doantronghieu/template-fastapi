"""Base class for LLM provider implementations.

Defines common interface and shared utilities for all LLM providers,
enabling runtime provider switching via the Strategy pattern.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Annotated

from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel


class LLMProvider(ABC):
    """Base class for LLM provider implementations.

    Provides shared utilities and defines required interface for:
    - Model creation with configurable parameters
    - Three invocation modes: invoke, batch, stream
    """

    def format_prompt(
        self,
        current_message: Annotated[str, "Current user message"],
        history: Annotated[list[dict] | None, "Previous messages with 'role' and 'content' keys"] = None,
    ) -> str:
        """Format prompt with XML structure for conversation context."""
        parts = []

        if history:
            history_text = "\n".join(
                f"<{msg['role']}>{msg['content']}</{msg['role']}>"
                for msg in history
            )
            parts.append(f"<history>\n{history_text}\n</history>")

        parts.append(f"<current_message>\n{current_message}\n</current_message>")

        return "\n\n".join(parts)

    @abstractmethod
    def create_model(
        self,
        model: Annotated[str, "Model identifier (e.g., 'gpt-5-nano')"],
        model_provider: Annotated[str | None, "Provider identifier (e.g., 'openai')"] = None,
        temperature: Annotated[float, "Sampling temperature (0.0 to 1.0)"] = 0.0,
        tools: Annotated[list | None, "Tools to bind to the model"] = None,
        schema: Annotated[type[BaseModel] | None, "Pydantic model for structured output"] = None,
        **kwargs,
    ) -> BaseChatModel:
        """Create a chat model instance with optional tools and structured output."""
        ...

    @abstractmethod
    async def invoke_model(
        self,
        prompt: Annotated[str | list[str], "Single prompt or list (for batch mode)"],
        mode: Annotated[str, "Invocation mode: 'invoke', 'batch', or 'stream'"] = "invoke",
        model: Annotated[BaseChatModel | None, "Pre-configured model instance"] = None,
        model_name: Annotated[str | None, "Model identifier (required if model not provided)"] = None,
        model_provider: Annotated[str | None, "Provider identifier"] = None,
        temperature: Annotated[float, "Sampling temperature (0.0 to 1.0)"] = 0.0,
        **kwargs,
    ) -> str | list[str] | AsyncIterator[str]:
        """Invoke LLM with specified mode."""
        ...
