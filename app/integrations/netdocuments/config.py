"""NetDocuments integration configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.integrations import generate_integration_env, get_integration_env_path

_env_file_path = get_integration_env_path(__file__)


class NetDocumentsSettings(BaseSettings):
    """NetDocuments API integration settings."""

    NETDOC_CLIENT_ID: str = Field(description="NetDocuments OAuth Client ID")
    NETDOC_CLIENT_SECRET: str = Field(description="NetDocuments OAuth Client Secret")
    NETDOC_TOKEN_URL: str = Field(
        default="https://api.vault.netvoyage.com/v1/OAuth",
        description="NetDocuments OAuth token endpoint",
    )
    NETDOC_ENDPOINT: str = Field(
        default="https://vault.netvoyage.com/v1",
        description="NetDocuments API base endpoint",
    )
    NETDOC_REPOSITORY_ID: str = Field(description="NetDocuments Repository ID")
    NETDOC_CABINET_ID: str = Field(description="NetDocuments Cabinet ID")
    NETDOC_SCOPE: str = Field(default="full", description="NetDocuments OAuth scope")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


generate_integration_env(__file__, NetDocumentsSettings)
netdocuments_settings = NetDocumentsSettings()
