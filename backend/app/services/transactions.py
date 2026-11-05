"""Transaction ingestion and search business logic."""

from __future__ import annotations

import math
from uuid import UUID

from app.core.errors import AppError
from app.models.transaction import (
    Transaction,
    TransactionIngestResult,
    TransactionPage,
    TransactionSearchQuery,
)
from app.repositories.container import RepositoryContainer
from app.services.csv_ingestion import parse_transactions_csv


class TransactionService:
    def __init__(self, repositories: RepositoryContainer, *, max_rows: int) -> None:
        self.repositories = repositories
        self.max_rows = max_rows

    def ingest_csv(
        self, content: bytes, *, filename: str
    ) -> TransactionIngestResult:
        parsed = parse_transactions_csv(
            content,
            filename=filename,
            max_rows=self.max_rows,
        )
        transaction_ids = [transaction.id for transaction in parsed.transactions]

        existing = self.repositories.transactions.existing_ids(transaction_ids)
        if existing:
            raise AppError(
                code="duplicate_transaction_ids",
                message="One or more transaction IDs already exist",
                status_code=409,
                details={
                    "duplicate_ids": sorted(str(value) for value in existing)[
                        :100
                    ],
                    "duplicate_count": len(existing),
                },
            )

        account_ids = {
            account_id
            for transaction in parsed.transactions
            for account_id in (transaction.from_account, transaction.to_account)
        }
        known_accounts = {
            account.id
            for account in self.repositories.accounts.get_by_ids(
                sorted(account_ids)
            )
        }
        missing_accounts = sorted(
            str(account_id)
            for account_id in account_ids
            if account_id not in known_accounts
        )
        if missing_accounts:
            raise AppError(
                code="unknown_accounts",
                message=(
                    "Transactions reference accounts that do not exist. "
                    "Seed the account master data before ingesting."
                ),
                status_code=422,
                details={
                    "missing_account_count": len(missing_accounts),
                    "missing_accounts": missing_accounts[:100],
                },
            )

        accepted = self.repositories.transactions.add_many(parsed.transactions)
        self.repositories.commit()

        return TransactionIngestResult(
            accepted=accepted,
            filename=parsed.filename,
        )

    def search(self, query: TransactionSearchQuery) -> TransactionPage:
        items, total = self.repositories.transactions.search(query)
        total_pages = math.ceil(total / query.page_size) if total else 0
        return TransactionPage(
            items=items,
            page=query.page,
            page_size=query.page_size,
            total=total,
            total_pages=total_pages,
        )

    def get(self, transaction_id: UUID) -> Transaction:
        transaction = self.repositories.transactions.get_by_id(transaction_id)
        if transaction is None:
            raise AppError(
                code="transaction_not_found",
                message="Transaction not found",
                status_code=404,
                details={"transaction_id": str(transaction_id)},
            )
        return transaction
