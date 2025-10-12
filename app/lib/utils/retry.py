"""Retry utilities for handling transient failures.

Provides decorators for automatic retry with exponential backoff.
"""

import asyncio
import logging
from functools import wraps
from typing import Callable, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


def async_retry(
    max_retries: int = 3,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    backoff_base: float = 2.0,
) -> Callable:
    """
    Decorator for automatic retry with exponential backoff on async functions.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        exceptions: Tuple of exceptions to catch and retry (default: Exception)
        backoff_base: Base for exponential backoff calculation (default: 2.0)

    Returns:
        Decorated function with retry logic

    Example:
        @async_retry(max_retries=3, exceptions=(httpx.HTTPError,))
        async def fetch_data():
            response = await client.get(url)
            return response.json()

    Note:
        Always logs errors with full stack trace on final failure.
    """

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except exceptions:
                    # Re-raise on final attempt with error logging
                    if attempt == max_retries - 1:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts",
                            exc_info=True,
                        )
                        raise

                    # Exponential backoff: 2^0=1s, 2^1=2s, 2^2=4s, etc.
                    delay = backoff_base**attempt
                    await asyncio.sleep(delay)

            # This line should never be reached due to raise above,
            # but helps type checker understand the return type
            raise RuntimeError(f"{func.__name__} exhausted all retries")

        return wrapper

    return decorator
