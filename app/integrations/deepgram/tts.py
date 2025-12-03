"""DeepGram Text-to-Speech provider implementation.

Implements TTSProvider protocol using DeepGram's Aura voices.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from deepgram import DeepgramClient

from app.integrations.deepgram.client import get_deepgram_client
from app.integrations.deepgram.config import deepgram_settings
from app.lib.voice.base import TTSProvider


class DeepGramTTSProvider(TTSProvider):
    """DeepGram implementation of TTSProvider."""

    def __init__(
        self,
        client: Annotated[DeepgramClient | None, "DeepGram client instance"] = None,
    ) -> None:
        """Initialize provider with DeepGram client."""
        self.client = client or get_deepgram_client()

    async def synthesize(
        self,
        text: Annotated[str, "Text to convert to speech"],
        voice: Annotated[
            str | None, "Aura voice model (e.g., 'aura-asteria-en')"
        ] = None,
    ) -> bytes:
        """Convert text to audio bytes (linear16 PCM at 24kHz)."""
        audio_chunks: list[bytes] = []
        async for chunk in self.client.speak.v1.audio.generate(
            text=text,
            model=voice or deepgram_settings.DEEPGRAM_TTS_VOICE,
            encoding="linear16",
            sample_rate=24000,
        ):
            audio_chunks.append(chunk)

        return b"".join(audio_chunks)

    async def synthesize_stream(
        self,
        text: Annotated[str, "Text to convert to speech"],
        voice: Annotated[
            str | None, "Aura voice model (e.g., 'aura-asteria-en')"
        ] = None,
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks for real-time playback.

        For production use with LiveKit, the agent handles TTS streaming
        via plugins directly. This is for standalone streaming.
        """
        async for chunk in self.client.speak.v1.audio.generate(
            text=text,
            model=voice or deepgram_settings.DEEPGRAM_TTS_VOICE,
            encoding="linear16",
            sample_rate=24000,
        ):
            yield chunk
