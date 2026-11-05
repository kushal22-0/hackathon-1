"""Shared enumerations used by API contracts and services."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    """String-valued enum that serializes as its value."""

    def __str__(self) -> str:
        return self.value


class Channel(StrEnum):
    MOBILE = "mobile"
    WEB = "web"
    ATM = "atm"
    BRANCH = "branch"
    API = "api"
    WIRE = "wire"
    UPI = "upi"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(StrEnum):
    OPEN = "open"
    TRIAGED = "triaged"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"


class CaseStatus(StrEnum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    PENDING_REVIEW = "pending_review"
    CLOSED = "closed"


class FraudOutcome(StrEnum):
    FRAUD = "fraud"
    LEGITIMATE = "legitimate"
    INCONCLUSIVE = "inconclusive"


class UserRole(StrEnum):
    ADMIN = "admin"
    INVESTIGATOR = "investigator"
