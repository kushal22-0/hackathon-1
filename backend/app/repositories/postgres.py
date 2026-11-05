"""Supabase PostgreSQL implementations of the repository protocols."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime
from decimal import Decimal
from typing import cast
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.account import Account, Customer
from app.models.tables import AccountTable, CustomerTable, TransactionTable
from app.models.transaction import Transaction, TransactionSearchQuery


def _to_customer(row: CustomerTable) -> Customer:
    return Customer.model_validate(row)


def _to_account(row: AccountTable) -> Account:
    return Account.model_validate(row)


def _to_transaction(row: TransactionTable) -> Transaction:
    return Transaction.model_validate(row)


class PostgresCustomerRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, customer_id: UUID) -> Customer | None:
        row = self.session.get(CustomerTable, customer_id)
        return _to_customer(row) if row else None

    def add_many(self, customers: Sequence[Customer]) -> int:
        self.session.add_all(
            [
                CustomerTable(
                    id=customer.id,
                    external_id=customer.external_id,
                    full_name=customer.full_name,
                    email=customer.email,
                    phone=customer.phone,
                    country=customer.country,
                    risk_level=customer.risk_level.value,
                )
                for customer in customers
            ]
        )
        self.session.flush()
        return len(customers)


class PostgresAccountRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_by_id(self, account_id: UUID) -> Account | None:
        row = self.session.get(AccountTable, account_id)
        return _to_account(row) if row else None

    def get_by_ids(self, account_ids: Sequence[UUID]) -> list[Account]:
        if not account_ids:
            return []
        rows = self.session.scalars(
            select(AccountTable).where(AccountTable.id.in_(account_ids))
        ).all()
        return [_to_account(row) for row in rows]

    def get_by_number(self, account_number: str) -> Account | None:
        row = self.session.scalar(
            select(AccountTable).where(
                AccountTable.account_number == account_number
            )
        )
        return _to_account(row) if row else None

    def add_many(self, accounts: Sequence[Account]) -> int:
        self.session.add_all(
            [
                AccountTable(
                    id=account.id,
                    customer_id=account.customer_id,
                    account_number=account.account_number,
                    account_type=account.account_type,
                    currency=account.currency,
                    status=account.status,
                    balance=Decimal(str(account.balance)),
                    opened_at=account.opened_at,
                )
                for account in accounts
            ]
        )
        self.session.flush()
        return len(accounts)


class PostgresTransactionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def add_many(self, transactions: Sequence[Transaction]) -> int:
        self.session.add_all(
            [
                TransactionTable(
                    id=transaction.id,
                    from_account=transaction.from_account,
                    to_account=transaction.to_account,
                    amount=Decimal(str(transaction.amount)),
                    currency=transaction.currency,
                    timestamp=transaction.timestamp,
                    device_id=transaction.device_id,
                    ip_address=transaction.ip_address,
                    channel=transaction.channel.value,
                    label=transaction.label,
                )
                for transaction in transactions
            ]
        )
        self.session.flush()
        return len(transactions)

    def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        row = self.session.get(TransactionTable, transaction_id)
        return _to_transaction(row) if row else None

    def existing_ids(self, transaction_ids: Sequence[UUID]) -> set[UUID]:
        if not transaction_ids:
            return set()
        rows = self.session.scalars(
            select(TransactionTable.id).where(
                TransactionTable.id.in_(transaction_ids)
            )
        ).all()
        return set(rows)

    def search(
        self, query: TransactionSearchQuery
    ) -> tuple[list[Transaction], int]:
        conditions = self._search_conditions(query)
        total = (
            self.session.scalar(
                select(func.count())
                .select_from(TransactionTable)
                .where(*conditions)
            )
            or 0
        )

        sort_column = (
            TransactionTable.amount
            if query.sort_by == "amount"
            else TransactionTable.timestamp
        )
        ordering = sort_column.desc() if query.sort_dir == "desc" else sort_column.asc()
        id_ordering = (
            TransactionTable.id.desc()
            if query.sort_dir == "desc"
            else TransactionTable.id.asc()
        )
        statement = (
            select(TransactionTable)
            .where(*conditions)
            .order_by(ordering, id_ordering)
            .offset((query.page - 1) * query.page_size)
            .limit(query.page_size)
        )
        rows = self.session.scalars(statement).all()
        return [_to_transaction(row) for row in rows], total

    def list_for_account(
        self,
        account_id: UUID,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        statements = select(TransactionTable).where(
            or_(
                TransactionTable.from_account == account_id,
                TransactionTable.to_account == account_id,
            )
        )
        return self._list_statements(statements, since, until, limit)

    def list_window(
        self,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int | None = None,
    ) -> list[Transaction]:
        return self._list_statements(
            select(TransactionTable), since, until, limit
        )

    def list_recent(self, limit: int = 10_000) -> list[Transaction]:
        rows = self.session.scalars(
            select(TransactionTable)
            .order_by(TransactionTable.timestamp.desc())
            .limit(limit)
        ).all()
        return [_to_transaction(row) for row in rows]

    def count(self) -> int:
        return (
            self.session.scalar(select(func.count()).select_from(TransactionTable))
            or 0
        )

    def _list_statements(
        self,
        statement,
        since: datetime | None,
        until: datetime | None,
        limit: int | None,
    ) -> list[Transaction]:
        if since is not None:
            statement = statement.where(TransactionTable.timestamp >= since)
        if until is not None:
            statement = statement.where(TransactionTable.timestamp <= until)

        # A limit means "most recent N within the window"; reverse into
        # ascending order for feature/tracing callers.
        if limit is not None:
            rows = self.session.scalars(
                statement.order_by(TransactionTable.timestamp.desc()).limit(limit)
            ).all()
            return [_to_transaction(row) for row in reversed(rows)]

        rows = self.session.scalars(
            statement.order_by(TransactionTable.timestamp.asc())
        ).all()
        return [_to_transaction(row) for row in rows]

    @staticmethod
    def _search_conditions(query: TransactionSearchQuery) -> list:
        conditions = []
        if query.account_id is not None:
            conditions.append(
                or_(
                    TransactionTable.from_account == query.account_id,
                    TransactionTable.to_account == query.account_id,
                )
            )
        if query.from_account is not None:
            conditions.append(
                TransactionTable.from_account == query.from_account
            )
        if query.to_account is not None:
            conditions.append(TransactionTable.to_account == query.to_account)
        if query.min_amount is not None:
            conditions.append(TransactionTable.amount >= query.min_amount)
        if query.max_amount is not None:
            conditions.append(TransactionTable.amount <= query.max_amount)
        if query.start_time is not None:
            conditions.append(TransactionTable.timestamp >= query.start_time)
        if query.end_time is not None:
            conditions.append(TransactionTable.timestamp <= query.end_time)
        if query.channel is not None:
            conditions.append(TransactionTable.channel == query.channel.value)
        if query.label is not None:
            conditions.append(TransactionTable.label == query.label)
        if query.device_id is not None:
            conditions.append(TransactionTable.device_id == query.device_id)
        if query.ip_address is not None:
            conditions.append(TransactionTable.ip_address == query.ip_address)
        return cast(list, conditions)
