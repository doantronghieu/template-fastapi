"""Vectorstore dependency injection."""

from typing import TYPE_CHECKING, Annotated, AsyncGenerator

from fastapi import Depends

if TYPE_CHECKING:
    from app.lib.vectorstore.service import VectorStore

_client: "VectorStore | None" = None


async def get_vectorstore() -> AsyncGenerator["VectorStore", None]:
    """Get Qdrant vectorstore instance (singleton)."""
    global _client
    if _client is None:
        from app.lib.vectorstore.service import VectorStore
        _client = VectorStore()
    yield _client


VectorStoreDep = Annotated["VectorStore", Depends(get_vectorstore)]
