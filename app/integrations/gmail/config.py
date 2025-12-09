"""Gmail integration configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.autodiscover import ModuleType, generate_module_env, get_module_env_path

_env_file_path = get_module_env_path(ModuleType.INTEGRATIONS, __file__)


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


generate_module_env(ModuleType.INTEGRATIONS, __file__, GmailSettings)
gmail_settings = GmailSettings()
