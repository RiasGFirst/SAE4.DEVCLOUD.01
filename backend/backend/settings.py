from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    # Voir https://tortoise.github.io/databases.html
    DB_URL: str = Field(validation_alias="DB_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

settings = Settings()  # pyright: ignore[reportCallIssue]
