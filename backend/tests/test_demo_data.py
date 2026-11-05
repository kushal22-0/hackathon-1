from __future__ import annotations

from collections import Counter, defaultdict
from datetime import UTC, datetime

import networkx as nx

from scripts.generate_demo_data import FRAUD_TRANSACTION_COUNT, generate_dataset

REFERENCE_END = datetime(2026, 10, 31, 23, 59, tzinfo=UTC)


def test_demo_dataset_has_required_volume_and_ground_truth() -> None:
    _customers, _accounts, transactions = generate_dataset(
        seed=42, end=REFERENCE_END
    )

    assert len(transactions) == 5_000
    assert sum(transaction.label for transaction in transactions) == (
        FRAUD_TRANSACTION_COUNT
    )
    assert all(transaction.label in (0, 1) for transaction in transactions)
    assert all(
        transaction.from_account != transaction.to_account
        for transaction in transactions
    )
    assert all(transaction.amount > 0 for transaction in transactions)


def test_injected_patterns_are_present() -> None:
    _customers, _accounts, transactions = generate_dataset(
        seed=42, end=REFERENCE_END
    )
    patterns = Counter(transaction.pattern for transaction in transactions)

    assert patterns["circular"] == 48
    assert patterns["fan_in"] == 80
    assert patterns["fan_in_consolidation"] == 10
    assert patterns["fan_out"] == 80
    assert patterns["rapid_fire"] == 80
    assert patterns["large"] == 52
    assert patterns["shared_identity"] == 150

    circular_graph = nx.DiGraph()
    for transaction in transactions:
        if transaction.pattern == "circular":
            circular_graph.add_edge(
                transaction.from_account, transaction.to_account
            )
    assert nx.simple_cycles(circular_graph), "Expected circular fund flows"

    inbound = Counter()
    outbound = Counter()
    for transaction in transactions:
        if transaction.pattern in {"fan_in", "fan_in_consolidation"}:
            inbound[transaction.to_account] += 1
            outbound[transaction.from_account] += 1
    assert max(inbound.values()) >= 8

    outbound.clear()
    for transaction in transactions:
        if transaction.pattern == "fan_out":
            outbound[transaction.from_account] += 1
    assert max(outbound.values()) >= 8

    burst_sizes = Counter(
        transaction.from_account
        for transaction in transactions
        if transaction.pattern == "rapid_fire"
    )
    assert max(burst_sizes.values()) == 8

    transaction_counts = defaultdict(int)
    devices_by_account = defaultdict(set)
    for transaction in transactions:
        if transaction.pattern == "shared_identity":
            transaction_counts[transaction.device_id] += 1
            devices_by_account[transaction.device_id].add(
                transaction.from_account
            )
    assert max(transaction_counts.values()) >= 6
    assert any(
        len(accounts) >= 3 for accounts in devices_by_account.values()
    )

    assert all(
        transaction.amount >= 15_000
        for transaction in transactions
        if transaction.pattern == "large"
    )
