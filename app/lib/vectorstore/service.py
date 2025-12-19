"""Qdrant vectorstore service."""

import logging
from typing import Annotated, Any

from qdrant_client import AsyncQdrantClient, models

from app.lib.utils.retry import async_retry
from app.lib.vectorstore.config import vectorstore_settings

logger = logging.getLogger(__name__)


class VectorStore:
    """Async Qdrant vectorstore client."""

    def __init__(
        self,
        url: Annotated[str | None, "Qdrant URL"] = None,
        api_key: Annotated[str | None, "API key"] = None,
        timeout: Annotated[int | None, "Request timeout"] = None,
        prefer_grpc: Annotated[bool | None, "Use gRPC"] = None,
    ):
        """Initialize Qdrant client."""
        self._client = AsyncQdrantClient(
            url=url or vectorstore_settings.QDRANT_URL,
            api_key=api_key or vectorstore_settings.QDRANT_API_KEY,
            timeout=timeout or vectorstore_settings.QDRANT_TIMEOUT,
            prefer_grpc=prefer_grpc if prefer_grpc is not None else vectorstore_settings.QDRANT_PREFER_GRPC,
        )
        self._default_dimension = vectorstore_settings.QDRANT_DEFAULT_DIMENSION

    async def close(self) -> None:
        """Close client connection."""
        await self._client.close()

    # -------------------------------------------------------------------------
    # Collection Management
    # -------------------------------------------------------------------------

    async def create_collection(
        self,
        name: Annotated[str, "Collection name"],
        dimension: Annotated[int | None, "Vector dimension"] = None,
        distance: Annotated[models.Distance, "Distance metric"] = models.Distance.COSINE,
    ) -> bool:
        """Create a new collection."""
        if await self._client.collection_exists(name):
            logger.info(f"Collection '{name}' already exists")
            return False

        await self._client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=dimension or self._default_dimension,
                distance=distance,
            ),
        )
        logger.info(f"Created collection '{name}'")
        return True

    async def delete_collection(self, name: Annotated[str, "Collection name"]) -> bool:
        """Delete a collection."""
        if not await self._client.collection_exists(name):
            return False
        await self._client.delete_collection(name)
        logger.info(f"Deleted collection '{name}'")
        return True

    async def collection_exists(self, name: Annotated[str, "Collection name"]) -> bool:
        """Check if collection exists."""
        return await self._client.collection_exists(name)

    # -------------------------------------------------------------------------
    # Point Operations
    # -------------------------------------------------------------------------

    async def upsert(
        self,
        collection: Annotated[str, "Collection name"],
        points: Annotated[list[models.PointStruct], "Points to upsert"],
    ) -> models.UpdateResult:
        """Upsert points into collection."""
        if not points:
            return models.UpdateResult(operation_id=0, status=models.UpdateStatus.COMPLETED)

        return await self._client.upsert(
            collection_name=collection,
            points=points,
            wait=True,
        )

    async def delete(
        self,
        collection: Annotated[str, "Collection name"],
        ids: Annotated[list[str | int], "Point IDs to delete"],
    ) -> models.UpdateResult:
        """Delete points by IDs."""
        if not ids:
            return models.UpdateResult(operation_id=0, status=models.UpdateStatus.COMPLETED)

        return await self._client.delete(
            collection_name=collection,
            points_selector=models.PointIdsList(points=ids),
            wait=True,
        )

    # -------------------------------------------------------------------------
    # Search Operations
    # -------------------------------------------------------------------------

    @async_retry(max_retries=3)
    async def search(
        self,
        collection: Annotated[str, "Collection name"],
        query_vector: Annotated[list[float], "Query embedding"],
        limit: Annotated[int, "Max results"] = 10,
        filter: Annotated[dict[str, Any] | None, "Metadata filter"] = None,
        score_threshold: Annotated[float | None, "Min score"] = None,
        with_vectors: Annotated[bool, "Include vectors in results"] = False,
    ) -> list[models.ScoredPoint]:
        """Similarity search."""
        qdrant_filter = models.Filter(**filter) if filter else None

        results = await self._client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            score_threshold=score_threshold,
            with_payload=True,
            with_vectors=with_vectors,
        )

        return results.points

    @async_retry(max_retries=3)
    async def search_with_params(
        self,
        collection: Annotated[str, "Collection name"],
        query_vector: Annotated[list[float], "Query embedding"],
        limit: Annotated[int, "Number of results"] = 4,
        filter: Annotated[dict[str, Any] | None, "Metadata filter"] = None,
        exact: Annotated[bool, "Use exact search (slower but more accurate)"] = False,
    ) -> list[models.ScoredPoint]:
        """Search with custom search parameters."""
        qdrant_filter = models.Filter(**filter) if filter else None

        results = await self._client.query_points(
            collection_name=collection,
            query=query_vector,
            limit=limit,
            query_filter=qdrant_filter,
            with_payload=True,
            with_vectors=False,
            search_params=models.SearchParams(exact=exact),
        )

        return results.points
