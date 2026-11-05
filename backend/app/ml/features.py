"""Behavioral context and numerical features for fraud detection.

Rules and the IsolationForest must see the same view of a transaction, so both
consume :class:`TransactionContext`. Context is derived only from transactions
at or before the target timestamp, which prevents future data leakage.
"""

from __future__ import annotations

import math
from bisect import bisect_left
from collections import defaultdict, deque
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from uuid import UUID

from app.models.transaction import Transaction

ONE_DAY = timedelta(hours=24)
DEFAULT_SECONDS_SINCE_PREVIOUS = 7 * 24 * 60 * 60

FEATURE_NAMES = (
    "log_amount",
    "log_amount_ratio_to_sender_mean",
    "log_sender_prior_count",
    "log_sender_count_rapid",
    "log_sender_count_frequency",
    "log_sender_count_10m",
    "log_sender_count_1h",
    "log_sender_count_24h",
    "log_sender_amount_1h",
    "log_sender_amount_24h",
    "log_seconds_since_sender_previous",
    "log_sender_unique_receivers_24h",
    "log_receiver_count_1h",
    "log_receiver_count_24h",
    "log_receiver_amount_1h",
    "log_receiver_unique_senders_24h",
    "log_device_distinct_senders",
    "log_device_count_1h",
    "log_ip_distinct_senders",
    "log_ip_count_1h",
)


@dataclass(frozen=True, slots=True)
class TransactionContext:
    """Point-in-time behavior around one transaction.

    Counts include the transaction itself, which matches how thresholds such as
    "five transfers in ten minutes" are normally read.
    """

    transaction: Transaction
    sender_prior_count: int
    sender_count_rapid: int
    sender_count_frequency: int
    sender_count_10m: int
    sender_count_1h: int
    sender_count_24h: int
    sender_amount_1h: float
    sender_amount_24h: float
    seconds_since_sender_previous: float
    sender_mean_amount: float
    sender_unique_receivers_24h: int
    receiver_count_1h: int
    receiver_count_24h: int
    receiver_amount_1h: float
    receiver_unique_senders_24h: int
    device_distinct_senders: int
    device_count_1h: int
    ip_distinct_senders: int
    ip_count_1h: int


class _UniqueWindow:
    """Distinct values seen in a trailing time window."""

    def __init__(self, window: timedelta) -> None:
        self.window = window
        self.events: deque[tuple[datetime, UUID]] = deque()
        self.counts: dict[UUID, int] = {}

    def expire(self, now: datetime) -> None:
        cutoff = now - self.window
        while self.events and self.events[0][0] < cutoff:
            _, value = self.events.popleft()
            remaining = self.counts[value] - 1
            if remaining:
                self.counts[value] = remaining
            else:
                del self.counts[value]

    def count_including(self, value: UUID) -> int:
        return len(self.counts) + (0 if value in self.counts else 1)

    def add(self, timestamp: datetime, value: UUID) -> None:
        self.events.append((timestamp, value))
        self.counts[value] = self.counts.get(value, 0) + 1


def _window_count(
    timestamps: list[datetime], now: datetime, seconds: int
) -> int:
    cutoff = now - timedelta(seconds=seconds)
    return len(timestamps) - bisect_left(timestamps, cutoff) + 1


def _window_amount(
    timestamps: list[datetime],
    prefix_amounts: list[float],
    now: datetime,
    seconds: int,
) -> float:
    cutoff = now - timedelta(seconds=seconds)
    left = bisect_left(timestamps, cutoff)
    return prefix_amounts[-1] - prefix_amounts[left]


