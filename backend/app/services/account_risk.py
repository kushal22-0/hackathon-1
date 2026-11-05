"""Live account risk profiles from transaction behavior and alert exposure."""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import UUID

from app.core.config import DetectionSettings
from app.core.errors import AppError
from app.models.account import Account, AccountRiskProfile, Customer, RiskSignal
from app.models.enums import (
    ACTIVE_ALERT_STATUSES,
    RiskLevel,
    RuleSeverity,
)
from app.models.transaction import Transaction, TransactionSearchQuery
from app.repositories.container import RepositoryContainer
from app.services.risk_scoring import (
    combine_contributions,
    risk_level_for_score,
)

DAY_SECONDS = 86_400
FAN_IN_THRESHOLD = 8
FAN_OUT_THRESHOLD = 8
SHARED_IDENTITY_THRESHOLD = 3
IDENTIFIER_LOOKUP_LIMIT = 20
IDENTIFIER_ROW_LIMIT = 200


class AccountRiskService:
    def __init__(
        self,
        repositories: RepositoryContainer,
        settings: DetectionSettings,
        *,
        max_transactions: int = 5_000,
    ) -> None:
        self.repositories = repositories
        self.settings = settings
        self.max_transactions = max_transactions

    def get_profile(self, account_id: UUID) -> AccountRiskProfile:
        account = self.repositories.accounts.get_by_id(account_id)
        if account is None:
            raise AppError(
                code="account_not_found",
                message="Account not found",
                status_code=404,
                details={"account_id": str(account_id)},
            )

        customer = self.repositories.customers.get_by_id(account.customer_id)
        transactions = self.repositories.transactions.list_for_account(
            account_id, limit=self.max_transactions
        )
        alerts = self.repositories.alerts.list_for_transactions(
            [transaction.id for transaction in transactions]
        )
        return self._build_profile(account, customer, transactions, alerts)

    def _build_profile(
        self,
        account: Account,
        customer: Customer | None,
        transactions: list[Transaction],
        alerts: list,
    ) -> AccountRiskProfile:
        outgoing = [
            transaction
            for transaction in transactions
            if transaction.from_account == account.id
        ]
        incoming = [
            transaction
            for transaction in transactions
            if transaction.to_account == account.id
        ]
        sent_amount = round(
            sum(transaction.amount for transaction in outgoing), 2
        )
        received_amount = round(
            sum(transaction.amount for transaction in incoming), 2
        )
        counterparties = {
            transaction.to_account for transaction in outgoing
        } | {transaction.from_account for transaction in incoming}

        max_sent = max(
            (transaction.amount for transaction in outgoing), default=0.0
        )
        max_frequency = _max_window_count(
            [transaction.timestamp for transaction in outgoing],
            self.settings.high_frequency_window_minutes * 60,
        )
        max_rapid = _max_window_count(
            [transaction.timestamp for transaction in outgoing],
            self.settings.rapid_succession_seconds,
        )
        max_fan_out = _max_distinct_in_window(
            [
                (transaction.timestamp, transaction.to_account)
                for transaction in outgoing
            ],
            DAY_SECONDS,
        )
        max_fan_in = _max_distinct_in_window(
            [
                (transaction.timestamp, transaction.from_account)
                for transaction in incoming
            ],
            DAY_SECONDS,
        )
        shared_identifier = self._best_shared_identifier(
            account, transactions
        )

        signals = self._build_signals(
            customer=customer,
            max_sent=max_sent,
            max_frequency=max_frequency,
            max_rapid=max_rapid,
            max_fan_out=max_fan_out,
            max_fan_in=max_fan_in,
            shared_identifier=shared_identifier,
        )
        activity_score = combine_contributions(
            signal.score_contribution for signal in signals
        )

        active_alerts = [
            alert for alert in alerts if alert.status in ACTIVE_ALERT_STATUSES
        ]
        max_active_alert_score = max(
            (alert.risk_score for alert in active_alerts), default=None
        )
        volume_bonus = min(
            10.0, max(0, len(active_alerts) - 1) * 3.0
        )
        risk_score = round(
            min(
                100.0,
                max(activity_score, max_active_alert_score or 0.0)
                + volume_bonus,
            ),
            2,
        )

        rule_hit_counts = Counter(
            hit.code.value
            for alert in alerts
            for hit in alert.rule_hits
        )
        explanation = _build_explanation(
            risk_score=risk_score,
            signals=signals,
            active_alert_count=len(active_alerts),
            alert_count=len(alerts),
            max_active_alert_score=max_active_alert_score,
            transaction_count=len(transactions),
            sent_amount=sent_amount,
            received_amount=received_amount,
            counterparty_count=len(counterparties),
        )

        return AccountRiskProfile(
            account=account,
            customer=customer,
            risk_score=risk_score,
            signals=signals,
            explanation=explanation,
            transaction_count=len(transactions),
            sent_count=len(outgoing),
            received_count=len(incoming),
            sent_amount=sent_amount,
            received_amount=received_amount,
            net_flow=round(received_amount - sent_amount, 2),
            counterparty_count=len(counterparties),
            first_transaction_at=(
                transactions[0].timestamp if transactions else None
            ),
            last_transaction_at=(
                transactions[-1].timestamp if transactions else None
            ),
            alert_count=len(alerts),
            active_alert_count=len(active_alerts),
            max_active_alert_risk_score=max_active_alert_score,
            rule_hit_counts=dict(sorted(rule_hit_counts.items())),
            generated_at=datetime.now(UTC),
        )

    def _build_signals(
        self,
        *,
        customer: Customer | None,
        max_sent: float,
        max_frequency: int,
        max_rapid: int,
        max_fan_out: int,
        max_fan_in: int,
        shared_identifier: tuple[str, str, int] | None,
    ) -> list[RiskSignal]:
        signals: list[RiskSignal] = []

        if max_sent >= self.settings.large_transfer_threshold:
            multiplier = max_sent / self.settings.large_transfer_threshold
            if multiplier >= self.settings.large_transfer_critical_multiplier:
                severity = RuleSeverity.CRITICAL
                points = self.settings.large_transfer_critical_points
            elif multiplier >= self.settings.large_transfer_high_multiplier:
                severity = RuleSeverity.HIGH
                points = self.settings.large_transfer_high_points
            else:
                severity = RuleSeverity.MEDIUM
                points = self.settings.large_transfer_points
            signals.append(
                RiskSignal(
                    code="large_transfer",
                    name="Large outgoing transfer",
                    severity=severity,
                    score_contribution=points,
                    explanation=(
                        f"Largest outgoing transfer of {_money(max_sent)} is "
                        f"{multiplier:.2f}x the "
                        f"{_money(self.settings.large_transfer_threshold)} "
                        "threshold."
                    ),
                    evidence={
                        "largest_outgoing_amount": round(max_sent, 2),
                        "threshold": self.settings.large_transfer_threshold,
                        "multiplier": round(multiplier, 2),
                    },
                )
            )

        if max_frequency >= self.settings.high_frequency_count:
            critical = (
                max_frequency
                >= self.settings.high_frequency_count
                * self.settings.high_frequency_critical_multiplier
            )
            signals.append(
                RiskSignal(
                    code="high_frequency",
                    name="High transaction frequency",
                    severity=(
                        RuleSeverity.CRITICAL
                        if critical
                        else RuleSeverity.HIGH
                    ),
                    score_contribution=(
                        self.settings.high_frequency_critical_points
                        if critical
                        else self.settings.high_frequency_points
                    ),
                    explanation=(
                        f"Peak of {max_frequency} outbound transfers within "
                        f"{self.settings.high_frequency_window_minutes} "
                        "minutes."
                    ),
                    evidence={
                        "peak_transaction_count": max_frequency,
                        "window_minutes": (
                            self.settings.high_frequency_window_minutes
                        ),
                        "threshold": self.settings.high_frequency_count,
                    },
                )
            )

        if max_rapid >= self.settings.rapid_succession_count:
            critical = (
                max_rapid
                >= self.settings.rapid_succession_count
                * self.settings.rapid_succession_critical_multiplier
            )
            signals.append(
                RiskSignal(
                    code="rapid_succession",
                    name="Rapid succession",
                    severity=(
                        RuleSeverity.HIGH
                        if critical
                        else RuleSeverity.MEDIUM
                    ),
                    score_contribution=(
                        self.settings.rapid_succession_critical_points
                        if critical
                        else self.settings.rapid_succession_points
                    ),
                    explanation=(
                        f"Peak of {max_rapid} outbound transfers within "
                        f"{self.settings.rapid_succession_seconds} seconds."
                    ),
                    evidence={
                        "peak_transaction_count": max_rapid,
                        "window_seconds": (
                            self.settings.rapid_succession_seconds
                        ),
                        "threshold": self.settings.rapid_succession_count,
                    },
                )
            )

        if max_fan_out >= FAN_OUT_THRESHOLD:
            critical = max_fan_out >= FAN_OUT_THRESHOLD * 2
            signals.append(
                RiskSignal(
                    code="fan_out",
                    name="Fan-out dispersion",
                    severity=(
                        RuleSeverity.HIGH
                        if critical
                        else RuleSeverity.MEDIUM
                    ),
                    score_contribution=60 if critical else 45,
                    explanation=(
                        f"Sent to {max_fan_out} distinct accounts within "
                        "24 hours."
                    ),
                    evidence={
                        "distinct_destinations": max_fan_out,
                        "window_hours": 24,
                        "threshold": FAN_OUT_THRESHOLD,
                    },
                )
            )

        if max_fan_in >= FAN_IN_THRESHOLD:
            critical = max_fan_in >= FAN_IN_THRESHOLD * 2
            signals.append(
                RiskSignal(
                    code="fan_in",
                    name="Fan-in consolidation",
                    severity=(
                        RuleSeverity.HIGH
                        if critical
                        else RuleSeverity.MEDIUM
                    ),
                    score_contribution=60 if critical else 45,
                    explanation=(
                        f"Received from {max_fan_in} distinct accounts within "
                        "24 hours."
                    ),
                    evidence={
                        "distinct_senders": max_fan_in,
                        "window_hours": 24,
                        "threshold": FAN_IN_THRESHOLD,
                    },
                )
            )

        if shared_identifier is not None:
            kind, value, account_count = shared_identifier
            critical = account_count >= SHARED_IDENTITY_THRESHOLD + 2
            label = "device" if kind == "device_id" else "IP address"
            signals.append(
                RiskSignal(
                    code="shared_identity",
                    name="Shared device or IP",
                    severity=(
                        RuleSeverity.HIGH
                        if critical
                        else RuleSeverity.MEDIUM
                    ),
                    score_contribution=55 if critical else 40,
                    explanation=(
                        f"{account_count} accounts have used the same "
                        f"{label}."
                    ),
                    evidence={
                        "identifier_type": kind,
                        "identifier": value,
                        "distinct_account_count": account_count,
                        "threshold": SHARED_IDENTITY_THRESHOLD,
                    },
                )
            )

        if customer is not None and customer.risk_level != RiskLevel.LOW:
            points = {
                RiskLevel.MEDIUM: 10,
                RiskLevel.HIGH: 20,
                RiskLevel.CRITICAL: 30,
            }[customer.risk_level]
            signals.append(
                RiskSignal(
                    code="customer_risk",
                    name="Customer risk rating",
                    severity=RuleSeverity(customer.risk_level.value),
                    score_contribution=points,
                    explanation=(
                        "The owning customer is pre-classified as "
                        f"{customer.risk_level.value} risk."
                    ),
                    evidence={
                        "customer_id": str(customer.id),
                        "risk_level": customer.risk_level.value,
                    },
                )
            )

        return signals

    def _best_shared_identifier(
        self, account: Account, transactions: list[Transaction]
    ) -> tuple[str, str, int] | None:
        devices = Counter(
            transaction.device_id
            for transaction in transactions
            if transaction.device_id
        )
        ip_addresses = Counter(
            transaction.ip_address
            for transaction in transactions
            if transaction.ip_address
        )
        candidates = [
            (count, "device_id", value)
            for value, count in devices.items()
        ] + [
            (count, "ip_address", value)
            for value, count in ip_addresses.items()
        ]
        candidates.sort(key=lambda item: (-item[0], item[1], item[2]))

        best: tuple[str, str, int] | None = None
        for _, kind, value in candidates[:IDENTIFIER_LOOKUP_LIMIT]:
            query = TransactionSearchQuery(
                **{kind: value}, page_size=IDENTIFIER_ROW_LIMIT
            )
            matches, _ = self.repositories.transactions.search(query)
            account_count = len(
                {transaction.from_account for transaction in matches}
            )
            if best is None or account_count > best[2]:
                best = (kind, value, account_count)

        if best is None or best[2] < SHARED_IDENTITY_THRESHOLD:
            return None
        return best


