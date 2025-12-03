"""Voice provider configuration types.

Defines provider type enums used for configuration and factory selection.
"""

from enum import Enum


class STTProviderType(str, Enum):
    """Available Speech-to-Text providers."""

    DEEPGRAM = "deepgram"
    # Future providers:
    # WHISPER = "whisper"
    # ASSEMBLY_AI = "assemblyai"


class TTSProviderType(str, Enum):
    """Available Text-to-Speech providers."""

    DEEPGRAM = "deepgram"
    # Future providers:
    # ELEVEN_LABS = "elevenlabs"
    # OPENAI = "openai"
