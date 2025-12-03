"""LiveKit Agent configuration.

Agent-specific settings with credentials from integration env files.
Agent-specific vars (FASTAPI_URL, etc.) from envs/workers/voice-agent.env.
"""

from pathlib import Path

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Calculate paths for env files
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
_ENVS_INTEGRATIONS = _PROJECT_ROOT / "envs" / "integrations"
_ENVS_WORKERS = _PROJECT_ROOT / "envs" / "workers"

_ENV_FILES = [
    _ENVS_INTEGRATIONS / "livekit.env",
    _ENVS_INTEGRATIONS / "deepgram.env",
    _ENVS_WORKERS / "voice-agent.env",
]
for _env_file in _ENV_FILES:
    if _env_file.exists():
        load_dotenv(_env_file, override=True)


class AgentSettings(BaseSettings):
    """Agent configuration settings.

    Credentials from integration env files (livekit.env, deepgram.env, etc.).
    Agent-specific settings from envs/workers/voice-agent.env.
    """

    # LiveKit credentials (from envs/integrations/livekit.env)
    LIVEKIT_URL: str = Field(..., description="LiveKit WebSocket URL")
    LIVEKIT_API_KEY: str = Field(..., description="LiveKit API key")
    LIVEKIT_API_SECRET: str = Field(..., description="LiveKit API secret")

    # DeepGram settings (from envs/integrations/deepgram.env)
    DEEPGRAM_API_KEY: str = Field(..., description="DeepGram API key")
    DEEPGRAM_STT_MODEL: str = Field(
        default="nova-3",
        description="DeepGram STT model",
    )
    DEEPGRAM_TTS_VOICE: str = Field(
        default="aura-asteria-en",
        description="DeepGram Aura TTS voice",
    )

    # Agent-specific settings (from envs/workers/voice-agent.env)
    AGENT_NAME: str = Field(
        default="voice-assistant",
        description="Participant identity name for the agent",
    )

    # LLM settings
    LLM_MODEL: str = Field(
        default="gpt-5-nano",
        description="LLM model for voice conversations",
    )
    LLM_MODEL_PROVIDER: str = Field(
        default="openai",
        description="LLM model provider",
    )
    SYSTEM_PROMPT_PATH: str = Field(
        default="app/features/voice/prompts/system.md",
        description="Path to system prompt file (from project root)",
    )

    model_config = SettingsConfigDict(
        env_file=[
            str(_ENVS_INTEGRATIONS / "livekit.env"),
            str(_ENVS_INTEGRATIONS / "deepgram.env"),
            str(_ENVS_WORKERS / "voice-agent.env"),
        ],
        extra="ignore",
    )


agent_settings = AgentSettings()
