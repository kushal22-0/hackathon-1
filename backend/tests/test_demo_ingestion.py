from __future__ import annotations

import csv
from pathlib import Path

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.models.account import Account, Customer
from app.repositories.container import seed_memory_store

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"


def _load_master_data() -> tuple[list[Customer], list[Account]]:
    with (DATA_DIR / "customers.csv").open(
        newline="", encoding="utf-8"
    ) as handle:
        customers = [
            Customer.model_validate(row) for row in csv.DictReader(handle)
        ]
    with (DATA_DIR / "accounts.csv").open(newline="", encoding="utf-8") as handle:
        accounts = [
            Account.model_validate(row) for row in csv.DictReader(handle)
        ]
    return customers, accounts


def test_generated_sample_ingests_end_to_end() -> None:
    app = create_app(
        Settings(
            environment="test",
            repository_backend="memory",
            max_upload_bytes=10 * 1024 * 1024,
            max_ingest_rows=10_000,
        )
    )
    customers, accounts = _load_master_data()
    seed_memory_store(
        app.state.memory_repositories.store,
        customers=customers,
        accounts=accounts,
    )

    content = (DATA_DIR / "sample_transactions.csv").read_bytes()
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/transactions/ingest",
            files={
                "file": ("sample_transactions.csv", content, "text/csv"),
            },
        )
        assert response.status_code == 201
        assert response.json()["accepted"] == 5_000

        all_transactions = client.get(
            "/api/v1/transactions", params={"page_size": 1}
        ).json()
        fraud_transactions = client.get(
            "/api/v1/transactions",
            params={"label": 1, "page_size": 1},
        ).json()

    assert all_transactions["total"] == 5_000
    assert fraud_transactions["total"] == 500