def build_transaction_contexts(
    transactions: Sequence[Transaction],
    *,
    rapid_window_seconds: int,
    frequency_window_seconds: int,
) -> dict[UUID, TransactionContext]:
    """Build one context per unique transaction, ordered by event time."""

    unique = {transaction.id: transaction for transaction in transactions}
    ordered = sorted(
        unique.values(),
        key=lambda transaction: (transaction.timestamp, str(transaction.id)),
    )

    sender_times: dict[UUID, list[datetime]] = defaultdict(list)
    sender_prefix_amounts: dict[UUID, list[float]] = defaultdict(
        lambda: [0.0]
    )
    receiver_times: dict[UUID, list[datetime]] = defaultdict(list)
    receiver_prefix_amounts: dict[UUID, list[float]] = defaultdict(
        lambda: [0.0]
    )
    sender_receivers: dict[UUID, _UniqueWindow] = defaultdict(
        lambda: _UniqueWindow(ONE_DAY)
    )
    receiver_senders: dict[UUID, _UniqueWindow] = defaultdict(
        lambda: _UniqueWindow(ONE_DAY)
    )
    device_times: dict[str, list[datetime]] = defaultdict(list)
    device_senders: dict[str, set[UUID]] = defaultdict(set)
    ip_times: dict[str, list[datetime]] = defaultdict(list)
    ip_senders: dict[str, set[UUID]] = defaultdict(set)

    contexts: dict[UUID, TransactionContext] = {}
    for transaction in ordered:
        now = transaction.timestamp
        sender = transaction.from_account
        receiver = transaction.to_account

        current_sender_times = sender_times[sender]
        sender_prefix = sender_prefix_amounts[sender]
        sender_prior_count = len(current_sender_times)
        sender_mean_amount = (
            sender_prefix[-1] / sender_prior_count
            if sender_prior_count
            else 0.0
        )
        seconds_since_previous = (
            (now - current_sender_times[-1]).total_seconds()
            if current_sender_times
            else float(DEFAULT_SECONDS_SINCE_PREVIOUS)
        )
        sender_receiver_window = sender_receivers[sender]
        sender_receiver_window.expire(now)

        current_receiver_times = receiver_times[receiver]
        receiver_prefix = receiver_prefix_amounts[receiver]
        receiver_sender_window = receiver_senders[receiver]
        receiver_sender_window.expire(now)

        device = transaction.device_id
        if device:
            device_sender_set = device_senders[device]
            device_distinct_senders = len(device_sender_set) + (
                0 if sender in device_sender_set else 1
            )
            device_count_1h = _window_count(
                device_times[device], now, 3_600
            )
        else:
            device_distinct_senders = 0
            device_count_1h = 0

        ip_address = transaction.ip_address
        if ip_address:
            ip_sender_set = ip_senders[ip_address]
            ip_distinct_senders = len(ip_sender_set) + (
                0 if sender in ip_sender_set else 1
            )
            ip_count_1h = _window_count(ip_times[ip_address], now, 3_600)
        else:
            ip_distinct_senders = 0
            ip_count_1h = 0

        contexts[transaction.id] = TransactionContext(
            transaction=transaction,
            sender_prior_count=sender_prior_count,
            sender_count_rapid=_window_count(
                current_sender_times, now, rapid_window_seconds
            ),
            sender_count_frequency=_window_count(
                current_sender_times, now, frequency_window_seconds
            ),
            sender_count_10m=_window_count(current_sender_times, now, 600),
            sender_count_1h=_window_count(current_sender_times, now, 3_600),
            sender_count_24h=_window_count(
                current_sender_times, now, 86_400
            ),
            sender_amount_1h=_window_amount(
                current_sender_times, sender_prefix, now, 3_600
            ),
            sender_amount_24h=_window_amount(
                current_sender_times, sender_prefix, now, 86_400
            ),
            seconds_since_sender_previous=max(0.0, seconds_since_previous),
            sender_mean_amount=sender_mean_amount,
            sender_unique_receivers_24h=(
                sender_receiver_window.count_including(receiver)
            ),
            receiver_count_1h=_window_count(
                current_receiver_times, now, 3_600
            ),
            receiver_count_24h=_window_count(
                current_receiver_times, now, 86_400
            ),
            receiver_amount_1h=_window_amount(
                current_receiver_times, receiver_prefix, now, 3_600
            ),
            receiver_unique_senders_24h=(
                receiver_sender_window.count_including(sender)
            ),
            device_distinct_senders=device_distinct_senders,
            device_count_1h=device_count_1h,
            ip_distinct_senders=ip_distinct_senders,
            ip_count_1h=ip_count_1h,
        )

        sender_times[sender].append(now)
        sender_prefix_amounts[sender].append(
            sender_prefix[-1] + transaction.amount
        )
        sender_receiver_window.add(now, receiver)

        receiver_times[receiver].append(now)
        receiver_prefix_amounts[receiver].append(
            receiver_prefix[-1] + transaction.amount
        )
        receiver_sender_window.add(now, sender)

        if device:
            device_times[device].append(now)
            device_senders[device].add(sender)
        if ip_address:
            ip_times[ip_address].append(now)
            ip_senders[ip_address].add(sender)

    return contexts


def _log1p(value: float) -> float:
    return math.log1p(max(0.0, value))


def feature_vector(context: TransactionContext) -> list[float]:
    """Return the model feature row in :data:`FEATURE_NAMES` order."""

    transaction = context.transaction
    if context.sender_mean_amount > 0:
        amount_ratio = min(
            transaction.amount / context.sender_mean_amount, 1_000.0
        )
    else:
        amount_ratio = 1.0

    return [
        _log1p(transaction.amount),
        _log1p(amount_ratio),
        _log1p(context.sender_prior_count),
        _log1p(context.sender_count_rapid),
        _log1p(context.sender_count_frequency),
        _log1p(context.sender_count_10m),
        _log1p(context.sender_count_1h),
        _log1p(context.sender_count_24h),
        _log1p(context.sender_amount_1h),
        _log1p(context.sender_amount_24h),
        _log1p(
            min(
                context.seconds_since_sender_previous,
                DEFAULT_SECONDS_SINCE_PREVIOUS,
            )
        ),
        _log1p(context.sender_unique_receivers_24h),
        _log1p(context.receiver_count_1h),
        _log1p(context.receiver_count_24h),
        _log1p(context.receiver_amount_1h),
        _log1p(context.receiver_unique_senders_24h),
        _log1p(context.device_distinct_senders),
        _log1p(context.device_count_1h),
        _log1p(context.ip_distinct_senders),
        _log1p(context.ip_count_1h),
    ]
