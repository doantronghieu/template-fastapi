"""Health check endpoint tests."""

from fastapi.testclient import TestClient


def test_health_check(sync_client: TestClient):
    """Verify health endpoint returns OK status."""
    response = sync_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
