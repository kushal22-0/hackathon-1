"""Typed application configuration loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]


class DetectionSettings(BaseModel):
    """Rule thresholds, score weights, and ML training parameters.

    Environment variables use the nested delimiter, for example:
    ``DETECTION__LARGE_TRANSFER_THRESHOLD=10000``.
    """

    model_config = ConfigDict(extra="forbid")

    # Rule thresholds
    large_transfer_threshold: float = Field(default=10_000, gt=0)
    large_transfer_high_multiplier: float = Field(default=2.0, gt=1)
    large_transfer_critical_multiplier: float = Field(default=4.0, gt=1)
    high_frequency_count: int = Field(default=5, ge=2)
    high_frequency_window_minutes: int = Field(default=10, ge=1)
    high_frequency_critical_multiplier: float = Field(default=2.0, ge=1)
    rapid_succession_count: int = Field(default=3, ge=2)
    rapid_succession_seconds: int = Field(default=60, ge=1)
    rapid_succession_critical_multiplier: float = Field(default=2.0, ge=1)

    # Rule score contributions
    large_transfer_points: float = Field(default=70, ge=0, le=100)
    large_transfer_high_points: float = Field(default=85, ge=0, le=100)
    large_transfer_critical_points: float = Field(default=95, ge=0, le=100)
    high_frequency_points: float = Field(default=55, ge=0, le=100)
    high_frequency_critical_points: float = Field(default=75, ge=0, le=100)
    rapid_succession_points: float = Field(default=50, ge=0, le=100)
    rapid_succession_critical_points: float = Field(default=70, ge=0, le=100)

    # Combination and alerting
    rule_weight: float = Field(default=0.60, ge=0, le=1)
    ml_weight: float = Field(default=0.40, ge=0, le=1)
    alert_threshold: float = Field(default=65, ge=0, le=100)

    # IsolationForest
    ml_contamination: float = Field(default=0.05, gt=0, lt=0.5)
    ml_estimators: int = Field(default=200, ge=10, le=1_000)
    ml_random_state: int = 42
    ml_min_training_rows: int = Field(default=50, ge=10)
    ml_max_training_rows: int = Field(default=10_000, ge=50)

    # Detection batch limits
    max_batch_size: int = Field(default=500, ge=1, le=5_000)

    @model_validator(mode="after")
    def validate_combinations(self) -> DetectionSettings:
        if abs((self.rule_weight + self.ml_weight) - 1.0) > 1e-6:
            raise ValueError("rule_weight and ml_weight must sum to 1.0")
        if self.large_transfer_high_multiplier >= self.large_transfer_critical_multiplier:
            raise ValueError(
                "large_transfer_high_multiplier must be less than "
                "large_transfer_critical_multiplier"
            )
        if self.high_frequency_critical_multiplier < 1:
            raise ValueError("high_frequency_critical_multiplier must be >= 1")
        if self.rapid_succession_critical_multiplier < 1:
            raise ValueError("rapid_succession_critical_multiplier must be >= 1")
        return self


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
        env_nested_delimiter="__",
    )

    app_name: str = "NexGuard AI API"
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

    # Account risk profiles
    account_profile_max_transactions: int = Field(
        default=5_000, ge=100, le=50_000
    )

    detection: DetectionSettings = Field(default_factory=DetectionSettings)

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
