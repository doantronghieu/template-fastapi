"""DeepGram Speech-to-Text provider implementation.

Implements STTProvider protocol using DeepGram's Nova-3 model.
"""

from collections.abc import AsyncIterator
from typing import Annotated

from deepgram import DeepgramClient, ListenV1Response

from app.integrations.deepgram.client import get_deepgram_client
from app.integrations.deepgram.config import deepgram_settings
from app.lib.voice.base import STTProvider


class DeepGramSTTProvider(STTProvider):
    """DeepGram implementation of STTProvider."""

    def __init__(
        self,
        client: Annotated[DeepgramClient | None, "DeepGram client instance"] = None,
    ) -> None:
        """Initialize provider with DeepGram client."""
        self.client = client or get_deepgram_client()

    async def transcribe_stream(
        self,
        audio_stream: Annotated[
            AsyncIterator[bytes], "Audio bytes stream (linear16, 16kHz)"
        ],
        language: Annotated[str, "Language code (e.g., 'en', 'vi')"] = "en",
    ) -> AsyncIterator[str]:
        """Stream real-time transcription.

        For production use with LiveKit, the agent handles real-time STT
        via DeepGram plugin directly. This is for standalone streaming.
        """
        # Collect audio chunks and transcribe in batches
        # For real-time streaming, use LiveKit agent with DeepGram plugin
        buffer: list[bytes] = []
        buffer_size = 0
        chunk_threshold = 16000 * 2 * 2  # ~2 seconds of 16kHz 16-bit audio

        async for audio_chunk in audio_stream:
            buffer.append(audio_chunk)
            buffer_size += len(audio_chunk)

            if buffer_size >= chunk_threshold:
                audio_data = b"".join(buffer)
                transcript = await self.transcribe_file(audio_data, language)
                if transcript:
                    yield transcript
                buffer = []
                buffer_size = 0

        # Process remaining audio
        if buffer:
            audio_data = b"".join(buffer)
            transcript = await self.transcribe_file(audio_data, language)
            if transcript:
                yield transcript

    async def transcribe_file(
        self,
        audio_data: Annotated[bytes, "Complete audio file bytes"],
        language: Annotated[str, "Language code (e.g., 'en', 'vi')"] = "en",
    ) -> str:
        """Transcribe complete audio file."""
        response: ListenV1Response = await self.client.listen.v1.media.transcribe_file(
            request=audio_data,
            model=deepgram_settings.DEEPGRAM_STT_MODEL,
            language=language,
            punctuate=True,
            smart_format=True,
        )

        # Extract transcript
        return (
            response.results.channels[0].alternatives[0].transcript
            if response.results
            and response.results.channels
            and response.results.channels[0].alternatives
            else ""
        )
