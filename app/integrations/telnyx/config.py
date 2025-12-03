"""Telnyx integration configuration.

Environment variables loaded from envs/integrations/telnyx.env
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import get_integration_env_path


class TelnyxSettings(BaseSettings):
    """Telnyx integration settings."""

    TELNYX_API_KEY: str = Field(
        ...,
        description="Telnyx API key from portal.telnyx.com",
    )
    TELNYX_API_SECRET: str = Field(
        default="",
        description="Telnyx API secret",
    )
    TELNYX_SIP_TRUNK_ID: str = Field(
        default="",
        description="Telnyx SIP trunk ID for LiveKit integration",
    )
    TELNYX_PHONE_NUMBER: str = Field(
        default="",
        description="Telnyx phone number (E.164 format)",
    )
    TELNYX_WEBHOOK_SECRET: str = Field(
        default="",
        description="Webhook secret for verifying callbacks",
    )

    model_config = SettingsConfigDict(
        env_file=get_integration_env_path(__file__),
        extra="ignore",
    )


telnyx_settings = TelnyxSettings()
