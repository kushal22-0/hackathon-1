from __future__ import annotations

from datetime import timedelta

from fastapi.testclient import TestClient

from app.models.enums import Channel
from app.repositories.container import seed_memory_store
from tests.conftest import (
    ACCOUNT_IDS,
    REFERENCE_TIME,
    make_transaction,
)


def _seed(client: TestClient, count: int = 30) -> None:
    transactions = []
    for index in range(count):
        transactions.append(
            make_transaction(
                index,
                from_index=index % 5,
                to_index=(index + 1) % 5,
                amount=50 + index * 10,
                timestamp=REFERENCE_TIME - timedelta(minutes=index * 15),
                channel=Channel.MOBILE if index % 2 == 0 else Channel.WIRE,
                label=1 if index % 10 == 0 else 0,
                device_id=f"device-{index % 3}",
                ip_address=f"203.0.113.{index % 4 + 1}",
            )
        )
    seed_memory_store(
        client.app.state.memory_repositories.store,
        transactions=transactions,
    )


def test_pagination_metadata_and_default_sort(client: TestClient) -> None:
    _seed(client, 30)

    response = client.get(
        "/api/v1/transactions", params={"page": 2, "page_size": 10}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 30
    assert body["page"] == 2
    assert body["page_size"] == 10
    assert body["total_pages"] == 3
    assert len(body["items"]) == 10
    timestamps = [item["timestamp"] for item in body["items"]]
    assert timestamps == sorted(timestamps, reverse=True)


def test_account_filter_matches_both_directions(client: TestClient) -> None:
    _seed(client, 10)

    response = client.get(
        "/api/v1/transactions",
        params={"account_id": str(ACCOUNT_IDS[2]), "page_size": 200},
    )

    assert response.status_code == 200
    for item in response.json()["items"]:
        assert (
            item["from_account"] == str(ACCOUNT_IDS[2])
            or item["to_account"] == str(ACCOUNT_IDS[2])
        )


def test_amount_channel_label_device_and_time_filters(client: TestClient) -> None:
    _seed(client, 30)

    response = client.get(
        "/api/v1/transactions",
        params={
            "min_amount": 150,
            "max_amount": 220,
            "channel": "wire",
            "label": 0,
            "device_id": "device-1",
            "start_time": (REFERENCE_TIME - timedelta(hours=5)).isoformat(),
            "end_time": REFERENCE_TIME.isoformat(),
            "sort_by": "amount",
            "sort_dir": "asc",
            "page_size": 200,
        },
    )

    assert response.status_code == 200
    items = response.json()["items"]
    assert items
    assert all(150 <= item["amount"] <= 220 for item in items)
    assert all(item["channel"] == "wire" for item in items)
    assert all(item["label"] == 0 for item in items)
    assert all(item["device_id"] == "device-1" for item in items)
    amounts = [item["amount"] for item in items]
    assert amounts == sorted(amounts)


def test_empty_page_beyond_last_page(client: TestClient) -> None:
    _seed(client, 5)

    response = client.get(
        "/api/v1/transactions", params={"page": 99, "page_size": 10}
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["total"] == 5
    assert response.json()["total_pages"] == 1


def test_invalid_filters_use_error_envelope(client: TestClient) -> None:
    response = client.get(
        "/api/v1/transactions",
        params={"min_amount": 500, "max_amount": 100},
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_invalid_page_size_uses_error_envelope(client: TestClient) -> None:
    response = client.get(
        "/api/v1/transactions", params={"page_size": 201}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


def test_transaction_not_found_envelope(client: TestClient) -> None:
    response = client.get(
        "/api/v1/transactions/00000000-0000-0000-0000-000000000001"
    )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "transaction_not_found"


def test_unknown_route_uses_error_envelope(client: TestClient) -> None:
    response = client.get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "http_error"
