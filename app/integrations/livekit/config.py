"""LiveKit integration configuration.

Environment variables loaded from envs/integrations/livekit.env
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import get_integration_env_path


class LiveKitSettings(BaseSettings):
    """LiveKit integration settings."""

    LIVEKIT_API_KEY: str = Field(
        ...,
        description="LiveKit API key from cloud.livekit.io",
    )
    LIVEKIT_API_SECRET: str = Field(
        ...,
        description="LiveKit API secret from cloud.livekit.io",
    )
    LIVEKIT_URL: str = Field(
        ...,
        description="LiveKit WebSocket URL (e.g., wss://your-project.livekit.cloud)",
    )
    BACKEND_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API URL for test client",
    )

    model_config = SettingsConfigDict(
        env_file=get_integration_env_path(__file__),
        extra="ignore",
    )

    @property
    def http_url(self) -> str:
        """Convert WebSocket URL to HTTP URL for API calls."""
        return self.LIVEKIT_URL.replace("wss://", "https://")

    @property
    def sip_host(self) -> str:
        """Get SIP host from WebSocket URL."""
        return self.LIVEKIT_URL.replace("wss://", "")

    def get_sip_uri(self, room_name: str) -> str:
        """Generate SIP URI for transferring calls (sip:room@host)."""
        return f"sip:{room_name}@{self.sip_host}"


livekit_settings = LiveKitSettings()
