"""LLM configuration enums and mappings.

Shared configuration used across all LLM provider implementations.

Model specifications sourced from:
- Groq: https://console.groq.com/docs/models
- OpenRouter: https://openrouter.ai/docs/api/reference/parameters
- Google: https://ai.google.dev/gemini-api/docs/models
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal

# OpenRouter routing preference type
OpenRouterRouting = Literal["floor", "nitro"] | None


class LLMProviderType(str, Enum):
    """Supported LLM provider types for runtime selection."""

    LANGCHAIN = "langchain"
    OPENAI = "openai"


class ModelProvider(str, Enum):
    """Supported LLM model providers."""

    OPENAI = "openai"
    GROQ = "groq"
    GOOGLE = "google_genai"
    OPENROUTER = "openrouter"


class Model(str, Enum):
    """Supported LLM models."""

    # OpenAI models
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"

    # Groq models
    LLAMA_3_1_8B_INSTANT = "llama-3.1-8b-instant"
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"

    # Google Gemini models
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"

    # Unified model IDs: org/model (OpenRouter)
    GROK_4_1_FAST_UID = "x-ai/grok-4.1-fast"
    GEMINI_2_5_PRO_UID = "google/gemini-2.5-pro"
    GEMINI_2_5_FLASH_UID = "google/gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE_UID = "google/gemini-2.5-flash-lite"

    def with_openrouter_routing(self, routing: OpenRouterRouting = None) -> str:
        """Get model ID with optional OpenRouter routing suffix."""
        if routing:
            return f"{self.value}:{routing}"
        return self.value


class InvocationMode(str, Enum):
    """LLM invocation modes."""

    INVOKE = "invoke"
    BATCH = "batch"
    STREAM = "stream"


# -----------------------------------------------------------------------------
# Model Configuration
# -----------------------------------------------------------------------------


@dataclass(frozen=True)
class ModelConfig:
    """Configuration for a specific LLM model."""

    provider: ModelProvider
    context_window: int  # Max input tokens
    max_output_tokens: int  # Max completion tokens


# Model specifications
MODEL_CONFIG: dict[Model, ModelConfig] = {
    # Groq models (https://console.groq.com/docs/models)
    Model.LLAMA_3_1_8B_INSTANT: ModelConfig(ModelProvider.GROQ, 131_072, 131_072),
    Model.GPT_OSS_120B: ModelConfig(ModelProvider.GROQ, 131_072, 65_536),
    Model.GPT_OSS_20B: ModelConfig(ModelProvider.GROQ, 131_072, 65_536),
    # Google Gemini models (direct API)
    Model.GEMINI_2_5_PRO: ModelConfig(ModelProvider.GOOGLE, 1_048_576, 65_536),
    Model.GEMINI_2_5_FLASH: ModelConfig(ModelProvider.GOOGLE, 1_048_576, 65_536),
    # OpenAI models
    Model.GPT_5: ModelConfig(ModelProvider.OPENAI, 128_000, 16_384),
    Model.GPT_5_MINI: ModelConfig(ModelProvider.OPENAI, 128_000, 16_384),
    Model.GPT_5_NANO: ModelConfig(ModelProvider.OPENAI, 128_000, 8_192),
    # OpenRouter models (via unified API)
    Model.GROK_4_1_FAST_UID: ModelConfig(ModelProvider.OPENROUTER, 131_072, 32_768),
    Model.GEMINI_2_5_PRO_UID: ModelConfig(ModelProvider.OPENROUTER, 1_048_576, 65_536),
    Model.GEMINI_2_5_FLASH_UID: ModelConfig(
        ModelProvider.OPENROUTER, 1_048_576, 65_536
    ),
    Model.GEMINI_2_5_FLASH_LITE_UID: ModelConfig(
        ModelProvider.OPENROUTER, 1_048_576, 65_536
    ),
}

# Provider-specific concurrency limits (max parallel LLM calls)
# - Groq: 250k TPM developer limit
# - OpenRouter: No hard rate limits for paid models
# - OpenAI/Google: Standard tier limits
PROVIDER_MAX_CONCURRENCY: dict[ModelProvider, int] = {
    ModelProvider.GROQ: 1,
    ModelProvider.OPENROUTER: 10,
    ModelProvider.OPENAI: 5,
    ModelProvider.GOOGLE: 5,
}


# -----------------------------------------------------------------------------
# Helper Functions
# -----------------------------------------------------------------------------


def get_model_config(model: Model) -> ModelConfig:
    """Get configuration for a specific model."""
    if model not in MODEL_CONFIG:
        raise ValueError(f"Unknown model: {model}")
    return MODEL_CONFIG[model]


def get_provider_for_model(model: Model) -> ModelProvider:
    """Get the appropriate provider for a given model."""
    return get_model_config(model).provider


def get_max_output_tokens(model: Model) -> int:
    """Get max output tokens for a model."""
    return get_model_config(model).max_output_tokens


def get_max_concurrency(model: Model) -> int:
    """Get max concurrency based on the model's provider."""
    provider = get_model_config(model).provider
    return PROVIDER_MAX_CONCURRENCY[provider]
