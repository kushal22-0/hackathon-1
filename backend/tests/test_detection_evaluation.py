from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import UUID, uuid5

from app.core.config import DetectionSettings
from app.models.alert import DetectionRunRequest
from app.models.enums import Channel
from app.models.transaction import Transaction
from app.repositories.container import seed_memory_store
from app.services.detection import DetectionService
from scripts.generate_demo_data import ID_NAMESPACE, generate_dataset
from tests.conftest import create_test_app

REFERENCE_END = datetime(2026, 10, 31, 23, 59, tzinfo=UTC)


def _to_transaction(index: int, demo) -> Transaction:
    return Transaction(
        id=uuid5(ID_NAMESPACE, f"evaluation-transaction/{index}"),
        from_account=UUID(demo.from_account),
        to_account=UUID(demo.to_account),
        amount=demo.amount,
        currency="USD",
        timestamp=demo.timestamp,
        device_id=demo.device_id,
        ip_address=demo.ip_address,
        channel=Channel(demo.channel),
        label=demo.label,
    )


def test_detection_quality_on_labeled_demo_corpus() -> None:
    _customers, _accounts, demo_transactions = generate_dataset(
        seed=42, total_transactions=1_500, end=REFERENCE_END
    )
    transactions = [
        _to_transaction(index, demo)
        for index, demo in enumerate(demo_transactions)
    ]
    labels = {transaction.id: transaction.label for transaction in transactions}
    patterns = {
        transaction.id: demo.pattern
        for transaction, demo in zip(
            transactions, demo_transactions, strict=True
        )
    }

    app = create_test_app(
        detection=DetectionSettings(ml_estimators=50)
    )
    seed_memory_store(
        app.state.memory_repositories.store,
        transactions=transactions,
    )
    service = DetectionService(
        app.state.memory_repositories.container,
        app.state.settings.detection,
        app.state.model_manager,
    )

    for start in range(0, len(transactions), 500):
        batch = [
            transaction.id
            for transaction in transactions[start : start + 500]
        ]
        service.scan(DetectionRunRequest(transaction_ids=batch))

    alerts = list(app.state.memory_repositories.store.alerts.values())
    alerted_ids = {alert.transaction_id for alert in alerts}
    true_positives = sum(
        1 for transaction_id in alerted_ids if labels[transaction_id] == 1
    )
    fraud_total = sum(labels.values())
    pattern_totals = Counter(patterns.values())
    pattern_hits = Counter(patterns[transaction_id] for transaction_id in alerted_ids)

    assert len(alerts) > 0
    assert true_positives == len(alerts), "Alerts must not flag legitimate rows"
    assert true_positives / fraud_total >= 0.20
    assert pattern_hits["large"] / pattern_totals["large"] >= 0.90
    assert pattern_hits["rapid_fire"] / pattern_totals["rapid_fire"] >= 0.65
    assert pattern_hits["normal"] == 0
