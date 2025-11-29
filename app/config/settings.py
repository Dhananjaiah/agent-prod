"""Configuration management using pydantic-settings."""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Environment
    app_env: Literal["local", "staging", "production"] = "local"

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/insurance_db"

    # LLM Configuration
    openai_api_key: str = ""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Logging
    log_level: str = "INFO"

    @property
    def sync_database_url(self) -> str:
        """Return synchronous database URL for migrations and seeding."""
        return self.database_url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.app_env == "production"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
