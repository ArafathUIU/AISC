"""RAG service tests."""

from fastapi.testclient import TestClient
from rag_service.main import app

client = TestClient(app)


class TestHealth:
    def test_health(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["service"] == "rag-service"


class TestIngest:
    def test_ingest_single_document(self) -> None:
        response = client.post(
            "/api/v1/rag/ingest",
            json={
                "documents": [
                    {"content": "FastAPI is a modern web framework for Python."}
                ],
                "collection": "doc_embeddings",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ingested"] == 1
        assert data["collection"] == "doc_embeddings"

    def test_ingest_multiple_documents(self) -> None:
        response = client.post(
            "/api/v1/rag/ingest",
            json={
                "documents": [
                    {"content": "Python is a programming language."},
                    {"content": "FastAPI uses Python type hints."},
                ],
            },
        )
        assert response.status_code == 200
        assert response.json()["ingested"] == 2


class TestQuery:
    def test_query_returns_relevant_results(self) -> None:
        response = client.post(
            "/api/v1/rag/query",
            json={"query": "FastAPI"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert len(data["results"]) > 0

    def test_query_no_results(self) -> None:
        response = client.post(
            "/api/v1/rag/query",
            json={"query": "nonexistent_term_xyz"},
        )
        assert response.status_code == 200
        assert response.json()["total_found"] == 0

    def test_query_limit_respected(self) -> None:
        response = client.post(
            "/api/v1/rag/query",
            json={"query": "Python", "limit": 1},
        )
        assert response.status_code == 200
        assert len(response.json()["results"]) <= 1

    def test_query_validation_rejects_invalid(self) -> None:
        response = client.post(
            "/api/v1/rag/query",
            json={"query": "", "limit": 100},
        )
        assert response.status_code == 422


class TestCollections:
    def test_list_collections(self) -> None:
        response = client.get("/api/v1/rag/collections")
        assert response.status_code == 200
        data = response.json()
        assert "collections" in data
        assert "total_documents" in data
