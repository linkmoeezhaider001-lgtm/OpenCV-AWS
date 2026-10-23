import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app
from app.routers.tickets import clear_ticket_store


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _HealthySession:
    def execute(self, query):
        if "pg_extension" in str(query):
            return _ScalarResult(1)
        return _ScalarResult(1)


@pytest.fixture(autouse=True)
def isolated_api(monkeypatch):
    monkeypatch.setenv("API_KEY", "test-api-key")
    monkeypatch.setenv("GOOGLE_API_KEY", "test-gemini-key")
    app.dependency_overrides[get_db] = lambda: _HealthySession()
    clear_ticket_store()
    yield
    app.dependency_overrides.clear()
    clear_ticket_store()


@pytest.fixture
def client():
    return TestClient(app)


def test_unauthenticated_request(client):
    response = client.post(
        "/api/v1/tickets/agent-reply",
        json={"query": "How do I reset the service?"},
    )

    assert response.status_code == 401


def test_invalid_api_key(client):
    response = client.post(
        "/api/v1/tickets/agent-reply",
        headers={"X-API-Key": "invalid-key"},
        json={"query": "How do I reset the service?"},
    )

    assert response.status_code == 401


def test_health_check(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_ingest_and_reply_flow(client):
    ticket = {
        "ticket_id": "TECH-TEST-001",
        "title": "Database connection timeout",
        "description": (
            "The production API cannot connect to PostgreSQL after deployment. "
            "Connection attempts time out while the application is starting."
        ),
        "metadata": {"priority": "high"},
    }
    headers = {"X-API-Key": "test-api-key"}

    ingest_response = client.post(
        "/api/v1/tickets/ingest", headers=headers, json=ticket
    )

    assert ingest_response.status_code == 201
    assert ingest_response.json()["chunks_created"] > 0

    reply_response = client.post(
        "/api/v1/tickets/agent-reply",
        headers=headers,
        json={"query": "Why does the PostgreSQL connection time out?"},
    )

    assert reply_response.status_code == 200
    assert reply_response.json()["category"] == "technical_rag"
    assert "TECH-TEST-001" in reply_response.json()["sources_used"]


def test_billing_classification_routing(client):
    response = client.post(
        "/api/v1/tickets/agent-reply",
        headers={"X-API-Key": "test-api-key"},
        json={"query": "I need a refund for my invoice"},
    )

    assert response.status_code == 200
    assert response.json()["category"] == "billing"
    assert response.json()["sources_used"] == []
