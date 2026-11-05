"""Seed a Supabase/PostgreSQL database with the generated demo CSV files.

The script is idempotent: rows that already exist are skipped by primary key or
unique constraint. Master data is loaded before transactions so foreign keys
are satisfied.

Usage (from backend/):
    python -m scripts.seed_demo_data --database-url "$DATABASE_URL"
    python -m scripts.seed_demo_data --skip-transactions
"""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.engine import make_url

from app.core.config import Settings
from app.core.database import build_database, normalize_database_url
from app.models.tables import AccountTable, CustomerTable, TransactionTable

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = REPO_ROOT / "data"
BATCH_SIZE = 500


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _customer_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {
                "id": UUID(row["id"]),
                "external_id": row["external_id"],
                "full_name": row["full_name"],
                "email": _optional(row.get("email")),
                "phone": _optional(row.get("phone")),
                "country": row.get("country") or "US",
                "risk_level": row.get("risk_level") or "low",
            }
            for row in csv.DictReader(handle)
        ]


def _account_rows(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            {
                "id": UUID(row["id"]),
                "customer_id": UUID(row["customer_id"]),
                "account_number": row["account_number"],
                "account_type": row.get("account_type") or "checking",
                "currency": (row.get("currency") or "USD").upper(),
                "status": row.get("status") or "active",
                "balance": Decimal(row.get("balance") or "0"),
                "opened_at": date.fromisoformat(row["opened_at"]),
            }
            for row in csv.DictReader(handle)
        ]


def _transaction_rows(path: Path) -> list[dict]:
    rows: list[dict] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            label_value = _optional(row.get("label"))
            rows.append(
                {
                    "id": UUID(row["id"]),
                    "from_account": UUID(row["from_account"]),
                    "to_account": UUID(row["to_account"]),
                    "amount": Decimal(row["amount"]),
                    "currency": (row.get("currency") or "USD").upper(),
                    "timestamp": datetime.fromisoformat(row["timestamp"]),
                    "device_id": _optional(row.get("device_id")),
                    "ip_address": _optional(row.get("ip_address")),
                    "channel": (row.get("channel") or "api").lower(),
                    "label": int(label_value) if label_value is not None else None,
                }
            )
    return rows


def _insert_ignore(session, table, rows: list[dict]) -> None:
    for start in range(0, len(rows), BATCH_SIZE):
        session.execute(
            pg_insert(table)
            .values(rows[start : start + BATCH_SIZE])
            .on_conflict_do_nothing()
        )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database-url",
        default=None,
        help="PostgreSQL URL. Defaults to DATABASE_URL from backend/.env.",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DEFAULT_DATA_DIR,
        help="Directory containing customers/accounts/sample_transactions CSVs",
    )
    parser.add_argument(
        "--skip-transactions",
        action="store_true",
        help="Load only customer/account master data",
    )
    args = parser.parse_args()

    settings = Settings()
    database_url = args.database_url or settings.database_url
    if not database_url:
        parser.error(
            "A database URL is required (--database-url or DATABASE_URL)"
        )
    parsed_url = make_url(normalize_database_url(database_url))
    print(f"Target: {parsed_url.host}:{parsed_url.port}/{parsed_url.database}")
    print(f"Data dir: {args.data_dir}")

    engine, session_factory = build_database(database_url)
    try:
        customers = _customer_rows(args.data_dir / "customers.csv")
        accounts = _account_rows(args.data_dir / "accounts.csv")

        with session_factory() as session:
            _insert_ignore(session, CustomerTable, customers)
            _insert_ignore(session, AccountTable, accounts)
            session.commit()
            print(f"Customers processed: {len(customers):,}")
            print(f"Accounts processed: {len(accounts):,}")

            if not args.skip_transactions:
                transactions = _transaction_rows(
                    args.data_dir / "sample_transactions.csv"
                )
                _insert_ignore(session, TransactionTable, transactions)
                session.commit()
                print(f"Transactions processed: {len(transactions):,}")
            else:
                print("Transactions skipped (--skip-transactions)")
    finally:
        engine.dispose()

    print("Demo data seed complete.")


if __name__ == "__main__":
    main()
