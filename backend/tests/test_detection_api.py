from __future__ import annotations

from datetime import timedelta
from uuid import UUID

from fastapi.testclient import TestClient

from app.core.config import DetectionSettings
from app.models.alert import Alert
from app.models.enums import AlertStatus
from app.repositories.container import seed_memory_store
from tests.conftest import (
    REFERENCE_TIME,
    create_test_app,
    make_transaction,
)

DETECTION_SETTINGS = DetectionSettings(ml_estimators=50)


def _history(count: int = 80) -> list:
    return [
        make_transaction(
            index,
            from_index=index % 5,
            to_index=(index + 1) % 5,
            amount=100 + index % 7 * 10,
            timestamp=REFERENCE_TIME - timedelta(hours=count - index),
            device_id=f"device-{index % 5}",
            ip_address=f"192.0.2.{index % 5 + 1}",
        )
        for index in range(count)
    ]


def _seed_large_transfer(client: TestClient):
    history = _history()
    target = make_transaction(
        900,
        from_index=0,
        to_index=2,
        amount=25_000,
        timestamp=REFERENCE_TIME,
        device_id="fresh-device",
        ip_address="198.51.100.99",
    )
    seed_memory_store(
        client.app.state.memory_repositories.store,
        transactions=history + [target],
    )
    return target, history


def test_assess_transaction_creates_alert_and_persists_evidence() -> None:
    app = create_test_app(detection=DETECTION_SETTINGS)
    with TestClient(app) as client:
        target, _ = _seed_large_transfer(client)

        response = client.post(
            f"/api/v1/detection/transactions/{target.id}"
        )

        assert response.status_code == 200
        body = response.json()
        assert body["transaction_id"] == str(target.id)
        assert body["alert_required"] is True
        assert body["alert_created"] is True
        assert body["alert_updated"] is False
        assert body["risk_score"] >= body["alert_threshold"]
        assert body["risk_level"] in {"high", "critical"}
        assert body["model_status"] == "ready"
        assert body["training_rows"] == 81
        assert any(
            hit["code"] == "large_transfer" for hit in body["rule_hits"]
        )
        assert body["explanation"].startswith("Alert raised")
        assert body["alert"]["rule_hits"] == body["rule_hits"]
        assert body["alert"]["evidence"]["scoring"]["risk_score"] == (
            body["risk_score"]
        )
        assert body["alert"]["evidence"]["rule_evidence"][
            "large_transfer"
        ]["amount"] == 25_000.0

        alert_id = body["alert"]["id"]
        detail = client.get(f"/api/v1/alerts/{alert_id}")
        assert detail.status_code == 200
        assert detail.json()["transaction_id"] == str(target.id)

        listing = client.get(
            "/api/v1/alerts",
            params={"transaction_id": str(target.id)},
        )
        assert listing.status_code == 200
        assert listing.json()["total"] == 1


def test_rescanning_updates_the_same_active_alert() -> None:
    app = create_test_app(detection=DETECTION_SETTINGS)
    with TestClient(app) as client:
        target, _ = _seed_large_transfer(client)

        first = client.post(
            f"/api/v1/detection/transactions/{target.id}"
        ).json()
        second = client.post(
            f"/api/v1/detection/transactions/{target.id}"
        ).json()

        assert second["alert_created"] is False
        assert second["alert_updated"] is True
        assert second["alert"]["id"] == first["alert"]["id"]
        assert client.get("/api/v1/alerts").json()["total"] == 1


def test_scan_accepts_explicit_transactions_and_reports_unknown_ids() -> None:
    app = create_test_app(detection=DETECTION_SETTINGS)
    with TestClient(app) as client:
        target, history = _seed_large_transfer(client)

        response = client.post(
            "/api/v1/detection/scan",
            json={
                "transaction_ids": [
                    str(target.id),
                    str(history[-1].id),
                ]
            },
        )

        assert response.status_code == 200
        body = response.json()
        assert body["scanned"] == 2
        assert body["alerts_required"] == 1
        assert body["alerts_created"] == 1
        assert len(body["alert_ids"]) == 1
        assert body["model_status"] == "ready"

        missing = client.post(
            "/api/v1/detection/scan",
            json={"transaction_ids": [str(UUID(int=999_999))]},
        )
        assert missing.status_code == 404
        assert missing.json()["error"]["code"] == "transactions_not_found"


