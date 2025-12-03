"""DeepGram SDK client singleton."""

from functools import lru_cache

from deepgram import DeepgramClient

from app.integrations.deepgram.config import deepgram_settings


@lru_cache(maxsize=1)
def get_deepgram_client() -> DeepgramClient:
    """Cached singleton."""
    return DeepgramClient(deepgram_settings.DEEPGRAM_API_KEY)
