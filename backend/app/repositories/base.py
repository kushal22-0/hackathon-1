"""Repository interfaces. Services depend on these protocols, not SQLAlchemy."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from typing import Protocol
from uuid import UUID

from app.models.account import Account, Customer
from app.models.transaction import Transaction, TransactionSearchQuery


class CustomerRepository(Protocol):
    def get_by_id(self, customer_id: UUID) -> Customer | None: ...

    def add_many(self, customers: Sequence[Customer]) -> int: ...


class AccountRepository(Protocol):
    def get_by_id(self, account_id: UUID) -> Account | None: ...

    def get_by_ids(self, account_ids: Sequence[UUID]) -> list[Account]: ...

    def get_by_number(self, account_number: str) -> Account | None: ...

    def add_many(self, accounts: Sequence[Account]) -> int: ...


class TransactionRepository(Protocol):
    def add_many(self, transactions: Sequence[Transaction]) -> int: ...

    def get_by_id(self, transaction_id: UUID) -> Transaction | None: ...

    def existing_ids(self, transaction_ids: Sequence[UUID]) -> set[UUID]: ...

    def search(
        self, query: TransactionSearchQuery
    ) -> tuple[list[Transaction], int]: ...

    def list_for_account(
        self,
        account_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]: ...

    def list_window(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]: ...

    def list_recent(self, limit: int = 10_000) -> list[Transaction]: ...

    def count(self) -> int: ...
