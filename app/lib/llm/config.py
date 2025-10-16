"""LLM configuration enums and mappings.

Shared configuration used across all LLM provider implementations.
"""

from enum import Enum


class LLMProviderType(str, Enum):
    """Supported LLM provider types for runtime selection."""

    LANGCHAIN = "langchain"
    OPENAI = "openai"


class ModelProvider(str, Enum):
    """Supported LLM model providers."""

    OPENAI = "openai"
    GROQ = "groq"
    GOOGLE = "google_genai"


class Model(str, Enum):
    """Supported LLM models."""

    # OpenAI models
    GPT_5 = "gpt-5"

    # Groq models (OpenAI OSS on Groq infrastructure)
    GPT_OSS_120B = "openai/gpt-oss-120b"
    GPT_OSS_20B = "openai/gpt-oss-20b"

    # Google Gemini models
    GEMINI_2_5_PRO = "gemini-2.5-pro"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"


class InvocationMode(str, Enum):
    """LLM invocation modes."""

    INVOKE = "invoke"
    BATCH = "batch"
    STREAM = "stream"


# Model to provider mapping for validation
MODEL_PROVIDER_MAP: dict[Model, ModelProvider] = {
    Model.GPT_5: ModelProvider.OPENAI,
    Model.GPT_OSS_120B: ModelProvider.GROQ,
    Model.GPT_OSS_20B: ModelProvider.GROQ,
    Model.GEMINI_2_5_PRO: ModelProvider.GOOGLE,
    Model.GEMINI_2_5_FLASH: ModelProvider.GOOGLE,
}


def get_provider_for_model(model: Model) -> ModelProvider:
    """Get the appropriate provider for a given model.

    Args:
        model: The model to look up

    Returns:
        The provider for the model

    Raises:
        ValueError: If model is not found in mapping
    """
    if model not in MODEL_PROVIDER_MAP:
        raise ValueError(f"Unknown model: {model}")
    return MODEL_PROVIDER_MAP[model]
