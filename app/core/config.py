from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "0.1.0"

    # PostgreSQL
    POSTGRES_USER: str = Field(..., description="PostgreSQL database user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL database password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(..., description="PostgreSQL database host")
    POSTGRES_PORT: int = Field(..., description="PostgreSQL database port")

    # Database
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL query logging")

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
    )

    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from PostgreSQL components."""
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"


settings = Settings()
