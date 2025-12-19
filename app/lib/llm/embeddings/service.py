"""Embeddings service."""

import logging
from typing import Annotated

from langchain_openai import OpenAIEmbeddings

from app.lib.llm.embeddings.config import EmbeddingModel, embeddings_settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    """OpenAI embeddings service."""

    def __init__(
        self,
        model: Annotated[str | EmbeddingModel | None, "Embedding model"] = None,
        api_key: Annotated[str | None, "OpenAI API key"] = None,
        dimensions: Annotated[int | None, "Vector dimensions"] = None,
    ):
        """Initialize embeddings with OpenAI."""
        model_name = model.value if isinstance(model, EmbeddingModel) else model
        self._model = model_name or embeddings_settings.EMBEDDING_MODEL
        self._dimensions = dimensions or embeddings_settings.EMBEDDING_DIMENSIONS

        self._embeddings = OpenAIEmbeddings(
            model=self._model,
            api_key=api_key or embeddings_settings.openai_api_key,
            dimensions=self._dimensions,
        )

    async def embed_query(
        self,
        text: Annotated[str, "Text to embed"],
    ) -> list[float]:
        """Generate embedding for a single query text."""
        return await self._embeddings.aembed_query(text)

    async def embed_documents(
        self,
        texts: Annotated[list[str], "Texts to embed"],
    ) -> list[list[float]]:
        """Generate embeddings for multiple documents."""
        if not texts:
            return []
        return await self._embeddings.aembed_documents(texts)

    @property
    def model(self) -> str:
        """Get configured model name."""
        return self._model

    @property
    def dimensions(self) -> int:
        """Get vector dimensions."""
        return self._dimensions
