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

    # Redis
    REDIS_HOST: str = Field(..., description="Redis host")
    REDIS_PORT: int = Field(..., description="Redis port")

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

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
    )

    @property
    def CELERY_TASKS_MODULE(self) -> str:
        """Construct Celery tasks module path from app name."""
        return f"{self.CELERY_APP_NAME}.tasks"

    @property
    def _db_connection_base(self) -> str:
        """Base PostgreSQL connection string."""
        return f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def DATABASE_URL(self) -> str:
        """Construct async database URL from PostgreSQL components."""
        return f"postgresql+asyncpg://{self._db_connection_base}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        """Construct sync database URL for SQLAlchemy Admin."""
        return f"postgresql+psycopg2://{self._db_connection_base}"

    @property
    def CELERY_BROKER_URL(self) -> str:
        """Construct Celery broker URL from Redis components."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @property
    def CELERY_RESULT_BACKEND(self) -> str:
        """Construct Celery result backend URL from Redis components."""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"


settings = Settings()
