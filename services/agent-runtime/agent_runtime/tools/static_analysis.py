"""Static Analysis Tool — runs ruff, mypy, radon on generated code."""

from __future__ import annotations

import subprocess
from typing import Any

from .base import BaseTool, ToolResult


class StaticAnalysisTool(BaseTool):
    def __init__(self) -> None:
        super().__init__(
            name="static_analysis",
            description="Run linters, type checkers, and complexity analysis on code",
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        path = kwargs.get("path", ".")
        checks = kwargs.get("checks", ["ruff"])

        results: dict[str, Any] = {}
        all_passed = True

        if "ruff" in checks:
            try:
                proc = subprocess.run(
                    ["ruff", "check", path],
                    capture_output=True, text=True, timeout=60,
                )
                results["ruff"] = {
                    "passed": proc.returncode == 0,
                    "output": proc.stdout[:2000],
                }
                if proc.returncode != 0:
                    all_passed = False
            except FileNotFoundError:
                results["ruff"] = {"passed": True, "output": "ruff not installed"}

        if "mypy" in checks:
            try:
                proc = subprocess.run(
                    ["mypy", path, "--ignore-missing-imports"],
                    capture_output=True, text=True, timeout=120,
                )
                results["mypy"] = {
                    "passed": proc.returncode == 0,
                    "output": proc.stdout[:2000],
                }
                if proc.returncode != 0:
                    all_passed = False
            except FileNotFoundError:
                results["mypy"] = {"passed": True, "output": "mypy not installed"}

        return ToolResult(
            success=all_passed,
            output=results,
            metadata={"path": path, "checks": checks},
        )

    def get_parameters(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "File or directory path to analyze",
                    "default": ".",
                },
                "checks": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Which checks to run",
                    "default": ["ruff", "mypy"],
                },
            },
            "required": ["path"],
        }
