from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def test_health_is_public_and_typed() -> None:
    app = create_app(Settings(environment="test", app_version="0.1.0-test"))
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "FraudNet AI API",
        "version": "0.1.0-test",
        "environment": "test",
    }
