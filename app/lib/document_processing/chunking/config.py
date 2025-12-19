"""Chunking configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings


class ChunkingSettings(BaseSettings):
    """Default chunking settings."""

    CHUNK_SIZE: int = Field(default=1000, description="Default chunk size in characters")
    CHUNK_OVERLAP: int = Field(default=200, description="Default overlap between chunks")

    model_config = {"extra": "allow"}


chunking_settings = ChunkingSettings()
