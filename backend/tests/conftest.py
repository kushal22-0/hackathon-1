from __future__ import annotations

import csv
import io
from collections.abc import Iterator
from datetime import UTC, date, datetime, timedelta
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import DetectionSettings, Settings
from app.main import create_app
from app.models.account import Account, Customer
from app.models.enums import Channel
from app.models.transaction import Transaction
from app.repositories.container import seed_memory_store

CUSTOMER_IDS = [UUID(int=100 + index) for index in range(5)]
ACCOUNT_IDS = [UUID(int=200 + index) for index in range(5)]
REFERENCE_TIME = datetime(2026, 10, 1, 12, 0, tzinfo=UTC)


def make_customer(index: int) -> Customer:
    return Customer(
        id=CUSTOMER_IDS[index],
        external_id=f"CUST-TEST-{index}",
        full_name=f"Test Customer {index}",
        email=f"test{index}@example.com",
        country="US",
    )


def make_account(index: int) -> Account:
    return Account(
        id=ACCOUNT_IDS[index],
        customer_id=CUSTOMER_IDS[index],
        account_number=f"TEST-ACCOUNT-{index}",
        account_type="checking",
        currency="USD",
        status="active",
        balance=10_000 + index,
        opened_at=date(2024, 1, 1),
    )


def make_transaction(
    index: int,
    *,
    from_index: int = 0,
    to_index: int = 1,
    amount: float = 100.0,
    timestamp: datetime | None = None,
    channel: Channel = Channel.MOBILE,
    label: int | None = 0,
    device_id: str | None = None,
    ip_address: str | None = None,
) -> Transaction:
    return Transaction(
        id=UUID(int=1_000 + index),
        from_account=ACCOUNT_IDS[from_index],
        to_account=ACCOUNT_IDS[to_index],
        amount=amount,
        currency="USD",
        timestamp=timestamp
        or REFERENCE_TIME - timedelta(hours=index),
        device_id=device_id or f"device-{index % 3}",
        ip_address=ip_address or f"192.0.2.{index % 5 + 1}",
        channel=channel,
        label=label,
    )


def build_csv(rows: list[dict[str, object]]) -> bytes:
    fieldnames = [
        "id",
        "from_account",
        "to_account",
        "amount",
        "currency",
        "timestamp",
        "device_id",
        "ip_address",
        "channel",
        "label",
    ]
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")


def create_test_app(
    *, detection: DetectionSettings | None = None
) -> FastAPI:
    application = create_app(
        Settings(
            environment="test",
            repository_backend="memory",
            max_upload_bytes=10 * 1024 * 1024,
            max_ingest_rows=10_000,
            detection=detection or DetectionSettings(),
        )
    )
    seed_memory_store(
        application.state.memory_repositories.store,
        customers=[make_customer(index) for index in range(5)],
        accounts=[make_account(index) for index in range(5)],
    )
    return application


@pytest.fixture()
def app() -> FastAPI:
    return create_test_app()


@pytest.fixture()
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client
