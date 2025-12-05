from typing import Any
from urllib.parse import quote

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.lib.llm.config import LLMProviderType
from app.lib.voice.config import STTProviderType, TTSProviderType


def _parse_comma_separated_list(v: Any) -> list[str]:
    """Parse comma-separated string to list. Shared by extension/integration validators."""
    if isinstance(v, str):
        if not v.strip():
            return []
        return [x.strip() for x in v.split(",") if x.strip()]
    return v or []


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "0.1.0"

    # FastAPI
    PORT: int = Field(default=8000, description="FastAPI server port")
    APP_ENVIRONMENT: str = Field(
        default="development",
        description="Application environment (development/production)",
    )

    # PostgreSQL
    POSTGRES_USER: str = Field(..., description="PostgreSQL database user")
    POSTGRES_PASSWORD: str = Field(..., description="PostgreSQL database password")
    POSTGRES_DB: str = Field(..., description="PostgreSQL database name")
    POSTGRES_HOST: str = Field(..., description="PostgreSQL database host")
    POSTGRES_PORT: int = Field(..., description="PostgreSQL database port")

    # Database
    DATABASE_ECHO: bool = Field(default=False, description="Enable SQL query logging")

    # Redis Cloud
    REDIS_URL: str = Field(
        ...,
        description="Redis Cloud connection URL (e.g., redis://user:pass@host:port)",
    )

    # Celery
    CELERY_APP_NAME: str = Field(..., description="Celery application name")
    CELERY_TIMEZONE: str = Field(..., description="Timezone for scheduling")
    CELERY_TASK_TRACK_STARTED: bool = Field(..., description="Track when tasks start")
    CELERY_TASK_TIME_LIMIT: int = Field(
        ..., description="Hard time limit in seconds - task killed after this duration"
    )
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(
        ...,
        description="Soft time limit in seconds - exception raised after this duration",
    )
    CELERY_RESULT_EXPIRES: int = Field(
        ..., description="Task result TTL in backend (seconds)"
    )
    CELERY_TASK_ACKS_LATE: bool = Field(
        ..., description="Acknowledge tasks after execution for reliability"
    )
    CELERY_WORKER_PREFETCH_MULTIPLIER: int = Field(
        ..., description="Number of tasks to prefetch per worker"
    )
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(
        ..., description="Restart worker after N tasks to prevent memory leaks"
    )
    FLOWER_PORT: int = Field(..., description="Flower monitoring UI port")

    # LLM
    LLM_PROVIDER: str = Field(
        default=LLMProviderType.LANGCHAIN.value,
        description="LLM provider (e.g., 'langchain', 'litellm')",
    )

    # Voice Providers
    STT_PROVIDER: str = Field(
        default=STTProviderType.DEEPGRAM.value,
        description="Speech-to-Text provider",
    )
    TTS_PROVIDER: str = Field(
        default=TTSProviderType.DEEPGRAM.value,
        description="Text-to-Speech provider",
    )

    # Google Generative AI
    GOOGLE_API_KEY: str = Field(..., description="Google API key for Gemini models")

    # OpenRouter
    OPENROUTER_API_KEY: str = Field(
        default="", description="OpenRouter API key for unified model access"
    )

    # Extensions
    ENABLED_EXTENSIONS: str | list[str] = Field(
        default="",
        description="Comma-separated extensions (e.g., 'ext_a,ext_b') or empty for core only",
    )

    # Integrations (opt-out model: all enabled by default, specify which to disable)
    DISABLED_INTEGRATIONS: str | list[str] = Field(
        default="",
        description="Comma-separated integrations to disable (e.g., 'int_1,int_2')",
    )

    @field_validator("ENABLED_EXTENSIONS", "DISABLED_INTEGRATIONS", mode="before")
    @classmethod
    def parse_comma_separated(cls, v: Any) -> list[str]:
        """Parse comma-separated string to list."""
        return _parse_comma_separated_list(v)

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        extra="allow",
    )

    @property
    def CELERY_TASKS_MODULE(self) -> str:
        """Construct Celery tasks module path from app name."""
        return f"{self.CELERY_APP_NAME}.tasks"

    @property
    def _db_connection_base(self) -> str:
        """Base PostgreSQL connection string with URL-encoded credentials."""
        # URL-encode username and password to handle special characters (@, :, etc.)
        user = quote(self.POSTGRES_USER, safe="")
        password = quote(self.POSTGRES_PASSWORD, safe="")
        return f"{user}:{password}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL from PostgreSQL components.

        Uses URL-encoded credentials to handle special characters.
        For Supabase: Works with Session Pooler and Direct Connection.
        """
        return f"postgresql+asyncpg://{self._db_connection_base}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Construct sync database URL for SQLAdmin (uses psycopg2, not asyncpg)."""
        return f"postgresql+psycopg2://{self._db_connection_base}"

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Construct Celery broker URL from Redis Cloud URL.

        Redis Cloud free tier only supports database 0.
        """
        return self.REDIS_URL

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Construct Celery result backend URL from Redis Cloud URL.

        Redis Cloud free tier only supports database 0.
        """
        return self.REDIS_URL


settings = Settings()
