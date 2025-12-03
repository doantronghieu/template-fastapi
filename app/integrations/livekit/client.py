"""LiveKit API client singleton."""

from functools import lru_cache

from livekit import api

from app.integrations.livekit.config import livekit_settings


@lru_cache(maxsize=1)
def get_livekit_client() -> api.LiveKitAPI:
    """Cached singleton."""
    return api.LiveKitAPI(
        livekit_settings.http_url,
        livekit_settings.LIVEKIT_API_KEY,
        livekit_settings.LIVEKIT_API_SECRET,
    )
