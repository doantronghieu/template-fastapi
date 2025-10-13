"""Centralized dependency injection providers for core application components."""

import os
from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, settings
from app.core.database import async_session_maker

# Redis client singleton
_redis_client: redis.Redis | None = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide async database session."""
    async with async_session_maker() as session:
        yield session


def get_settings() -> Settings:
    """Provide application settings."""
    return settings


async def get_redis_client() -> redis.Redis:
    """
    Get or create Redis client singleton.

    Returns:
        redis.Redis: Async Redis client instance with UTF-8 encoding

    Implementation:
        - Singleton pattern: Single connection shared across application
        - decode_responses=True: Auto-decode bytes to strings
        - Connects to Redis Cloud (same instance used by Celery)

    Note:
        Redis Cloud free tier has connection limit. Singleton prevents
        connection exhaustion by reusing one client per app instance.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")) -> None:
    """Verify API key for endpoint authentication.

    Generic API key validator for protecting any endpoint. Validates against
    API_KEY environment variable.

    Args:
        x_api_key: API key from X-API-Key header

    Raises:
        HTTPException: 503 if not configured, 401 if invalid

    Usage:
        # Protect entire router
        router = APIRouter(dependencies=[Depends(verify_api_key)])

        # Or protect specific endpoint
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            return {"message": "Protected"}
    """
    expected_key = os.getenv("API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="API key not configured on server",
        )

    if x_api_key != expected_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )


# Type aliases for cleaner endpoint signatures
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
