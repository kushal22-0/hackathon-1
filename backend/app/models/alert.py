"""Alert API contracts and detection result schemas."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    computed_field,
    field_validator,
    model_validator,
)

from app.models.enums import AlertStatus, RiskLevel, RuleCode, RuleSeverity


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include a timezone")
    return value.astimezone(UTC)


class RuleHit(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: RuleCode
    name: str
    severity: RuleSeverity
    score_contribution: float = Field(ge=0, le=100)
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)


class Alert(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: UUID
    transaction_id: UUID
    risk_score: float = Field(ge=0, le=100)
    rule_hits: list[RuleHit] = Field(default_factory=list)
    ml_score: float = Field(ge=0, le=100)
    explanation: str
    evidence: dict[str, Any] = Field(default_factory=dict)
    status: AlertStatus = AlertStatus.OPEN
    created_at: datetime
    updated_at: datetime

    @field_validator("created_at", "updated_at")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        return _ensure_aware(value)

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


class AlertSearchQuery(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: AlertStatus | None = None
    transaction_id: UUID | None = None
    min_risk_score: float | None = Field(default=None, ge=0, le=100)
    max_risk_score: float | None = Field(default=None, ge=0, le=100)
    sort_by: Literal["created_at", "risk_score"] = "created_at"
    sort_dir: Literal["asc", "desc"] = "desc"
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=25, ge=1, le=200)

    @model_validator(mode="after")
    def validate_ranges(self) -> AlertSearchQuery:
        if (
            self.min_risk_score is not None
            and self.max_risk_score is not None
            and self.min_risk_score > self.max_risk_score
        ):
            raise ValueError(
                "min_risk_score must be less than or equal to max_risk_score"
            )
        return self


class AlertPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[Alert]
    page: int
    page_size: int
    total: int
    total_pages: int


class DetectionResult(BaseModel):
    """Assessment for one transaction, whether or not an alert was opened."""

    model_config = ConfigDict(extra="forbid")

    transaction_id: UUID
    risk_score: float = Field(ge=0, le=100)
    rule_score: float = Field(ge=0, le=100)
    ml_score: float = Field(ge=0, le=100)
    alert_threshold: float = Field(ge=0, le=100)
    rule_hits: list[RuleHit]
    explanation: str
    alert_required: bool
    alert_created: bool = False
    alert_updated: bool = False
    alert: Alert | None = None
    model_status: str
    training_rows: int

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


class DetectionRunRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    transaction_ids: list[UUID] | None = Field(
        default=None,
        max_length=500,
        description="Explicit transactions to scan; omit to scan the most recent",
    )
    limit: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Number of recent transactions to scan when IDs are omitted",
    )


class DetectionRunResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scanned: int
    alerts_required: int
    alerts_created: int
    alerts_updated: int
    alert_ids: list[UUID]
    model_status: str
    training_rows: int
