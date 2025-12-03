"""FastAPI dependencies for voice providers.

Provides dependency injection for STT and TTS providers in API endpoints.
"""

from typing import Annotated

from fastapi import Depends

from app.lib.voice.base import STTProvider, TTSProvider
from app.lib.voice.factory import get_stt_provider, get_tts_provider

STTProviderDep = Annotated[STTProvider, Depends(get_stt_provider)]
TTSProviderDep = Annotated[TTSProvider, Depends(get_tts_provider)]
