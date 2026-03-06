from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "IRIS API"
    DEBUG: bool = True

    DATABASE_URL: str = "postgresql+psycopg2://silver:silverpass@db:5432/appdb"
    REDIS_URL: str = "redis://redis:6379/0"

    JWT_SECRET_KEY: str = "change_this_secret"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


settings = Settings()