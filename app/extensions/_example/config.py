"""Extension-specific configuration.

This demonstrates how to create extension-specific settings that load from
a separate .env file, keeping extension configuration isolated from core.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.extensions import generate_extension_env, get_extension_env_path


class ExampleExtensionSettings(BaseSettings):
    """Settings specific to the example extension."""

    EXAMPLE_API_KEY: str = Field(..., description="API key for external service")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=get_extension_env_path(__file__),
        env_file_encoding="utf-8",
        extra="allow",
    )


# Generate .env file if it doesn't exist
generate_extension_env(__file__, ExampleExtensionSettings)

# Singleton instance - import this in your extension modules
extension_settings = ExampleExtensionSettings()
