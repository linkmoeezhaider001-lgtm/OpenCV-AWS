from types import SimpleNamespace

from app.routers.health import health


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalar(self):
        return self.value


class FakeSession:
    def __init__(self, vector_active=True):
        self.vector_active = vector_active

    def execute(self, query):
        if "pg_extension" in str(query):
            return FakeResult(1 if self.vector_active else None)
        return FakeResult(1)


def test_health_reports_healthy_when_dependencies_are_available(monkeypatch):
    monkeypatch.setenv("GOOGLE_API_KEY", "configured")
    response = SimpleNamespace(status_code=None)

    result = health(response, FakeSession(vector_active=True))

    assert response.status_code == 200
    assert result.status == "healthy"
    assert result.database == "connected"
    assert result.pgvector_extension == "active"
    assert result.gemini_api_configured is True


def test_health_reports_service_unavailable_when_pgvector_is_missing(monkeypatch):
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    response = SimpleNamespace(status_code=None)

    result = health(response, FakeSession(vector_active=False))

    assert response.status_code == 503
    assert result.status == "unhealthy"
    assert result.database == "connected"
    assert result.pgvector_extension == "missing"
    assert result.gemini_api_configured is False
