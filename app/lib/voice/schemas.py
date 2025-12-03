"""Voice provider schemas.

Common data structures used across voice providers.
"""

from pydantic import BaseModel, Field


class TranscriptionResult(BaseModel):
    """Result from speech-to-text transcription."""

    text: str = Field(..., description="Transcribed text from audio")


class SynthesisResult(BaseModel):
    """Result from text-to-speech synthesis."""

    audio_data: bytes = Field(..., description="Synthesized audio bytes (linear16 PCM)")
