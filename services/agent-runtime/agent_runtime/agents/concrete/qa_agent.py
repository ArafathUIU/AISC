"""QA Agent — generates tests with coverage and mutation analysis."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

QA_SYSTEM_PROMPT = """\
You are an expert QA Engineer. Generate comprehensive test suites from
source code and requirements. Cover happy path, edge cases, error paths,
and boundary conditions.

Requirements:
- Use pytest conventions (fixtures, parametrize)
- Mock external dependencies
- Cover line and branch coverage targets
- Include integration tests for API endpoints
- Add edge case tests (null, empty, max values)
- Use descriptive test names

Output ONLY valid JSON:
{
  "test_files": [
    {
      "path": "tests/test_module.py",
      "content": "test code...",
      "covers": ["function_name", "endpoint"]
    }
  ],
  "coverage_target": 90,
  "test_count": 10,
  "summary": "what was tested"
}
"""

_MOCK_TESTS = [
    {
        "path": "tests/test_models.py",
        "content": (
            "import pytest\n"
            "from src.models.user import UserCreate\n\n\n"
            "class TestUserCreate:\n"
            "    def test_valid_user(self) -> None:\n"
            '        user = UserCreate(email="a@b.com", password="12345678", display_name="Test")\n'
            "        assert user.email == \"a@b.com\"\n\n"
            "    def test_invalid_email(self) -> None:\n"
            "        with pytest.raises(Exception):\n"
            '            UserCreate(email="invalid", password="12345678", display_name="Test")\n\n'
            "    def test_short_password(self) -> None:\n"
            "        with pytest.raises(Exception):\n"
            '            UserCreate(email="a@b.com", password="short", display_name="Test")\n\n'
            "    def test_empty_display_name(self) -> None:\n"
            "        with pytest.raises(Exception):\n"
            '            UserCreate(email="a@b.com", password="12345678", display_name="")\n'
        ),
        "covers": ["UserCreate", "validation"],
    },
    {
        "path": "tests/test_routes.py",
        "content": (
            "from fastapi.testclient import TestClient\n"
            "from src.main import app\n\n"
            "client = TestClient(app)\n\n\n"
            "class TestUserRoutes:\n"
            "    def test_create_user_success(self) -> None:\n"
            "        response = client.post(\"/users/\", json={\n"
            '            "email": "new@test.com",\n'
            '            "password": "securepass123",\n'
            '            "display_name": "New User",\n'
            "        })\n"
            "        assert response.status_code == 201\n\n"
            "    def test_create_user_invalid_email(self) -> None:\n"
            "        response = client.post(\"/users/\", json={\n"
            '            "email": "bad-email",\n'
            '            "password": "securepass123",\n'
            '            "display_name": "User",\n'
            "        })\n"
            "        assert response.status_code == 422\n"
        ),
        "covers": ["POST /users/", "validation"],
    },
]


class QAAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="qa-agent", agent_type=AgentType.QA)
        self._router = router
        self.logger = get_logger("agent.qa")

    async def generate(self, task: TaskContext) -> Artifact:
        source_code = task.input.get("source_code", task.input.get("code", ""))
        requirements = task.input.get("requirements", "")

        messages = [
            {"role": "system", "content": QA_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate tests for:\nCode: {source_code}\n"
                    f"Requirements: {requirements}"
                ),
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.3, max_tokens=4096,
                complexity=TaskComplexity.MODERATE,
            )
            content = response.content
        else:
            content = self._build_mock_tests()

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.TEST_FILE,
            name="Generated test suite",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"test_count": len(_MOCK_TESTS)},
        )

    def _build_mock_tests(self) -> str:
        return json.dumps({
            "test_files": _MOCK_TESTS,
            "coverage_target": 90,
            "test_count": 4,
            "summary": "Unit + integration tests for user endpoints",
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            files = data.get("test_files", [])
            if not files:
                issues.append("No test files generated")
            if data.get("test_count", 0) < 3:
                issues.append("Fewer than 3 tests")
            for tf in files:
                if "assert" not in tf.get("content", ""):
                    issues.append(
                        f"No assertions in {tf.get('path', 'unknown')}"
                    )

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    [f"Generated {len(files)} test files"]
                    if not issues else []
                ),
                improvements=issues,
            )
        except json.JSONDecodeError:
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=0.0,
                issues=["Output is not valid JSON"],
                strengths=[],
                improvements=["Return valid JSON"],
            )
