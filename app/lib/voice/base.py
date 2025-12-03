"""Base protocols for voice provider implementations.

Defines the common interfaces that all STT and TTS providers must implement,
enabling runtime provider switching via the Strategy pattern.
"""

from collections.abc import AsyncIterator
from typing import Annotated, Protocol


class STTProvider(Protocol):
    """Protocol defining the interface for Speech-to-Text provider implementations.

    All STT provider implementations must support:
    - Streaming transcription for real-time audio
    - File-based transcription for pre-recorded audio
    """

    async def transcribe_stream(
        self,
        audio_stream: Annotated[
            AsyncIterator[bytes], "Async iterator yielding audio bytes"
        ],
        language: Annotated[str, "Language code (e.g., 'en', 'vi')"] = "en",
    ) -> AsyncIterator[str]:
        """Stream audio, yield transcription chunks in real-time."""
        ...

    async def transcribe_file(
        self,
        audio_data: Annotated[bytes, "Complete audio file bytes"],
        language: Annotated[str, "Language code (e.g., 'en', 'vi')"] = "en",
    ) -> str:
        """Transcribe complete audio file. Returns complete transcription text."""
        ...


class TTSProvider(Protocol):
    """Protocol defining the interface for Text-to-Speech provider implementations.

    All TTS provider implementations must support:
    - Complete synthesis returning full audio
    - Streaming synthesis for real-time audio playback
    """

    async def synthesize(
        self,
        text: Annotated[str, "Text to convert to speech"],
        voice: Annotated[
            str | None, "Voice model identifier (provider-specific)"
        ] = None,
    ) -> bytes:
        """Convert text to audio bytes (typically linear16 PCM at 16kHz)."""
        ...

    async def synthesize_stream(
        self,
        text: Annotated[str, "Text to convert to speech"],
        voice: Annotated[
            str | None, "Voice model identifier (provider-specific)"
        ] = None,
    ) -> AsyncIterator[bytes]:
        """Stream audio chunks for real-time playback."""
        ...
