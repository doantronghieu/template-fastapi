"""Chunking data transfer objects."""

from typing import Any

from pydantic import BaseModel, Field


class ChunkingOptions(BaseModel):
    """Options for text chunking."""

    chunk_size: int | None = Field(default=None, description="Max characters per chunk")
    chunk_overlap: int | None = Field(default=None, description="Overlap between chunks")
    separators: list[str] | None = Field(default=None, description="Custom separators")


class Chunk(BaseModel):
    """A text chunk with metadata."""

    text: str = Field(description="Chunk text content")
    index: int = Field(description="Chunk index in sequence")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @property
    def char_count(self) -> int:
        """Get character count."""
        return len(self.text)


class Document(BaseModel):
    """Source document for chunking."""

    content: str = Field(description="Document text content")
    metadata: dict[str, Any] = Field(default_factory=dict)
