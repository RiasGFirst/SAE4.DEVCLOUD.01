from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Voir https://tortoise.github.io/databases.html
    DB_URL: str = "sqlite:///./test.db"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
