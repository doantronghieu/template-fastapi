"""Centralized dependency injection providers for core application components."""

from collections.abc import AsyncGenerator
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends
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


# Type aliases for cleaner endpoint signatures
SessionDep = Annotated[AsyncSession, Depends(get_session)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
RedisDep = Annotated[redis.Redis, Depends(get_redis_client)]
