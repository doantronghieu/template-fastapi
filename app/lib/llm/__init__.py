"""LLM library with pluggable provider support.

Provides a unified interface for LLM operations with runtime provider selection.
Configure the provider via LLM_PROVIDER environment variable.
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
from app.lib.llm.utils import create_loader
from app.lib.llm.schemas.api import CreateModelRequest, InvokeModelRequest

__all__ = [
    # ABC
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
    # Schemas
    "CreateModelRequest",
    "InvokeModelRequest",
    # Resources
    "create_loader",
]
