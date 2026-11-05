"""Pydantic account and customer contracts."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
)

from app.models.enums import RiskLevel, RuleSeverity


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


class RiskSignal(BaseModel):
    """One explainable contribution to an account's risk score."""

    model_config = ConfigDict(extra="forbid")

    code: str
    name: str
    severity: RuleSeverity
    score_contribution: float = Field(ge=0, le=100)
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class AccountRiskProfile(BaseModel):
    """Live risk view for one account, computed from activity and alerts."""

    model_config = ConfigDict(extra="forbid")

    account: Account
    customer: Customer | None = None
    risk_score: float = Field(ge=0, le=100)
    signals: list[RiskSignal] = Field(default_factory=list)
    explanation: str

    # Activity metrics
    transaction_count: int
    sent_count: int
    received_count: int
    sent_amount: float
    received_amount: float
    net_flow: float
    counterparty_count: int
    first_transaction_at: datetime | None = None
    last_transaction_at: datetime | None = None

    # Alert exposure
    alert_count: int
    active_alert_count: int
    max_active_alert_risk_score: float | None = None
    rule_hit_counts: dict[str, int] = Field(default_factory=dict)

    generated_at: datetime

    @computed_field
    @property
    def risk_level(self) -> RiskLevel:
        if self.risk_score >= 85:
            return RiskLevel.CRITICAL
        if self.risk_score >= 65:
            return RiskLevel.HIGH
        if self.risk_score >= 40:
            return RiskLevel.MEDIUM
        return RiskLevel.LOW
