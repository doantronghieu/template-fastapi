"""Text chunking module for document processing."""

from app.lib.document_processing.chunking.config import ChunkingSettings, chunking_settings
from app.lib.document_processing.chunking.schemas import Chunk, ChunkingOptions, Document
from app.lib.document_processing.chunking.service import DocumentChunker

__all__ = [
    "DocumentChunker",
    "Chunk",
    "ChunkingOptions",
    "Document",
    "ChunkingSettings",
    "chunking_settings",
]