def _max_window_count(
    timestamps: list[datetime], window_seconds: int
) -> int:
    if not timestamps:
        return 0
    left = 0
    best = 0
    window = timedelta(seconds=window_seconds)
    for right, timestamp in enumerate(timestamps):
        while timestamp - timestamps[left] > window:
            left += 1
        best = max(best, right - left + 1)
    return best


def _max_distinct_in_window(
    events: list[tuple[datetime, UUID]], window_seconds: int
) -> int:
    if not events:
        return 0
    left = 0
    best = 0
    counts: Counter[UUID] = Counter()
    window = timedelta(seconds=window_seconds)

    for right, (timestamp, value) in enumerate(events):
        counts[value] += 1
        while timestamp - events[left][0] > window:
            expired = events[left][1]
            counts[expired] -= 1
            if counts[expired] == 0:
                del counts[expired]
            left += 1
        best = max(best, len(counts))
    return best


def _money(value: float) -> str:
    return f"${value:,.2f}"


def _build_explanation(
    *,
    risk_score: float,
    signals: list[RiskSignal],
    active_alert_count: int,
    alert_count: int,
    max_active_alert_score: float | None,
    transaction_count: int,
    sent_amount: float,
    received_amount: float,
    counterparty_count: int,
) -> str:
    level = risk_level_for_score(risk_score).value.title()
    if signals:
        signal_text = "Signals: " + "; ".join(
            f"{signal.name} (+{signal.score_contribution:g})"
            for signal in signals
        )
    else:
        signal_text = "No transaction-risk signals fired."

    if active_alert_count:
        alert_text = (
            f"{active_alert_count} active alert(s), highest risk "
            f"{max_active_alert_score or 0:.1f}/100."
        )
    elif alert_count:
        alert_text = (
            f"{alert_count} alert(s) on file, none currently active."
        )
    else:
        alert_text = "No alerts are on file."

    return (
        f"{level} risk at {risk_score:.1f}/100. {signal_text} {alert_text} "
        f"Activity: {transaction_count} transactions, "
        f"{_money(sent_amount)} sent, {_money(received_amount)} received "
        f"across {counterparty_count} counterparties."
    )
