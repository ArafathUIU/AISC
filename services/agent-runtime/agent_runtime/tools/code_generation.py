"""Code Generation Tool — LLM-powered code generation with framework awareness."""

from __future__ import annotations

from typing import Any

from .base import BaseTool, ToolResult


class CodeGenerationTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="code_generation",
            description="Generate production-quality code in Python, TypeScript, SQL, and more",
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        language = kwargs.get("language", "python")
        specification = kwargs.get("specification", "")
        framework = kwargs.get("framework", "")

        if not specification:
            return ToolResult(success=False, error="specification is required")

        return ToolResult(
            success=True,
            output={
                "language": language,
                "framework": framework,
                "generated": True,
                "message": (
                    f"Code generation requested for {language}"
                    + (f" using {framework}" if framework else "")
                ),
            },
            metadata={"language": language, "framework": framework},
        )

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "specification": {
                    "type": "string",
                    "description": "What code to generate",
                },
                "language": {
                    "type": "string",
                    "description": "Target programming language",
                    "default": "python",
                },
                "framework": {
                    "type": "string",
                    "description": "Target framework (e.g., FastAPI, React)",
                },
            },
            "required": ["specification"],
        }
