"""Telnyx SDK client singleton."""

from functools import lru_cache

from telnyx import AsyncTelnyx

from app.integrations.telnyx.config import telnyx_settings


@lru_cache(maxsize=1)
def get_telnyx_client() -> AsyncTelnyx:
    """Cached singleton."""
    return AsyncTelnyx(api_key=telnyx_settings.TELNYX_API_KEY)
