"""Risk-score combination, explanations, and audit evidence."""

from __future__ import annotations

from collections.abc import Iterable

from app.core.config import DetectionSettings
from app.ml.anomaly import MODEL_READY
from app.ml.features import TransactionContext
from app.models.alert import RuleHit
from app.models.enums import RiskLevel


def combine_contributions(contributions: Iterable[float]) -> float:
    """Combine independent signal strengths with a noisy-OR."""

    remaining_normal = 1.0
    for contribution in contributions:
        remaining_normal *= 1.0 - (contribution / 100.0)
    return round((1.0 - remaining_normal) * 100.0, 2)


def risk_level_for_score(score: float) -> RiskLevel:
    if score >= 85:
        return RiskLevel.CRITICAL
    if score >= 65:
        return RiskLevel.HIGH
    if score >= 40:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def combine_scores(
    *,
    rule_score: float,
    ml_score: float,
    settings: DetectionSettings,
    model_available: bool,
) -> float:
    """Blend rule and model scores.

    When the model cannot train (for example, a brand-new deployment with only
    a handful of transactions), the rule weight carries the full score rather
    than silently suppressing alerts.
    """

    if not model_available:
        return round(rule_score, 2)
    return round(
        settings.rule_weight * rule_score
        + settings.ml_weight * ml_score,
        2,
    )


def build_explanation(
    *,
    risk_score: float,
    rule_hits: list[RuleHit],
    ml_score: float,
    model_status: str,
    training_rows: int,
    alert_threshold: float,
    alert_required: bool,
) -> str:
    verdict = "Alert raised" if alert_required else "No alert"
    level = risk_level_for_score(risk_score).value
    rule_summary = (
        " ".join(hit.explanation for hit in rule_hits)
        if rule_hits
        else "No deterministic fraud rules were triggered."
    )
    if model_status == MODEL_READY:
        model_summary = (
            f"IsolationForest anomaly score {ml_score:.1f}/100 "
            f"(percentile against {training_rows:,} transactions)."
        )
    else:
        model_summary = (
            "The anomaly model is not trained yet, so the rule score "
            "carries full weight."
        )
    return (
        f"{verdict}: {level} risk at {risk_score:.1f}/100 "
        f"(alert threshold {alert_threshold:.1f}). "
        f"{rule_summary} {model_summary}"
    )


def build_alert_evidence(
    context: TransactionContext,
    *,
    rule_hits: list[RuleHit],
    rule_score: float,
    ml_score: float,
    risk_score: float,
    model_status: str,
    training_rows: int,
    settings: DetectionSettings,
) -> dict:
    transaction = context.transaction
    model_ready = model_status == MODEL_READY
    return {
        "transaction": {
            "from_account": str(transaction.from_account),
            "to_account": str(transaction.to_account),
            "amount": round(transaction.amount, 2),
            "currency": transaction.currency,
            "timestamp": transaction.timestamp.isoformat(),
            "channel": transaction.channel.value,
            "device_id": transaction.device_id,
            "ip_address": transaction.ip_address,
        },
        "scoring": {
            "rule_score": rule_score,
            "ml_score": round(ml_score, 2),
            "risk_score": risk_score,
            "rule_weight": settings.rule_weight if model_ready else 1.0,
            "ml_weight": settings.ml_weight if model_ready else 0.0,
            "alert_threshold": settings.alert_threshold,
            "model_status": model_status,
            "training_rows": training_rows,
        },
        "rule_evidence": {
            hit.code.value: hit.evidence for hit in rule_hits
        },
    }
