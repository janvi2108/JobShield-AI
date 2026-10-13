import pytest
from fastapi.testclient import TestClient
from backend.app.main import app


@pytest.fixture
def client():
    """Create a FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client


def test_root_endpoint(client: TestClient):
    """Ensure the root endpoint returns service metadata."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert "JobShield AI" in data["service"]
    assert data["health"] == "/api/health"


def test_health_endpoint_success(client: TestClient):
    """Ensure GET /api/health returns HTTP 200 and required fields."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "jobshield-ai-backend"
    assert "version" in data
    assert "environment" in data
    assert "timestamp" in data
    assert "model_status" in data
    assert data["model_status"] in ["pending_training", "trained", "degraded"]


def test_health_endpoint_details(client: TestClient):
    """Verify health endpoint details contain API prefix and subsystem status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()

    assert "details" in data
    assert data["details"]["api_prefix"] == "/api"
    assert "model_subsystem" in data["details"]


def test_cors_headers_allowed(client: TestClient):
    """Verify that requests with allowed frontend origins succeed."""
    response = client.get(
        "/api/health",
        headers={"Origin": "http://localhost:5173"},
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:5173"
