"""Qdrant store — semantic vector memory."""

from __future__ import annotations

from typing import Any

from aisc_utils import get_logger, settings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams

logger = get_logger(__name__)

COLLECTIONS: dict[str, int] = {
    "code_embeddings": 768,
    "doc_embeddings": 768,
    "agent_memory": 1536,
    "test_embeddings": 768,
    "security_findings": 768,
    "error_patterns": 768,
    "knowledge_snippets": 3072,
}


class QdrantStore:
    def __init__(self) -> None:
        self._client: QdrantClient | None = None

    async def connect(self) -> None:
        self._client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
        logger.info("qdrant_connected", host=settings.qdrant_host)

    async def ensure_collections(self) -> None:
        if self._client is None:
            return
        for name, dims in COLLECTIONS.items():
            if not self._client.collection_exists(name):
                self._client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(size=dims, distance=Distance.COSINE),
                )
                logger.info("qdrant_collection_created", name=name)

    async def upsert(
        self, collection: str, point_id: str, vector: list[float], payload: dict[str, Any]
    ) -> None:
        if self._client is None:
            return
        self._client.upsert(
            collection_name=collection,
            points=[PointStruct(id=point_id, vector=vector, payload=payload)],
        )

    async def search(
        self,
        collection: str,
        vector: list[float],
        limit: int = 10,
        score_threshold: float = 0.0,
    ) -> list[dict[str, Any]]:
        if self._client is None:
            return []
        results = self._client.search(  # type: ignore[attr-defined]
            collection_name=collection,
            query_vector=vector,
            limit=limit,
            score_threshold=score_threshold,
        )
        return [
            {"id": r.id, "score": r.score, "payload": r.payload}
            for r in results
        ]

    async def delete_points(self, collection: str, point_ids: list[Any]) -> None:
        if self._client is None:
            return
        self._client.delete(
            collection_name=collection,
            points_selector=point_ids,
        )


qdrant_store = QdrantStore()
