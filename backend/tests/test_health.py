from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_200_with_expected_shape():
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["api"]["status"] == "ok"
    assert "database" in body
    assert "ollama" in body
    assert body["status"] in ("ok", "degraded")
