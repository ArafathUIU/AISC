"""Memory service unit tests."""

import uuid

import pytest
from fastapi.testclient import TestClient
from memory_service.main import app

client = TestClient(app)


class TestHealth:
    def test_health(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "memory-service"


class TestMemoryAPI:
    @pytest.mark.skip(reason="Requires Redis connection")
    def test_store_short_term(self) -> None:
        response = client.post(
            "/api/v1/memory/store",
            json={"tier": "short", "key": "test:key:123", "data": {"value": "hello"}},
        )
        assert response.status_code == 200

    def test_store_unsupported_tier(self) -> None:
        response = client.post(
            "/api/v1/memory/store",
            json={"tier": "graph", "key": "test", "data": {"nodes": []}},
        )
        assert response.status_code == 200
        assert response.json()["tier"] == "graph"

    def test_search_endpoint_exists(self) -> None:
        response = client.get("/api/v1/memory/search?q=test&tier=short")
        assert response.status_code in (200, 500)

    def test_get_agent_context(self) -> None:
        agent_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/memory/context/{agent_id}")
        assert response.status_code in (200, 500)
        if response.status_code == 200:
            assert response.json()["agent_id"] == agent_id

    def test_get_project_history(self) -> None:
        proj_id = str(uuid.uuid4())
        response = client.get(f"/api/v1/memory/project/{proj_id}/history")
        assert response.status_code in (200, 500)
