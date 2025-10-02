from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "FastAPI Template"
    VERSION: str = "0.1.0"

    class Config:
        case_sensitive = True


settings = Settings()
