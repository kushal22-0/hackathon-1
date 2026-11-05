"""Typed application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings.

    Values are read from the process environment first, then `backend/.env`.
    The defaults are safe for local development.
    """

    model_config = SettingsConfigDict(
        env_file=BACKEND_DIR / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "FraudNet AI API"
    app_version: str = "0.1.0"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: list[str] = ["http://localhost:5173"]

    # Persistence
    repository_backend: Literal["memory", "postgres"] = "memory"
    database_url: str | None = None

    # Ingestion limits
    max_upload_bytes: int = 10 * 1024 * 1024
    max_ingest_rows: int = 50_000

    @field_validator("database_url", mode="before")
    @classmethod
    def blank_database_url_is_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @property
    def sqlalchemy_database_url(self) -> str:
        """Return a configured database URL or fail with a clear message."""

        if not self.database_url:
            raise ValueError(
                "DATABASE_URL is required when REPOSITORY_BACKEND=postgres"
            )
        return self.database_url


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a process-wide settings instance."""

    return Settings()
