"""Developer Agent — generates production-quality code from specs."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

DEVELOPER_SYSTEM_PROMPT = """\
You are an expert Software Developer. Generate production-quality code
from API specifications and architecture documents.

Requirements:
- Use type hints everywhere
- Include docstrings on public functions
- Add proper error handling
- Follow PEP 8 and language best practices
- Use dependency injection patterns
- Validate all inputs
- Include constructor injection for dependencies

Output ONLY valid JSON:
{
  "files": [
    {
      "path": "relative/path/to/file.py",
      "language": "python",
      "content": "code here..."
    }
  ],
  "dependencies": ["package>=version"],
  "summary": "what was generated"
}
"""

_MOCK_CODE_FILES = [
    {
        "path": "src/models/user.py",
        "language": "python",
        "content": (
            'from datetime import datetime\n'
            'from uuid import UUID, uuid4\n\n'
            'from pydantic import BaseModel, EmailStr, Field\n\n\n'
            'class UserCreate(BaseModel):\n'
            '    email: EmailStr\n'
            '    password: str = Field(min_length=8)\n'
            '    display_name: str = Field(min_length=1, max_length=100)\n\n\n'
            'class UserResponse(BaseModel):\n'
            '    id: UUID\n'
            '    email: str\n'
            '    display_name: str\n'
            '    created_at: datetime\n'
            '    model_config = {"from_attributes": True}\n'
        ),
    },
    {
        "path": "src/routes/users.py",
        "language": "python",
        "content": (
            'from typing import Any\n'
            'from uuid import UUID\n\n'
            'from fastapi import APIRouter, Depends, HTTPException\n\n'
            'from ..models.user import UserCreate, UserResponse\n\n'
            'router = APIRouter(prefix="/users", tags=["users"])\n\n\n'
            '@router.post("/", response_model=UserResponse)\n'
            'async def create_user(body: UserCreate) -> Any:\n'
            '    """Create a new user."""\n'
            '    return {"id": str(UUID(int=0)), '
            '"email": body.email, '
            '"display_name": body.display_name}\n'
        ),
    },
    {
        "path": "src/services/user_service.py",
        "language": "python",
        "content": (
            'from __future__ import annotations\n\n'
            'from typing import Any\n\n\n'
            'class UserService:\n'
            '    """User business logic service."""\n\n'
            '    def __init__(self, db_session: Any) -> None:\n'
            '        self._db = db_session\n\n'
            '    async def create(self, email: str, name: str) -> dict[str, Any]:\n'
            '        """Create user with validation."""\n'
            '        if not email or "@" not in email:\n'
            '            raise ValueError("Invalid email")\n'
            '        return {"email": email, "name": name, "created": True}\n'
        ),
    },
]


class DeveloperAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="developer-agent", agent_type=AgentType.DEVELOPER)
        self._router = router
        self.logger = get_logger("agent.developer")

    async def generate(self, task: TaskContext) -> Artifact:
        spec = task.input.get("api_spec", task.input.get("specification", ""))
        language = task.input.get("language", "python")
        framework = task.input.get("framework", "fastapi")

        messages = [
            {"role": "system", "content": DEVELOPER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Generate {language} code using {framework} for:\n{spec}"
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
            content = self._build_mock_code(language, framework)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.SOURCE_CODE,
            name=f"Generated {language} code ({framework})",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"language": language, "framework": framework},
        )

    def _build_mock_code(self, language: str, framework: str) -> str:
        return json.dumps({
            "files": _MOCK_CODE_FILES,
            "dependencies": ["fastapi>=0.111", "pydantic>=2.7", "uvicorn>=0.29"],
            "summary": f"Generated {language} code using {framework} with 3 files",
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            files = data.get("files", [])
            if not files:
                issues.append("No files generated")
            if not data.get("dependencies"):
                issues.append("No dependencies listed")

            for f in files:
                content = f.get("content", "")
                if not content:
                    issues.append(f"Empty file: {f.get('path', 'unknown')}")
                if "import" not in content and f.get("language") == "python":
                    issues.append(f"No imports in {f.get('path', 'unknown')}")

            score = 100.0 - (len(issues) * 12)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    [f"Generated {len(files)} files with deps"]
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
