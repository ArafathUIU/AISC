"""RAG service — query and ingest routes."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

_documents: list[dict[str, Any]] = []


class QueryRequest(BaseModel):
    query: str
    collection: str | None = None
    limit: int = Field(default=5, ge=1, le=50)
    score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)


class IngestRequest(BaseModel):
    documents: list[dict[str, Any]]
    collection: str = "doc_embeddings"


class IngestResponse(BaseModel):
    ingested: int
    collection: str


@router.post("/query")
async def query_rag(body: QueryRequest) -> dict[str, Any]:
    query_lower = body.query.lower()
    results = [
        doc for doc in _documents
        if query_lower in str(doc.get("content", "")).lower()
    ][: body.limit]

    return {
        "results": results,
        "query": body.query,
        "total_found": len(results),
    }


@router.post("/ingest")
async def ingest_documents(body: IngestRequest) -> IngestResponse:
    for doc in body.documents:
        doc["_collection"] = body.collection
        _documents.append(doc)

    return IngestResponse(
        ingested=len(body.documents),
        collection=body.collection,
    )


@router.get("/collections")
async def list_collections() -> dict[str, Any]:
    collections: set[str] = {
        str(doc.get("_collection", "default")) for doc in _documents
    }
    return {"collections": sorted(collections), "total_documents": len(_documents)}
