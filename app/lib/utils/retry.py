"""Retry decorators with exponential backoff for sync and async functions."""

import asyncio
import logging
import time
from functools import wraps
from typing import Annotated, Callable, Type, TypeVar

logger = logging.getLogger(__name__)
T = TypeVar("T")


def retry(
    max_retries: Annotated[int, "Maximum retry attempts"] = 3,
    exceptions: Annotated[tuple[Type[Exception], ...], "Exceptions to retry on"] = (
        Exception,
    ),
    backoff_base: Annotated[
        float, "Exponential backoff base (delay = base^attempt)"
    ] = 2.0,
    log_attempts: Annotated[bool, "Log warning on each failed attempt"] = True,
) -> Callable:
    """Decorator for sync functions with exponential backoff retry."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts",
                            exc_info=True,
                        )
                        raise
                    if log_attempts:
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_retries} failed: {e}"
                        )
                    time.sleep(backoff_base**attempt)
            raise RuntimeError(f"{func.__name__} exhausted all retries")

        return wrapper

    return decorator


def async_retry(
    max_retries: Annotated[int, "Maximum retry attempts"] = 3,
    exceptions: Annotated[tuple[Type[Exception], ...], "Exceptions to retry on"] = (
        Exception,
    ),
    backoff_base: Annotated[
        float, "Exponential backoff base (delay = base^attempt)"
    ] = 2.0,
    log_attempts: Annotated[bool, "Log warning on each failed attempt"] = True,
) -> Callable:
    """Decorator for async functions with exponential backoff retry."""

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            for attempt in range(1, max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} attempts",
                            exc_info=True,
                        )
                        raise
                    if log_attempts:
                        logger.warning(
                            f"{func.__name__} attempt {attempt}/{max_retries} failed: {e}"
                        )
                    await asyncio.sleep(backoff_base**attempt)
            raise RuntimeError(f"{func.__name__} exhausted all retries")

        return wrapper

    return decorator
