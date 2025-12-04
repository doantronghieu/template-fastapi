"""Mistral integration configuration.

Pydantic settings for Mistral OCR API.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import generate_integration_env, get_integration_env_path


class MistralSettings(BaseSettings):
    """Mistral API settings."""

    MISTRAL_API_KEY: str = Field(
        default="",
        description="Mistral API key",
    )

    MISTRAL_OCR_MODEL: str = Field(
        default="mistral-ocr-latest",
        description="OCR model name",
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=get_integration_env_path(__file__),
        env_file_encoding="utf-8",
        extra="ignore",
    )


# Generate .env template on first import
generate_integration_env(__file__, MistralSettings)

# Singleton instance
mistral_settings = MistralSettings()
