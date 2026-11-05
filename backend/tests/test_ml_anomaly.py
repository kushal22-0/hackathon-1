from __future__ import annotations

import math
from datetime import timedelta

from app.core.config import DetectionSettings
from app.ml.anomaly import (
    MODEL_INSUFFICIENT_DATA,
    MODEL_READY,
    AnomalyModelManager,
)
from app.ml.features import (
    FEATURE_NAMES,
    build_transaction_contexts,
    feature_vector,
)
from tests.conftest import REFERENCE_TIME, make_transaction

FEATURE_CONTEXTS = build_transaction_contexts(
    [
        make_transaction(
            1,
            from_index=0,
            to_index=1,
            amount=100,
            timestamp=REFERENCE_TIME,
            device_id="shared-device",
            ip_address="198.51.100.50",
        ),
        make_transaction(
            2,
            from_index=2,
            to_index=1,
            amount=200,
            timestamp=REFERENCE_TIME + timedelta(seconds=10),
            device_id="shared-device",
            ip_address="198.51.100.50",
        ),
        make_transaction(
            3,
            from_index=0,
            to_index=3,
            amount=300,
            timestamp=REFERENCE_TIME + timedelta(seconds=20),
            device_id="shared-device",
            ip_address="198.51.100.50",
        ),
    ],
    rapid_window_seconds=60,
    frequency_window_seconds=600,
)


def test_context_counts_velocity_and_shared_identities() -> None:
    first = FEATURE_CONTEXTS[make_transaction(1).id]
    second = FEATURE_CONTEXTS[make_transaction(2).id]
    third = FEATURE_CONTEXTS[make_transaction(3).id]

    assert first.sender_prior_count == 0
    assert first.sender_count_rapid == 1

    assert second.receiver_count_1h == 2
    assert second.receiver_unique_senders_24h == 2

    assert third.sender_prior_count == 1
    assert third.sender_count_rapid == 2
    assert third.sender_count_frequency == 2
    assert third.seconds_since_sender_previous == 20
    assert third.device_distinct_senders == 2
    assert third.ip_distinct_senders == 2


def test_feature_vector_is_finite_and_ordered() -> None:
    values = feature_vector(FEATURE_CONTEXTS[make_transaction(3).id])

    assert len(values) == len(FEATURE_NAMES)
    assert all(math.isfinite(value) for value in values)
    assert values[0] == math.log1p(300)


def _normal_transactions() -> list:
    return [
        make_transaction(
            index,
            from_index=index % 5,
            to_index=(index + 1) % 5,
            amount=100 + index % 10,
            timestamp=REFERENCE_TIME - timedelta(hours=200 - index),
            device_id=f"device-{index % 5}",
            ip_address=f"192.0.2.{index % 5 + 1}",
        )
        for index in range(120)
    ]


def _burst_transactions() -> list:
    start = REFERENCE_TIME - timedelta(minutes=10)
    return [
        make_transaction(
            500 + index,
            from_index=0,
            to_index=(index % 4) + 1,
            amount=50,
            timestamp=start + timedelta(seconds=index * 5),
            device_id="burst-device",
            ip_address="198.51.100.200",
        )
        for index in range(8)
    ]


def test_isolation_forest_returns_bounded_scores_and_flags_burst() -> None:
    normal = _normal_transactions()
    burst = _burst_transactions()
    contexts = build_transaction_contexts(
        normal + burst,
        rapid_window_seconds=60,
        frequency_window_seconds=600,
    )
    manager = AnomalyModelManager(
        DetectionSettings(ml_estimators=50, ml_min_training_rows=50)
    )

    evaluation = manager.evaluate(
        [contexts[transaction.id] for transaction in normal],
        [contexts[transaction.id] for transaction in burst],
    )

    assert evaluation.status == MODEL_READY
    assert evaluation.training_rows == 120
    assert set(evaluation.scores) == {transaction.id for transaction in burst}
    assert all(0 <= score <= 100 for score in evaluation.scores.values())
    assert max(evaluation.scores.values()) >= 80
    assert sum(
        1 for score in evaluation.scores.values() if score >= 75
    ) >= 4

    repeated = manager.evaluate(
        [contexts[transaction.id] for transaction in normal],
        [contexts[transaction.id] for transaction in burst],
    )
    assert repeated.scores == evaluation.scores


def test_isolation_forest_reports_insufficient_training_data() -> None:
    normal = _normal_transactions()[:10]
    contexts = build_transaction_contexts(
        normal,
        rapid_window_seconds=60,
        frequency_window_seconds=600,
    )
    manager = AnomalyModelManager(
        DetectionSettings(ml_estimators=50, ml_min_training_rows=50)
    )

    evaluation = manager.evaluate(
        [contexts[transaction.id] for transaction in normal],
        [contexts[transaction.id] for transaction in normal],
    )

    assert evaluation.status == MODEL_INSUFFICIENT_DATA
    assert evaluation.training_rows == 10
    assert set(evaluation.scores.values()) == {0.0}
