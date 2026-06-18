"""Git Operations Tool — stage, commit, push code changes."""

from __future__ import annotations

import subprocess
from typing import Any

from .base import BaseTool, ToolResult


class GitOpsTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="git_ops",
            description="Stage, commit, and push code changes to git repository",
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "status")
        path = kwargs.get("path", ".")

        try:
            if operation == "status":
                proc = subprocess.run(
                    ["git", "-C", path, "status", "--short"],
                    capture_output=True, text=True, timeout=30,
                )
                return ToolResult(
                    success=True,
                    output={"status": proc.stdout.strip()},
                )

            if operation == "stage":
                files = kwargs.get("files", ".")
                subprocess.run(
                    ["git", "-C", path, "add"] + ([files] if files != "." else ["-A"]),
                    capture_output=True, text=True, timeout=30,
                )
                return ToolResult(success=True, output={"staged": files})

            if operation == "commit":
                message = kwargs.get("message", "Automated commit")
                proc = subprocess.run(
                    ["git", "-C", path, "commit", "-m", message],
                    capture_output=True, text=True, timeout=30,
                )
                return ToolResult(
                    success=proc.returncode == 0,
                    output={"output": proc.stdout.strip()},
                )

            return ToolResult(success=False, error=f"Unknown operation: {operation}")

        except Exception as e:
            return ToolResult(success=False, error=str(e))

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["status", "stage", "commit"],
                    "description": "Git operation to perform",
                },
                "path": {
                    "type": "string",
                    "description": "Repository path",
                    "default": ".",
                },
                "files": {
                    "type": "string",
                    "description": "Files to stage (for stage operation)",
                },
                "message": {
                    "type": "string",
                    "description": "Commit message (for commit operation)",
                },
            },
            "required": ["operation"],
        }
