"""Embeddings configuration."""

from enum import Enum

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.lib.llm.settings import llm_settings


class EmbeddingModel(str, Enum):
    """Supported OpenAI embedding models."""

    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"
    TEXT_EMBEDDING_3_LARGE = "text-embedding-3-large"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


class EmbeddingsSettings(BaseSettings):
    """Embeddings settings."""

    EMBEDDING_MODEL: str = Field(
        default=EmbeddingModel.TEXT_EMBEDDING_3_SMALL.value,
        description="Default embedding model",
    )
    EMBEDDING_DIMENSIONS: int = Field(default=1536, description="Vector dimensions")

    model_config = SettingsConfigDict(extra="allow")

    @property
    def openai_api_key(self) -> str:
        """Get OpenAI API key from LLM settings."""
        return llm_settings.OPENAI_API_KEY


embeddings_settings = EmbeddingsSettings()
