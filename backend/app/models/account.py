"""Pydantic account and customer contracts."""

from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.enums import RiskLevel


class Customer(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    external_id: str
    full_name: str
    email: str | None = None
    phone: str | None = None
    country: str = "US"
    risk_level: RiskLevel = RiskLevel.LOW
    created_at: datetime | None = None


class Account(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    customer_id: UUID
    account_number: str
    account_type: str = "checking"
    currency: str = "USD"
    status: str = "active"
    balance: float = 0
    opened_at: date
    created_at: datetime | None = None

    @field_validator("currency")
    @classmethod
    def normalize_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter ISO code")
        return value
