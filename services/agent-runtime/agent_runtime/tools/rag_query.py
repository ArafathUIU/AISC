"""RAG Query Tool — queries the RAG service for relevant context."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseTool, ToolResult


class RAGQueryTool(BaseTool):
    def __init__(self, rag_service_url: str = "http://localhost:8006") -> None:
        super().__init__(
            name="rag_query",
            description="Search the knowledge base for relevant code, docs, and patterns",
        )
        self.rag_service_url = rag_service_url

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        collection = kwargs.get("collection")
        limit = kwargs.get("limit", 5)

        if not query:
            return ToolResult(success=False, error="query is required")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                payload: dict[str, Any] = {"query": query, "limit": limit}
                if collection:
                    payload["collection"] = collection
                response = await client.post(
                    f"{self.rag_service_url}/api/v1/rag/query",
                    json=payload,
                )
                if response.status_code == 200:
                    return ToolResult(
                        success=True,
                        output=response.json(),
                    )
                return ToolResult(
                    success=False,
                    error=f"RAG service returned {response.status_code}",
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query text",
                },
                "collection": {
                    "type": "string",
                    "description": "Optional collection name to filter",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results to return",
                    "default": 5,
                },
            },
            "required": ["query"],
        }
