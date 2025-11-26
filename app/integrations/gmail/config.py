"""Gmail integration configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import generate_integration_env, get_integration_env_path

# Pre-generate env file path to ensure it exists before class definition
_env_file_path = get_integration_env_path(__file__)


class GmailSettings(BaseSettings):
    """Gmail IMAP integration settings."""

    GMAIL_EMAIL: str = Field(description="Gmail account email address")
    GMAIL_APP_PASSWORD: str = Field(
        description="App-specific password from Google Account settings"
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


# Generate env file AFTER class definition but BEFORE instantiation
generate_integration_env(__file__, GmailSettings)
gmail_settings = GmailSettings()
