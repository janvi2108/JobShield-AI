import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.schemas.analysis import JobAnalysisRequest
from backend.app.services.prediction_service import (
    analyze_job_posting,
    extract_heuristic_signals,
    load_model_bundle,
    load_metrics_data,
)


@pytest.fixture
def test_client():
    return TestClient(app)


def test_heuristic_signals_extraction():
    req = JobAnalysisRequest(
        title="Immediate Hire Wire Transfer Telegram",
        description="Earn $1000/week guaranteed approval! No interview required. Send registration fee via telegram to start immediately.",
        has_company_logo=False,
    )
    signals = extract_heuristic_signals(req)
    assert len(signals) >= 3
    assert any("fee" in s.lower() or "financial" in s.lower() for s in signals)
    assert any("telegram" in s.lower() for s in signals)
    assert any("logo" in s.lower() for s in signals)


def test_model_bundle_loading():
    bundle = load_model_bundle()
    assert bundle is not None
    assert "model" in bundle
    assert "preprocessor" in bundle
    assert "decision_threshold" in bundle
    assert bundle["decision_threshold"] > 0.0


def test_metrics_data_loading():
    metrics = load_metrics_data()
    assert metrics is not None
    assert "candidate_comparison" in metrics
    assert "test_evaluation" in metrics
    assert "selected_model" in metrics
    assert len(metrics["candidate_comparison"]) == 4


def test_api_health_endpoint(test_client):
    response = test_client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["model_status"] == "trained"


def test_api_metrics_endpoint(test_client):
    response = test_client.get("/api/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "selected_model" in data
    assert "test_evaluation" in data
    assert data["selected_model"]["name"] == "Linear Support Vector Machine"


def test_api_analyze_scam_posting(test_client):
    payload = {
        "title": "URGENT Data Entry Agent",
        "company_name": "QuickCash Inc",
        "description": "Urgent work from home job. Send $150 training fee via wire transfer or telegram before starting.",
        "requirements": "No interview or experience needed",
        "has_company_logo": False,
    }
    response = test_client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["is_fraudulent"] is True
    assert data["fraud_probability"] >= data["decision_threshold"]
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert len(data["heuristic_signals"]) > 0
    assert len(data["shap_values"]) > 0
    assert data["explanation"] is not None


def test_api_analyze_legitimate_posting(test_client):
    payload = {
        "title": "Software Engineering Intern - Platform Infrastructure",
        "company_name": "Datadog Cloud Systems",
        "company_profile": "Global cloud monitoring and security platform serving 25,000 customers worldwide.",
        "description": "Join our core infrastructure team as an intern. Build distributed microservices in Go and Python, work with senior mentors, and write unit and integration tests.",
        "requirements": "Currently enrolled in Computer Science degree. Experience with Git, Linux, and algorithms.",
        "benefits": "$45/hour compensation, full medical benefits, housing stipend, mentor matching.",
        "has_company_logo": True,
    }
    response = test_client.post("/api/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["is_fraudulent"] is False
    assert data["fraud_probability"] < data["decision_threshold"]
    assert data["risk_level"] == "LOW"
    assert data["verdict"] == "Likely Legitimate Employment Posting"


def test_api_analyze_validation_error_short_description(test_client):
    payload = {
        "title": "Job Title",
        "description": "Too short",  # less than 20 chars
    }
    response = test_client.post("/api/analyze", json=payload)
    assert response.status_code == 422  # Pydantic validation error
