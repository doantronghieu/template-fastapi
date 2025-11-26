"""Salesforce integration configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import generate_integration_env, get_integration_env_path

_env_file_path = get_integration_env_path(__file__)


class SalesforceSettings(BaseSettings):
    """Salesforce API integration settings."""

    SALESFORCE_DOMAIN: str = Field(
        description="Salesforce domain (e.g., 'company.my' for company.my.salesforce.com)"
    )
    SALESFORCE_CONSUMER_KEY: str = Field(
        description="Consumer Key from Connected App"
    )
    SALESFORCE_CONSUMER_SECRET: str = Field(
        description="Consumer Secret from Connected App"
    )
    # Optional: Only needed for Username-Password Flow (legacy)
    SALESFORCE_USERNAME: str = Field(
        default="", description="Salesforce username (optional, for legacy flow)"
    )
    SALESFORCE_PASSWORD: str = Field(
        default="", description="Salesforce password (optional, for legacy flow)"
    )

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


generate_integration_env(__file__, SalesforceSettings)
salesforce_settings = SalesforceSettings()
