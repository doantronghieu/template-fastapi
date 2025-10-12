"""Redis-based rate limiter service.

Implements sliding window rate limiting using Redis sorted sets (ZSET).
Provides distributed rate limiting across multiple application instances.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends

from app.core.dependencies import RedisDep

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    Redis-based rate limiter using sliding window algorithm.

    Uses Redis sorted sets (ZSET) to track request timestamps per user.
    Provides accurate, distributed rate limiting without "burst" issues.

    Algorithm:
        1. Remove timestamps outside current window (cleanup)
        2. Count requests within window
        3. If under limit, add current timestamp
        4. Set TTL for automatic cleanup

    Advantages over fixed window:
        - No burst at window boundaries
        - Accurate sliding window measurement
        - Works across multiple app instances

    Note:
        Fails open (allows requests) if Redis unavailable to prevent
        cascading failures affecting availability.
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self, user_id: str, max_per_minute: int, window_seconds: int = 60
    ) -> bool:
        """
        Check if user has exceeded rate limit using sliding window.

        Args:
            user_id: User identifier (e.g., PSID from Messenger)
            max_per_minute: Maximum requests allowed in window
            window_seconds: Time window in seconds (default: 60)

        Returns:
            bool: True if within limit (request allowed), False if exceeded

        Algorithm Steps:
            1. Remove old timestamps outside window (ZREMRANGEBYSCORE)
            2. Count remaining timestamps in window (ZCARD)
            3. If count >= max, reject (return False)
            4. If count < max, add current timestamp (ZADD) and accept
            5. Set expiration for automatic cleanup (EXPIRE)

        Fail-Open Policy:
            Returns True (allow) if Redis operation fails to maintain
            availability even when rate limiting is temporarily unavailable.
        """
        key = f"rate_limit:{user_id}"
        now = datetime.now(timezone.utc)
        window_start = now - timedelta(seconds=window_seconds)

        try:
            # Remove timestamps outside sliding window
            await self.redis.zremrangebyscore(key, "-inf", window_start.timestamp())

            # Count requests in current window
            request_count = await self.redis.zcard(key)

            # Reject if limit exceeded
            if request_count >= max_per_minute:
                return False

            # Add current timestamp and update expiration
            await self.redis.zadd(key, {str(now.timestamp()): now.timestamp()})
            await self.redis.expire(key, window_seconds * 2)  # 2x window for safety
            return True

        except Exception:
            logger.error(f"Rate limiter failed for user {user_id}", exc_info=True)
            # Fail open: Allow request if Redis unavailable (prioritize availability)
            return True


async def get_rate_limiter(redis_client: RedisDep) -> RedisRateLimiter:
    """
    Provide RedisRateLimiter instance with Redis dependency.

    Args:
        redis_client: Injected Redis client from core dependencies

    Returns:
        RedisRateLimiter: Initialized rate limiter instance
    """
    return RedisRateLimiter(redis_client)


# Type alias for dependency injection
RateLimiterDep = Annotated[RedisRateLimiter, Depends(get_rate_limiter)]
