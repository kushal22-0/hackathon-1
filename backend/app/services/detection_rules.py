"""Deterministic fraud rules evaluated against point-in-time behavior."""

from __future__ import annotations

from app.core.config import DetectionSettings
from app.ml.features import TransactionContext
from app.models.alert import RuleHit
from app.models.enums import RuleCode, RuleSeverity


def _money(value: float) -> str:
    return f"${value:,.2f}"


def evaluate_rules(
    context: TransactionContext, settings: DetectionSettings
) -> list[RuleHit]:
    hits: list[RuleHit] = []

    large_transfer = _evaluate_large_transfer(context, settings)
    if large_transfer is not None:
        hits.append(large_transfer)

    high_frequency = _evaluate_high_frequency(context, settings)
    if high_frequency is not None:
        hits.append(high_frequency)

    rapid_succession = _evaluate_rapid_succession(context, settings)
    if rapid_succession is not None:
        hits.append(rapid_succession)

    return hits


def combine_rule_scores(hits: list[RuleHit]) -> float:
    """Combine independent rule strengths with a noisy-OR.

    Two moderate rules should outweigh either rule alone without allowing the
    score to exceed 100.
    """

    remaining_normal = 1.0
    for hit in hits:
        remaining_normal *= 1.0 - (hit.score_contribution / 100.0)
    return round((1.0 - remaining_normal) * 100.0, 2)


def _evaluate_large_transfer(
    context: TransactionContext, settings: DetectionSettings
) -> RuleHit | None:
    amount = context.transaction.amount
    threshold = settings.large_transfer_threshold
    if amount < threshold:
        return None

    multiplier = amount / threshold
    if multiplier >= settings.large_transfer_critical_multiplier:
        severity = RuleSeverity.CRITICAL
        points = settings.large_transfer_critical_points
    elif multiplier >= settings.large_transfer_high_multiplier:
        severity = RuleSeverity.HIGH
        points = settings.large_transfer_high_points
    else:
        severity = RuleSeverity.MEDIUM
        points = settings.large_transfer_points

    return RuleHit(
        code=RuleCode.LARGE_TRANSFER,
        name="Large transfer",
        severity=severity,
        score_contribution=points,
        explanation=(
            f"Transfer of {_money(amount)} is {multiplier:.2f}x the "
            f"{_money(threshold)} large-transfer threshold."
        ),
        evidence={
            "amount": round(amount, 2),
            "threshold": round(threshold, 2),
            "multiplier": round(multiplier, 2),
        },
    )


def _evaluate_high_frequency(
    context: TransactionContext, settings: DetectionSettings
) -> RuleHit | None:
    count = context.sender_count_frequency
    if count < settings.high_frequency_count:
        return None

    critical_count = (
        settings.high_frequency_count
        * settings.high_frequency_critical_multiplier
    )
    if count >= critical_count:
        severity = RuleSeverity.CRITICAL
        points = settings.high_frequency_critical_points
    else:
        severity = RuleSeverity.HIGH
        points = settings.high_frequency_points

    return RuleHit(
        code=RuleCode.HIGH_FREQUENCY,
        name="High transaction frequency",
        severity=severity,
        score_contribution=points,
        explanation=(
            f"{count} outbound transfers from this account within "
            f"{settings.high_frequency_window_minutes} minutes "
            f"(threshold: {settings.high_frequency_count})."
        ),
        evidence={
            "transaction_count": count,
            "window_minutes": settings.high_frequency_window_minutes,
            "threshold": settings.high_frequency_count,
        },
    )


def _evaluate_rapid_succession(
    context: TransactionContext, settings: DetectionSettings
) -> RuleHit | None:
    count = context.sender_count_rapid
    if count < settings.rapid_succession_count:
        return None

    critical_count = (
        settings.rapid_succession_count
        * settings.rapid_succession_critical_multiplier
    )
    if count >= critical_count:
        severity = RuleSeverity.HIGH
        points = settings.rapid_succession_critical_points
    else:
        severity = RuleSeverity.MEDIUM
        points = settings.rapid_succession_points

    return RuleHit(
        code=RuleCode.RAPID_SUCCESSION,
        name="Rapid succession",
        severity=severity,
        score_contribution=points,
        explanation=(
            f"{count} outbound transfers from this account within "
            f"{settings.rapid_succession_seconds} seconds "
            f"(threshold: {settings.rapid_succession_count})."
        ),
        evidence={
            "transaction_count": count,
            "window_seconds": settings.rapid_succession_seconds,
            "threshold": settings.rapid_succession_count,
        },
    )
