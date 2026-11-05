from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from tests.conftest import ACCOUNT_IDS, REFERENCE_TIME, build_csv


def _row(
    *,
    index: int,
    from_index: int = 0,
    to_index: int = 1,
    amount: float = 100.0,
    label: int = 0,
    timestamp: str | None = None,
    device_id: str = "device-test",
) -> dict[str, object]:
    return {
        "id": str(UUID(int=10_000 + index)),
        "from_account": str(ACCOUNT_IDS[from_index]),
        "to_account": str(ACCOUNT_IDS[to_index]),
        "amount": f"{amount:.2f}",
        "currency": "usd",
        "timestamp": timestamp or REFERENCE_TIME.isoformat(),
        "device_id": device_id,
        "ip_address": "198.51.100.10",
        "channel": "MOBILE",
        "label": label,
    }


def test_ingest_csv_and_read_back(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", build_csv([_row(index=1)]), "text/csv")},
    )

    assert response.status_code == 201
    assert response.json()["accepted"] == 1
    assert response.json()["filename"] == "transactions.csv"

    transaction_id = str(UUID(int=10_001))
    detail = client.get(f"/api/v1/transactions/{transaction_id}")
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["amount"] == 100.0
    assert payload["currency"] == "USD"
    assert payload["channel"] == "mobile"
    assert payload["label"] == 0


def test_ingestion_rejects_unknown_accounts_and_writes_nothing(
    client: TestClient,
) -> None:
    unknown = UUID(int=999_999)
    row = _row(index=2)
    row["to_account"] = str(unknown)

    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", build_csv([row]), "text/csv")},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "unknown_accounts"
    assert str(unknown) in body["error"]["details"]["missing_accounts"]

    listing = client.get("/api/v1/transactions")
    assert listing.json()["total"] == 0


def test_ingestion_is_all_or_nothing_on_invalid_rows(client: TestClient) -> None:
    rows = [_row(index=3), _row(index=4, amount=-50)]

    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", build_csv(rows), "text/csv")},
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "csv_validation_failed"
    assert body["error"]["details"]["error_count"] == 1
    assert body["error"]["details"]["errors"][0]["field"] == "amount"
    assert client.get("/api/v1/transactions").json()["total"] == 0


def test_ingestion_rejects_duplicate_ids_in_file(client: TestClient) -> None:
    rows = [_row(index=5), _row(index=5, amount=200)]

    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", build_csv(rows), "text/csv")},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "csv_validation_failed"


def test_ingestion_rejects_ids_that_already_exist(client: TestClient) -> None:
    content = build_csv([_row(index=6)])
    first = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", content, "text/csv")},
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.csv", content, "text/csv")},
    )
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "duplicate_transaction_ids"


def test_ingestion_requires_expected_columns(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions/ingest",
        files={
            "file": (
                "transactions.csv",
                b"id,amount\n1,100\n",
                "text/csv",
            )
        },
    )

    assert response.status_code == 422
    body = response.json()
    assert body["error"]["code"] == "csv_missing_columns"
    assert "from_account" in body["error"]["details"]["missing"]


def test_ingestion_rejects_non_csv_extension(client: TestClient) -> None:
    response = client.post(
        "/api/v1/transactions/ingest",
        files={"file": ("transactions.json", b"[]", "application/json")},
    )

    assert response.status_code == 415
    assert response.json()["error"]["code"] == "unsupported_file_type"


def test_ingestion_rejects_oversized_upload(client: TestClient, app) -> None:
    original_limit = app.state.settings.max_upload_bytes
    app.state.settings.max_upload_bytes = 10
    try:
        response = client.post(
            "/api/v1/transactions/ingest",
            files={
                "file": (
                    "transactions.csv",
                    b"a" * 20,
                    "text/csv",
                )
            },
        )
    finally:
        app.state.settings.max_upload_bytes = original_limit

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "file_too_large"
