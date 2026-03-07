from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "IRIS API"
    DEBUG: bool = True

    DATABASE_URL: str = Field(
        default="postgresql+psycopg2://silver:silverpass@db:5432/appdb"
    )
    REDIS_URL: str = Field(default="redis://redis:6379/0")

    JWT_SECRET_KEY: str = Field(default="change_this_in_env_now")
    JWT_ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, gt=0)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return self.DATABASE_URL

    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET_KEY


settings = Settings()
