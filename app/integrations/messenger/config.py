"""Messenger integration configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import generate_integration_env, get_integration_env_path

# Pre-generate env file path to ensure it exists before class definition
_env_file_path = get_integration_env_path(__file__)


class MessengerSettings(BaseSettings):
    """Facebook Messenger integration settings."""

    FACEBOOK_PAGE_ACCESS_TOKEN: str = Field(
        description="Facebook Page Access Token for sending messages"
    )
    FACEBOOK_VERIFY_TOKEN: str = Field(
        description="Custom token for webhook verification"
    )
    FACEBOOK_APP_SECRET: str = Field(
        description="Facebook App Secret for signature verification"
    )
    FACEBOOK_GRAPH_API_VERSION: str = Field(
        default="v24.0", description="Facebook Graph API version"
    )
    FACEBOOK_RATE_LIMIT_MESSAGES_PER_MINUTE: int = Field(
        default=10, description="Max messages per minute per user"
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


# Generate env file AFTER class definition but BEFORE instantiation
generate_integration_env(__file__, MessengerSettings)
messenger_settings = MessengerSettings()
