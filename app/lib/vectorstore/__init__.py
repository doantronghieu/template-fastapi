"""Vectorstore library for vector storage and search."""

from app.lib.vectorstore.config import VectorStoreSettings, vectorstore_settings
from app.lib.vectorstore.dependencies import VectorStoreDep, get_vectorstore
from app.lib.vectorstore.service import VectorStore

__all__ = [
    "VectorStore",
    "VectorStoreSettings",
    "vectorstore_settings",
    "get_vectorstore",
    "VectorStoreDep",
]
