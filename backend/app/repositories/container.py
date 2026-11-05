"""Repository container scoped to one service call or database session."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.account import Account, Customer
from app.models.alert import Alert
from app.models.transaction import Transaction
from app.repositories.base import (
    AccountRepository,
    AlertRepository,
    CustomerRepository,
    TransactionRepository,
)
from app.repositories.memory import (
    InMemoryAccountRepository,
    InMemoryAlertRepository,
    InMemoryCustomerRepository,
    InMemoryStore,
    InMemoryTransactionRepository,
)
from app.repositories.postgres import (
    PostgresAccountRepository,
    PostgresAlertRepository,
    PostgresCustomerRepository,
    PostgresTransactionRepository,
)


@dataclass
class RepositoryContainer:
    """All repositories for a request plus an optional SQLAlchemy transaction."""

    customers: CustomerRepository
    accounts: AccountRepository
    transactions: TransactionRepository
    alerts: AlertRepository
    session: Session | None = None

    def commit(self) -> None:
        if self.session is not None and self.session.in_transaction():
            self.session.commit()

    def rollback(self) -> None:
        if self.session is not None:
            self.session.rollback()

    @classmethod
    def from_session(cls, session: Session) -> RepositoryContainer:
        return cls(
            customers=PostgresCustomerRepository(session),
            accounts=PostgresAccountRepository(session),
            transactions=PostgresTransactionRepository(session),
            alerts=PostgresAlertRepository(session),
            session=session,
        )


@dataclass
class MemoryRepositories:
    """Access to the shared in-memory store and its repository container."""

    store: InMemoryStore
    container: RepositoryContainer


def build_memory_repositories() -> MemoryRepositories:
    store = InMemoryStore()
    container = RepositoryContainer(
        customers=InMemoryCustomerRepository(store),
        accounts=InMemoryAccountRepository(store),
        transactions=InMemoryTransactionRepository(store),
        alerts=InMemoryAlertRepository(store),
    )
    return MemoryRepositories(store=store, container=container)


def seed_memory_store(
    store: InMemoryStore,
    *,
    customers: list[Customer] | None = None,
    accounts: list[Account] | None = None,
    transactions: list[Transaction] | None = None,
    alerts: list[Alert] | None = None,
) -> None:
    with store.lock:
        for customer in customers or []:
            store.customers[customer.id] = customer
        for account in accounts or []:
            store.accounts[account.id] = account
        for transaction in transactions or []:
            store.transactions[transaction.id] = transaction
        for alert in alerts or []:
            store.alerts[alert.id] = alert