def test_scan_recent_limit_and_batch_cap() -> None:
    app = create_test_app(
        detection=DetectionSettings(
            ml_estimators=50, max_batch_size=2
        )
    )
    with TestClient(app) as client:
        transactions = _history(5)
        seed_memory_store(
            client.app.state.memory_repositories.store,
            transactions=transactions,
        )

        limited = client.post(
            "/api/v1/detection/scan", json={"limit": 2}
        )
        assert limited.status_code == 200
        assert limited.json()["scanned"] == 2

        too_large = client.post(
            "/api/v1/detection/scan",
            json={
                "transaction_ids": [
                    str(transaction.id) for transaction in transactions[:3]
                ]
            },
        )
        assert too_large.status_code == 422
        assert too_large.json()["error"]["code"] == "batch_too_large"


def _alert(index: int, score: float, status: AlertStatus) -> Alert:
    created_at = REFERENCE_TIME + timedelta(minutes=index)
    return Alert(
        id=UUID(int=7_000 + index),
        transaction_id=UUID(int=8_000 + index),
        risk_score=score,
        rule_hits=[],
        ml_score=50,
        explanation=f"Alert {index}",
        evidence={},
        status=status,
        created_at=created_at,
        updated_at=created_at,
    )


def test_alert_search_filters_sorting_and_pagination() -> None:
    app = create_test_app()
    with TestClient(app) as client:
        seed_memory_store(
            client.app.state.memory_repositories.store,
            alerts=[
                _alert(0, 30, AlertStatus.OPEN),
                _alert(1, 50, AlertStatus.DISMISSED),
                _alert(2, 70, AlertStatus.OPEN),
                _alert(3, 80, AlertStatus.OPEN),
                _alert(4, 90, AlertStatus.ESCALATED),
            ],
        )

        default_page = client.get("/api/v1/alerts").json()
        assert default_page["total"] == 5
        assert default_page["items"][0]["risk_score"] == 90

        dismissed = client.get(
            "/api/v1/alerts", params={"status": "dismissed"}
        ).json()
        assert dismissed["total"] == 1
        assert dismissed["items"][0]["status"] == "dismissed"

        high_risk = client.get(
            "/api/v1/alerts", params={"min_risk_score": 75}
        ).json()
        assert high_risk["total"] == 2

        ascending = client.get(
            "/api/v1/alerts",
            params={"sort_by": "risk_score", "sort_dir": "asc"},
        ).json()
        assert [item["risk_score"] for item in ascending["items"]] == [
            30,
            50,
            70,
            80,
            90,
        ]

        second_page = client.get(
            "/api/v1/alerts", params={"page": 2, "page_size": 2}
        ).json()
        assert second_page["page"] == 2
        assert second_page["total_pages"] == 3
        assert len(second_page["items"]) == 2
        assert second_page["items"][0]["risk_score"] == 70

        invalid = client.get(
            "/api/v1/alerts",
            params={"min_risk_score": 90, "max_risk_score": 20},
        )
        assert invalid.status_code == 422
        assert invalid.json()["error"]["code"] == "validation_error"


def test_large_transfer_alerts_during_cold_start_without_ml() -> None:
    app = create_test_app()
    with TestClient(app) as client:
        target = make_transaction(
            950,
            from_index=0,
            to_index=1,
            amount=15_000,
            timestamp=REFERENCE_TIME,
        )
        seed_memory_store(
            client.app.state.memory_repositories.store,
            transactions=[target],
        )

        response = client.post(
            f"/api/v1/detection/transactions/{target.id}"
        )

    assert response.status_code == 200
    body = response.json()
    assert body["model_status"] == "insufficient_data"
    assert body["ml_score"] == 0
    assert body["rule_score"] == 70
    assert body["risk_score"] == 70
    assert body["alert_required"] is True
    assert body["alert_created"] is True
    assert "rule score carries full weight" in body["explanation"]


def test_alert_not_found_uses_error_envelope() -> None:
    app = create_test_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/alerts/00000000-0000-0000-0000-000000000001"
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "alert_not_found"
