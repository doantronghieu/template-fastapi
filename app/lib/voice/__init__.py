"""Voice provider abstraction layer.

Defines interfaces for Speech-to-Text (STT) and Text-to-Speech (TTS) providers,
enabling runtime provider switching via the Strategy pattern.
"""

from app.lib.voice.base import STTProvider, TTSProvider
from app.lib.voice.factory import get_stt_provider, get_tts_provider
from app.lib.voice.schemas.dto import SynthesisResult, TranscriptionResult

__all__ = [
    "STTProvider",
    "TTSProvider",
    "SynthesisResult",
    "TranscriptionResult",
    "get_stt_provider",
    "get_tts_provider",
]
