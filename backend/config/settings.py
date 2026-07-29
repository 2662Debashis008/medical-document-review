from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "Medical Document Review API"
    APP_VERSION: str = "1.0.0"

    DEBUG: bool = False

    HOST: str = "127.0.0.1"
    PORT: int = 8000

    DATABASE_URL: str = "sqlite:///./medical_document.db"

    MEDGEMMA_API_URL: str = ""
    MODEL_NAME: str = "medgemma:4b"
    MEDGEMMA_READ_TIMEOUT_SECONDS: float = 240.0
    MEDGEMMA_MAX_TOKENS: int = 1024

    LOG_LEVEL: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        extra="ignore",
    )

    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, value):
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_database_url(cls, value):
        if value == "sqlite:///./medical_document.db":
            return f"sqlite:///{(BASE_DIR / 'medical_document.db').as_posix()}"
        return value


settings = Settings()
