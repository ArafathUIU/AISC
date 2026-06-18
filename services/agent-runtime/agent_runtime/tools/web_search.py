"""Web Search Tool — searches the web for information."""

from __future__ import annotations

from typing import Any

import httpx

from .base import BaseTool, ToolResult


class WebSearchTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="web_search",
            description="Search the web for current information, documentation, and research",
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        if not query:
            return ToolResult(success=False, error="query is required")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(
                    "https://api.duckduckgo.com/",
                    params={"q": query, "format": "json", "no_html": 1},
                )
                if response.status_code == 200:
                    data = response.json()
                    results = []
                    for item in data.get("RelatedTopics", [])[:5]:
                        if isinstance(item, dict):
                            results.append({
                                "title": item.get("Text", ""),
                                "url": item.get("FirstURL", ""),
                            })
                    return ToolResult(success=True, output={"results": results})
                return ToolResult(
                    success=False, error=f"Search failed: {response.status_code}"
                )
        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query",
                },
            },
            "required": ["query"],
        }
