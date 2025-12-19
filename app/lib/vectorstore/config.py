"""Vectorstore configuration."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.autodiscover import ModuleType, generate_module_env, get_module_env_path

_env_file_path = get_module_env_path(ModuleType.LIB, __file__)


class VectorStoreSettings(BaseSettings):
    """Qdrant vectorstore settings."""

    QDRANT_URL: str = Field(description="Qdrant cluster endpoint URL")
    QDRANT_API_KEY: str = Field(description="Qdrant API key")
    QDRANT_TIMEOUT: int = Field(default=10, description="Request timeout in seconds")
    QDRANT_PREFER_GRPC: bool = Field(default=False, description="Use gRPC instead of REST")
    QDRANT_DEFAULT_DIMENSION: int = Field(default=1536, description="Default vector dimension")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=_env_file_path,
        extra="allow",
    )


generate_module_env(ModuleType.LIB, __file__, VectorStoreSettings)
vectorstore_settings = VectorStoreSettings()
