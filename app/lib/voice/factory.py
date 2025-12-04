"""Voice provider factory for runtime provider selection.

Implements the Strategy pattern by selecting the appropriate STT/TTS provider
based on application configuration.
"""

from collections.abc import Callable
from functools import lru_cache

from app.integrations import require_integration
from app.lib.voice.base import STTProvider, TTSProvider
from app.lib.voice.config import STTProviderType, TTSProviderType


@lru_cache(maxsize=1)
def get_stt_provider() -> STTProvider:
    """Get the configured STT provider based on STT_PROVIDER setting."""
    from app.core.config import settings

    providers: dict[str, Callable[[], STTProvider]] = {
        STTProviderType.DEEPGRAM.value: _get_deepgram_stt,
    }

    provider_factory = providers.get(settings.STT_PROVIDER)
    if not provider_factory:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown STT provider: {settings.STT_PROVIDER}. Available: {available}"
        )

    return provider_factory()


@require_integration("deepgram")
def _get_deepgram_stt() -> STTProvider:
    """Lazy import DeepGram STT provider."""
    from app.integrations.deepgram.stt import DeepGramSTTProvider

    return DeepGramSTTProvider()


@lru_cache(maxsize=1)
def get_tts_provider() -> TTSProvider:
    """Get the configured TTS provider based on TTS_PROVIDER setting."""
    from app.core.config import settings

    providers: dict[str, Callable[[], TTSProvider]] = {
        TTSProviderType.DEEPGRAM.value: _get_deepgram_tts,
    }

    provider_factory = providers.get(settings.TTS_PROVIDER)
    if not provider_factory:
        available = ", ".join(providers.keys())
        raise ValueError(
            f"Unknown TTS provider: {settings.TTS_PROVIDER}. Available: {available}"
        )

    return provider_factory()


@require_integration("deepgram")
def _get_deepgram_tts() -> TTSProvider:
    """Lazy import DeepGram TTS provider."""
    from app.integrations.deepgram.tts import DeepGramTTSProvider

    return DeepGramTTSProvider()
