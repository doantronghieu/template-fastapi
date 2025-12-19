"""Text chunking service."""

import logging
from typing import Annotated

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.lib.document_processing.chunking.config import chunking_settings
from app.lib.document_processing.chunking.schemas import Chunk, ChunkingOptions, Document

logger = logging.getLogger(__name__)


class DocumentChunker:
    """Document chunking service."""

    def __init__(
        self,
        chunk_size: Annotated[int | None, "Max chunk size"] = None,
        chunk_overlap: Annotated[int | None, "Overlap between chunks"] = None,
        separators: Annotated[list[str] | None, "Custom separators"] = None,
    ):
        """Initialize chunker with default or custom settings."""
        self._chunk_size = chunk_size or chunking_settings.CHUNK_SIZE
        self._chunk_overlap = chunk_overlap or chunking_settings.CHUNK_OVERLAP
        self._separators = separators
        self._splitter = self._create_splitter(
            self._chunk_size, self._chunk_overlap, self._separators
        )

    def _create_splitter(
        self,
        chunk_size: int,
        chunk_overlap: int,
        separators: list[str] | None,
    ) -> RecursiveCharacterTextSplitter:
        """Create splitter with validated overlap."""
        # Ensure overlap is less than chunk size
        if chunk_overlap >= chunk_size:
            chunk_overlap = max(0, chunk_size - 1)

        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False,
        )

    def chunk(
        self,
        text: Annotated[str, "Text to chunk"],
        options: Annotated[ChunkingOptions | None, "Override options"] = None,
    ) -> list[Chunk]:
        """Split text into chunks."""
        if not text or not text.strip():
            return []

        # Use default splitter or create custom one if options provided
        splitter = self._splitter
        chunk_size = self._chunk_size

        if options and (options.chunk_size or options.chunk_overlap or options.separators):
            chunk_size = options.chunk_size or self._chunk_size
            chunk_overlap = options.chunk_overlap or self._chunk_overlap
            separators = options.separators or self._separators
            splitter = self._create_splitter(chunk_size, chunk_overlap, separators)

        # Return single chunk if text fits
        if len(text) <= chunk_size:
            return [Chunk(text=text, index=0, metadata={})]

        chunks_text = splitter.split_text(text)
        return [
            Chunk(text=chunk_text, index=i, metadata={})
            for i, chunk_text in enumerate(chunks_text)
        ]

    def chunk_documents(
        self,
        documents: Annotated[list[Document], "Documents to chunk"],
        options: Annotated[ChunkingOptions | None, "Override options"] = None,
    ) -> list[Chunk]:
        """Chunk multiple documents, preserving source metadata."""
        all_chunks: list[Chunk] = []
        global_index = 0

        for doc_idx, doc in enumerate(documents):
            doc_chunks = self.chunk(doc.content, options)

            for chunk in doc_chunks:
                chunk.metadata = {
                    **doc.metadata,
                    "source_doc_index": doc_idx,
                    "chunk_index_in_doc": chunk.index,
                }
                chunk.index = global_index
                global_index += 1
                all_chunks.append(chunk)

        return all_chunks

    @property
    def chunk_size(self) -> int:
        """Get configured chunk size."""
        return self._chunk_size

    @property
    def chunk_overlap(self) -> int:
        """Get configured overlap."""
        return self._chunk_overlap
