from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    DEBUG: bool

    HOST: str
    PORT: int

    DATABASE_URL: str

    MEDGEMMA_API_URL: str
    MEDGEMMA_API_KEY: str
    MODEL_NAME: str

    LOG_LEVEL: str

    class Config:
        env_file = ".env"


settings = Settings()