"""LLM library with pluggable provider support.

Provides a unified interface for LLM operations with runtime provider selection.
Configure the provider via LLM_PROVIDER environment variable.

Example:
    >>> # In .env: LLM_PROVIDER=langchain
    >>> from app.lib.llm import get_llm_provider, Model, InvocationMode
    >>>
    >>> provider = get_llm_provider()
    >>> response = await provider.invoke_model(
    ...     "Hello!",
    ...     model_name=Model.GPT_5_NANO.value,
    ...     model_provider="openai"
    ... )
"""

from app.lib.llm.base import LLMProvider
from app.lib.llm.config import (
    InvocationMode,
    LLMProviderType,
    Model,
    ModelProvider,
    get_provider_for_model,
)
from app.lib.llm.dependencies import LLMProviderDep, get_llm_provider
from app.lib.llm.factory import get_llm_provider as factory_get_llm_provider

__all__ = [
    # Factory
    "factory_get_llm_provider",
    # Protocol
    "LLMProvider",
    # Config
    "LLMProviderType",
    "Model",
    "ModelProvider",
    "InvocationMode",
    "get_provider_for_model",
    # Dependencies
    "get_llm_provider",
    "LLMProviderDep",
]
