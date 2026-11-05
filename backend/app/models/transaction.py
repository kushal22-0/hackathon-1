"""Transaction API, ingestion, and search contracts."""

from __future__ import annotations

import ipaddress
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from app.models.enums import Channel


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)


def _parse_binary_label(value: object) -> object:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        try:
            return int(value)
        except ValueError:
            return value
    return value


class Transaction(BaseModel):
    """A persisted transaction event."""

    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    from_account: UUID
    to_account: UUID
    amount: float = Field(gt=0, le=1_000_000_000_000)
    currency: str = "USD"
    timestamp: datetime
    device_id: str | None = None
    ip_address: str | None = None
    channel: Channel = Channel.API
    label: Literal[0, 1] | None = None
    created_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return value

    @field_validator("timestamp", "created_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime | None) -> datetime | None:
        return _ensure_aware(value) if value is not None else None


class TransactionCsvRow(BaseModel):
    """One validated row from an uploaded CSV file."""

    model_config = ConfigDict(
        extra="ignore",
        str_strip_whitespace=True,
    )

    id: UUID | None = None
    from_account: UUID
    to_account: UUID
    amount: float = Field(gt=0, le=1_000_000_000_000)
    currency: str = "USD"
    timestamp: datetime
    device_id: str | None = Field(default=None, max_length=128)
    ip_address: str | None = Field(default=None, max_length=64)
    channel: Channel = Channel.API
    label: Literal[0, 1] | None = None

    @field_validator("id", "device_id", "ip_address", "label", mode="before")
    @classmethod
    def empty_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, value: object) -> str:
        text = str(value or "USD").strip().upper()
        if len(text) != 3 or not text.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return text

    @field_validator("channel", mode="before")
    @classmethod
    def normalize_channel(cls, value: object) -> str:
        return str(value or "api").strip().lower()

    @field_validator("label", mode="before")
    @classmethod
    def parse_label(cls, value: object) -> object:
        return _parse_binary_label(value)

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(ipaddress.ip_address(value))

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _ensure_aware(value)

    @model_validator(mode="after")
    def validate_distinct_accounts(self) -> TransactionCsvRow:
        if self.from_account == self.to_account:
            raise ValueError("from_account and to_account must differ")
        return self


class IngestRowError(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row: int = Field(description="1-based CSV line number (header is line 1)")
    field: str | None = None
    message: str


class TransactionIngestResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    accepted: int
    filename: str
    message: str = "Transactions ingested successfully"


class TransactionSearchQuery(BaseModel):
    """Validated search filters. FastAPI flattens these into query parameters."""

    model_config = ConfigDict(extra="forbid")

    account_id: UUID | None = Field(
        default=None, description="Match either the source or destination account"
    )
    from_account: UUID | None = None
    to_account: UUID | None = None
    min_amount: float | None = Field(default=None, ge=0)
    max_amount: float | None = Field(default=None, ge=0)
    start_time: datetime | None = None
    end_time: datetime | None = None
    channel: Channel | None = None
    label: Literal[0, 1] | None = None
    device_id: str | None = Field(default=None, max_length=128)
    ip_address: str | None = Field(default=None, max_length=64)
    sort_by: Literal["timestamp", "amount"] = "timestamp"
    sort_dir: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)

    @field_validator("start_time", "end_time")
    @classmethod
    def normalize_time(cls, value: datetime | None) -> datetime | None:
        return _ensure_aware(value) if value is not None else None

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(ipaddress.ip_address(value))

    @field_validator("label", mode="before")
    @classmethod
    def parse_label(cls, value: object) -> object:
        return _parse_binary_label(value)

    @model_validator(mode="after")
    def validate_ranges(self) -> TransactionSearchQuery:
        if (
            self.min_amount is not None
            and self.max_amount is not None
            and self.min_amount > self.max_amount
        ):
            raise ValueError("min_amount must be less than or equal to max_amount")
        if (
            self.start_time is not None
            and self.end_time is not None
            and self.start_time > self.end_time
        ):
            raise ValueError("start_time must be earlier than or equal to end_time")
        return self


class TransactionPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Transaction]
    page: int
    page_size: int
    total: int
    total_pages: int

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
