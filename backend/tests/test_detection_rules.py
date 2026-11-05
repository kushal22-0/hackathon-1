from __future__ import annotations

from datetime import timedelta

from app.core.config import DetectionSettings
from app.ml.features import TransactionContext, build_transaction_contexts
from app.models.alert import RuleHit
from app.models.enums import RuleCode, RuleSeverity
from app.services.detection_rules import combine_rule_scores, evaluate_rules
from tests.conftest import REFERENCE_TIME, make_transaction

SETTINGS = DetectionSettings()


def _contexts(
    transactions: list,
) -> dict:
    return build_transaction_contexts(
        transactions,
        rapid_window_seconds=SETTINGS.rapid_succession_seconds,
        frequency_window_seconds=(
            SETTINGS.high_frequency_window_minutes * 60
        ),
    )


def _single(transaction) -> TransactionContext:
    return _contexts([transaction])[transaction.id]


def _amount_rule(amount: float) -> RuleHit | None:
    transaction = make_transaction(
        9_000, amount=amount, timestamp=REFERENCE_TIME
    )
    hits = evaluate_rules(_single(transaction), SETTINGS)
    return next(
        (hit for hit in hits if hit.code == RuleCode.LARGE_TRANSFER), None
    )


def test_large_transfer_tiers_and_points() -> None:
    medium = _amount_rule(15_000)
    high = _amount_rule(25_000)
    critical = _amount_rule(45_000)

    assert medium is not None
    assert medium.severity == RuleSeverity.MEDIUM
    assert medium.score_contribution == 70
    assert medium.evidence["multiplier"] == 1.5

    assert high is not None
    assert high.severity == RuleSeverity.HIGH
    assert high.score_contribution == 85

    assert critical is not None
    assert critical.severity == RuleSeverity.CRITICAL
    assert critical.score_contribution == 95


def test_large_transfer_below_threshold_does_not_fire() -> None:
    assert _amount_rule(9_999) is None


def _velocity_transactions(count: int, spacing: timedelta) -> list:
    return [
        make_transaction(
            10_000 + index,
            from_index=0,
            to_index=1,
            amount=100 + index,
            timestamp=REFERENCE_TIME + spacing * index,
        )
        for index in range(count)
    ]


def test_high_frequency_requires_five_transfers_in_ten_minutes() -> None:
    four = _velocity_transactions(4, timedelta(minutes=2))
    assert not any(
        hit.code == RuleCode.HIGH_FREQUENCY
        for hit in evaluate_rules(
            _contexts(four)[four[-1].id], SETTINGS
        )
    )

    five = _velocity_transactions(5, timedelta(minutes=2))
    target = _contexts(five)[five[-1].id]
    hits = evaluate_rules(target, SETTINGS)
    frequency = next(
        hit for hit in hits if hit.code == RuleCode.HIGH_FREQUENCY
    )

    assert frequency.severity == RuleSeverity.HIGH
    assert frequency.score_contribution == 55
    assert frequency.evidence == {
        "transaction_count": 5,
        "window_minutes": 10,
        "threshold": 5,
    }


def test_high_frequency_escalates_at_critical_volume() -> None:
    ten = _velocity_transactions(10, timedelta(minutes=1))
    target = _contexts(ten)[ten[-1].id]
    hits = evaluate_rules(target, SETTINGS)
    frequency = next(
        hit for hit in hits if hit.code == RuleCode.HIGH_FREQUENCY
    )

    assert frequency.severity == RuleSeverity.CRITICAL
    assert frequency.score_contribution == 75


def test_rapid_succession_requires_three_transfers_in_a_minute() -> None:
    two = _velocity_transactions(2, timedelta(seconds=20))
    assert not any(
        hit.code == RuleCode.RAPID_SUCCESSION
        for hit in evaluate_rules(_contexts(two)[two[-1].id], SETTINGS)
    )

    three = _velocity_transactions(3, timedelta(seconds=20))
    target = _contexts(three)[three[-1].id]
    rapid = next(
        hit
        for hit in evaluate_rules(target, SETTINGS)
        if hit.code == RuleCode.RAPID_SUCCESSION
    )

    assert rapid.severity == RuleSeverity.MEDIUM
    assert rapid.score_contribution == 50
    assert rapid.evidence == {
        "transaction_count": 3,
        "window_seconds": 60,
        "threshold": 3,
    }


def test_rapid_succession_escalates_at_critical_volume() -> None:
    six = _velocity_transactions(6, timedelta(seconds=10))
    target = _contexts(six)[six[-1].id]
    hits = evaluate_rules(target, SETTINGS)
    rapid = next(
        hit for hit in hits if hit.code == RuleCode.RAPID_SUCCESSION
    )

    assert rapid.severity == RuleSeverity.HIGH
    assert rapid.score_contribution == 70
    assert any(hit.code == RuleCode.HIGH_FREQUENCY for hit in hits)


def test_rule_scores_combine_without_exceeding_one_hundred() -> None:
    hits = [
        RuleHit(
            code=RuleCode.LARGE_TRANSFER,
            name="Large transfer",
            severity=RuleSeverity.MEDIUM,
            score_contribution=55,
            explanation="large",
        ),
        RuleHit(
            code=RuleCode.RAPID_SUCCESSION,
            name="Rapid succession",
            severity=RuleSeverity.MEDIUM,
            score_contribution=50,
            explanation="rapid",
        ),
    ]

    assert combine_rule_scores(hits) == 77.5
    assert combine_rule_scores([]) == 0
    assert combine_rule_scores(hits + hits) == 94.94
