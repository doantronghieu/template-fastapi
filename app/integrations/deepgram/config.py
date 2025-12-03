"""DeepGram integration configuration.

Environment variables loaded from envs/integrations/deepgram.env
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import get_integration_env_path


class DeepGramSettings(BaseSettings):
    """DeepGram integration settings."""

    DEEPGRAM_API_KEY: str = Field(
        ...,
        description="DeepGram API key from console.deepgram.com",
    )
    DEEPGRAM_STT_MODEL: str = Field(
        default="nova-3",
        description="DeepGram STT model",
    )
    DEEPGRAM_TTS_VOICE: str = Field(
        default="aura-asteria-en",
        description="DeepGram Aura TTS voice model",
    )

    model_config = SettingsConfigDict(
        env_file=get_integration_env_path(__file__),
        extra="ignore",
    )


deepgram_settings = DeepGramSettings()
