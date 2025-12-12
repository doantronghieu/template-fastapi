"""Structured extraction client factory.

Provides cached async client for LLM structured data extraction.
"""

from functools import lru_cache
from typing import Annotated

import instructor
import redis
from groq import AsyncGroq
from instructor.cache import BaseCache
from openai import AsyncOpenAI

from app.core.config import settings
from app.lib.llm.config import ModelProvider


class RedisCache(BaseCache):
    """Redis-backed cache for Instructor responses."""

    def __init__(self, url: str, ttl: int = 3600):
        self.client = redis.from_url(url)
        self.ttl = ttl

    def get(self, key: str) -> str | None:
        """Get cached value by key."""
        value: bytes | None = self.client.get(key)
        return value.decode("utf-8") if value else None

    def set(self, key: str, value: str, **_: int) -> None:
        """Set cache value with TTL."""
        self.client.setex(key, self.ttl, value)


@lru_cache(maxsize=1)
def _get_redis_cache(ttl: int = 3600) -> RedisCache:
    """Get Redis cache instance for Instructor."""
    return RedisCache(url=settings.REDIS_URL, ttl=ttl)


def get_extraction_client(
    provider: Annotated[ModelProvider, "Model provider"] = ModelProvider.OPENROUTER,
    mode: Annotated[instructor.Mode, "Extraction mode"] = instructor.Mode.JSON,
    cache_enabled: Annotated[bool, "Enable Redis caching"] = False,
    cache_ttl: Annotated[int, "Cache TTL in seconds"] = 3600,
) -> instructor.AsyncInstructor:
    """Get client for structured LLM extraction.

    Supports OpenRouter and Groq providers.
    Optionally enables Redis caching for responses.
    """
    cache = _get_redis_cache(cache_ttl) if cache_enabled else None

    if provider == ModelProvider.GROQ:
        return instructor.from_groq(
            AsyncGroq(api_key=settings.GROQ_API_KEY),
            mode=instructor.Mode.JSON,  # Groq works best with JSON mode
            cache=cache,
        )

    # Default: OpenRouter
    return instructor.from_openai(
        AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=settings.OPENROUTER_API_KEY,
        ),
        mode=mode,
        cache=cache,
    )
