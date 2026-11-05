"""Thread-safe in-memory repositories for local development and tests."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from threading import RLock
from uuid import UUID

from app.models.account import Account, Customer
from app.models.alert import Alert, AlertSearchQuery
from app.models.enums import ACTIVE_ALERT_STATUSES
from app.models.transaction import Transaction, TransactionSearchQuery


class InMemoryStore:
    """Shared mutable state for all in-memory repositories."""

    def __init__(self) -> None:
        self.customers: dict[UUID, Customer] = {}
        self.accounts: dict[UUID, Account] = {}
        self.transactions: dict[UUID, Transaction] = {}
        self.alerts: dict[UUID, Alert] = {}
        self.lock = RLock()


class InMemoryCustomerRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        with self.store.lock:
            return self.store.customers.get(customer_id)

    def add_many(self, customers: Sequence[Customer]) -> int:
        with self.store.lock:
            for customer in customers:
                self.store.customers[customer.id] = customer
            return len(customers)


class InMemoryAccountRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def get_by_id(self, account_id: UUID) -> Account | None:
        with self.store.lock:
            return self.store.accounts.get(account_id)

    def get_by_ids(self, account_ids: Sequence[UUID]) -> list[Account]:
        with self.store.lock:
            return [
                self.store.accounts[account_id]
                for account_id in account_ids
                if account_id in self.store.accounts
            ]

    def get_by_number(self, account_number: str) -> Account | None:
        with self.store.lock:
            return next(
                (
                    account
                    for account in self.store.accounts.values()
                    if account.account_number == account_number
                ),
                None,
            )

    def add_many(self, accounts: Sequence[Account]) -> int:
        with self.store.lock:
            for account in accounts:
                self.store.accounts[account.id] = account
            return len(accounts)


class InMemoryTransactionRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def add_many(self, transactions: Sequence[Transaction]) -> int:
        with self.store.lock:
            for transaction in transactions:
                if transaction.id in self.store.transactions:
                    raise ValueError(
                        f"Transaction {transaction.id} already exists"
                    )
                self.store.transactions[transaction.id] = transaction
            return len(transactions)

    def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        with self.store.lock:
            return self.store.transactions.get(transaction_id)

    def get_by_ids(self, transaction_ids: Sequence[UUID]) -> list[Transaction]:
        with self.store.lock:
            return [
                self.store.transactions[transaction_id]
                for transaction_id in transaction_ids
                if transaction_id in self.store.transactions
            ]

    def existing_ids(self, transaction_ids: Sequence[UUID]) -> set[UUID]:
        with self.store.lock:
            return {
                transaction_id
                for transaction_id in transaction_ids
                if transaction_id in self.store.transactions
            }

    def search(
        self, query: TransactionSearchQuery
    ) -> tuple[list[Transaction], int]:
        with self.store.lock:
            items = [
                transaction
                for transaction in self.store.transactions.values()
                if self._matches(transaction, query)
            ]

        if query.sort_by == "amount":
            items.sort(
                key=lambda transaction: (
                    transaction.amount,
                    transaction.timestamp,
                    str(transaction.id),
                ),
                reverse=query.sort_dir == "desc",
            )
        else:
            items.sort(
                key=lambda transaction: (
                    transaction.timestamp,
                    transaction.amount,
                    str(transaction.id),
                ),
                reverse=query.sort_dir == "desc",
            )

        total = len(items)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return items[start:end], total

    def list_for_account(
        self,
        account_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        with self.store.lock:
            items = [
                transaction
                for transaction in self.store.transactions.values()
                if (
                    (transaction.from_account == account_id)
                    or (transaction.to_account == account_id)
                )
                and (since is None or transaction.timestamp >= since)
                and (until is None or transaction.timestamp <= until)
            ]
        items.sort(key=lambda transaction: transaction.timestamp)
        if limit is not None and len(items) > limit:
            return items[-limit:]
        return items

    def list_window(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        with self.store.lock:
            items = [
                transaction
                for transaction in self.store.transactions.values()
                if (since is None or transaction.timestamp >= since)
                and (until is None or transaction.timestamp <= until)
            ]
        items.sort(key=lambda transaction: transaction.timestamp)
        if limit is not None and len(items) > limit:
            return items[-limit:]
        return items

    def list_recent(self, limit: int = 10_000) -> list[Transaction]:
        with self.store.lock:
            items = list(self.store.transactions.values())
        items.sort(key=lambda transaction: transaction.timestamp, reverse=True)
        return items[:limit]

    def count(self) -> int:
        with self.store.lock:
            return len(self.store.transactions)

    @staticmethod
    def _matches(
        transaction: Transaction, query: TransactionSearchQuery
    ) -> bool:
        if query.account_id is not None and (
            transaction.from_account != query.account_id
            and transaction.to_account != query.account_id
        ):
            return False
        if (
            query.from_account is not None
            and transaction.from_account != query.from_account
        ):
            return False
        if (
            query.to_account is not None
            and transaction.to_account != query.to_account
        ):
            return False
        if (
            query.min_amount is not None
            and transaction.amount < query.min_amount
        ):
            return False
        if (
            query.max_amount is not None
            and transaction.amount > query.max_amount
        ):
            return False
        if (
            query.start_time is not None
            and transaction.timestamp < query.start_time
        ):
            return False
        if (
            query.end_time is not None
            and transaction.timestamp > query.end_time
        ):
            return False
        if query.channel is not None and transaction.channel != query.channel:
            return False
        if query.label is not None and transaction.label != query.label:
            return False
        if (
            query.device_id is not None
            and transaction.device_id != query.device_id
        ):
            return False
        return not (
            query.ip_address is not None
            and transaction.ip_address != query.ip_address
        )


class InMemoryAlertRepository:
    def __init__(self, store: InMemoryStore) -> None:
        self.store = store

    def add(self, alert: Alert) -> Alert:
        with self.store.lock:
            self._ensure_active_uniqueness(alert)
            self.store.alerts[alert.id] = alert
            return alert

    def update(self, alert: Alert) -> Alert:
        with self.store.lock:
            if alert.id not in self.store.alerts:
                raise ValueError(f"Alert {alert.id} does not exist")
            self._ensure_active_uniqueness(alert)
            self.store.alerts[alert.id] = alert
            return alert

    def get_by_id(self, alert_id: UUID) -> Alert | None:
        with self.store.lock:
            return self.store.alerts.get(alert_id)

    def get_active_by_transaction_id(
        self, transaction_id: UUID
    ) -> Alert | None:
        with self.store.lock:
            candidates = [
                alert
                for alert in self.store.alerts.values()
                if alert.transaction_id == transaction_id
                and alert.status in ACTIVE_ALERT_STATUSES
            ]
        if not candidates:
            return None
        return max(
            candidates,
            key=lambda alert: (alert.created_at, str(alert.id)),
        )

    def search(
        self, query: AlertSearchQuery
    ) -> tuple[list[Alert], int]:
        with self.store.lock:
            items = [
                alert
                for alert in self.store.alerts.values()
                if self._matches(alert, query)
            ]

        reverse = query.sort_dir == "desc"
        if query.sort_by == "risk_score":
            items.sort(
                key=lambda alert: (
                    alert.risk_score,
                    alert.created_at,
                    str(alert.id),
                ),
                reverse=reverse,
            )
        else:
            items.sort(
                key=lambda alert: (
                    alert.created_at,
                    alert.risk_score,
                    str(alert.id),
                ),
                reverse=reverse,
            )

        total = len(items)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        return items[start:end], total

    def _ensure_active_uniqueness(self, alert: Alert) -> None:
        if alert.status not in ACTIVE_ALERT_STATUSES:
            return
        for existing in self.store.alerts.values():
            if (
                existing.id != alert.id
                and existing.transaction_id == alert.transaction_id
                and existing.status in ACTIVE_ALERT_STATUSES
            ):
                raise ValueError(
                    "An active alert already exists for transaction "
                    f"{alert.transaction_id}"
                )

    @staticmethod
    def _matches(alert: Alert, query: AlertSearchQuery) -> bool:
        if query.status is not None and alert.status != query.status:
            return False
        if (
            query.transaction_id is not None
            and alert.transaction_id != query.transaction_id
        ):
            return False
        if (
            query.min_risk_score is not None
            and alert.risk_score < query.min_risk_score
        ):
            return False
        return not (
            query.max_risk_score is not None
            and alert.risk_score > query.max_risk_score
        )
