"""Architect Agent — designs system architecture from requirements."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

ARCHITECT_SYSTEM_PROMPT = """\
You are an expert Software Architect. Design a complete system architecture
from product requirements. Produce structured, implementable designs.

Include:
1. System Overview — one paragraph summary
2. Service Decomposition — list of microservices with responsibilities
3. Data Architecture — database design, data flow
4. API Contracts — key endpoints per service
5. Technology Stack — specific technologies with versions and rationale
6. Security Architecture — auth flow, trust boundaries
7. Architecture Decisions — key tradeoffs with rationale (ADR format)
8. Diagrams — describe in text (Mermaid-compatible)

Output ONLY valid JSON:
{
  "system_overview": "...",
  "services": [
    {
      "name": "service-name",
      "responsibility": "...",
      "api_endpoints": [
        {"method": "GET", "path": "/api/...", "description": "..."}
      ],
      "data_owned": ["table1", "table2"],
      "dependencies": ["other-service"]
    }
  ],
  "database": {
    "tables": [
      {"name": "...", "columns": [{"name": "...", "type": "...", "constraints": "..."}]}
    ],
    "relationships": [
      {"from": "table1.column", "to": "table2.column", "type": "1:N"}
    ]
  },
  "technology_stack": [
    {"category": "...", "technology": "...", "version": "...", "rationale": "..."}
  ],
  "security": {
    "auth_flow": "...",
    "trust_boundaries": ["..."],
    "encryption": "at-rest and in-transit via TLS 1.3"
  },
  "architecture_decisions": [
    {"title": "...", "context": "...", "decision": "...", "consequences": "..."}
  ],
  "mermaid_diagram": "graph TD\\n  A[Client] --> B[API Gateway]..."
}
"""


class ArchitectAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="architect-agent", agent_type=AgentType.ARCHITECT)
        self._router = router
        self.logger = get_logger("agent.architect")

    async def generate(self, task: TaskContext) -> Artifact:
        requirements = task.input.get("requirements", task.input.get("prd", ""))
        if isinstance(requirements, dict):
            requirements = json.dumps(requirements)

        messages = [
            {"role": "system", "content": ARCHITECT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Design architecture for: {requirements}",
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.5, max_tokens=4096,
                complexity=TaskComplexity.COMPLEX,
            )
            content = response.content
        else:
            content = self._build_mock_architecture(requirements)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.ARCHITECTURE_DOC,
            name=f"Architecture: {str(requirements)[:50]}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"requirements_summary": str(requirements)[:200]},
        )

    def _build_mock_architecture(self, requirements: str) -> str:  # noqa: ARG002
        return json.dumps({
            "system_overview": (
                "A distributed system designed to meet the specified "
                "requirements with scalability and reliability."
            ),
            "services": [
                {
                    "name": "api-gateway",
                    "responsibility": "Route external requests, auth, rate limiting",
                    "api_endpoints": [
                        {
                            "method": "GET",
                            "path": "/api/v1/health",
                            "description": "Health check",
                        },
                    ],
                    "data_owned": [],
                    "dependencies": ["auth-service"],
                },
                {
                    "name": "auth-service",
                    "responsibility": "User authentication and authorization",
                    "api_endpoints": [
                        {
                            "method": "POST",
                            "path": "/api/v1/auth/login",
                            "description": "User login",
                        },
                        {
                            "method": "POST",
                            "path": "/api/v1/auth/register",
                            "description": "User registration",
                        },
                    ],
                    "data_owned": ["users", "refresh_tokens"],
                    "dependencies": [],
                },
                {
                    "name": "core-service",
                    "responsibility": "Core business logic",
                    "api_endpoints": [
                        {
                            "method": "GET",
                            "path": "/api/v1/items",
                            "description": "List items",
                        },
                        {
                            "method": "POST",
                            "path": "/api/v1/items",
                            "description": "Create item",
                        },
                    ],
                    "data_owned": ["items"],
                    "dependencies": ["auth-service"],
                },
            ],
            "database": {
                "tables": [
                    {
                        "name": "users",
                        "columns": [
                            {"name": "id", "type": "UUID", "constraints": "PK"},
                            {
                                "name": "email",
                                "type": "VARCHAR(255)",
                                "constraints": "UNIQUE NOT NULL",
                            },
                            {
                                "name": "password_hash",
                                "type": "VARCHAR(255)",
                                "constraints": "NOT NULL",
                            },
                        ],
                    },
                    {
                        "name": "items",
                        "columns": [
                            {"name": "id", "type": "UUID", "constraints": "PK"},
                            {
                                "name": "user_id",
                                "type": "UUID",
                                "constraints": "FK -> users.id",
                            },
                            {
                                "name": "title",
                                "type": "VARCHAR(500)",
                                "constraints": "NOT NULL",
                            },
                        ],
                    },
                ],
                "relationships": [
                    {
                        "from": "items.user_id",
                        "to": "users.id",
                        "type": "N:1",
                    },
                ],
            },
            "technology_stack": [
                {
                    "category": "Backend",
                    "technology": "FastAPI",
                    "version": "0.111+",
                    "rationale": "Async Python, OpenAPI auto-generation",
                },
                {
                    "category": "Database",
                    "technology": "PostgreSQL",
                    "version": "15+",
                    "rationale": "ACID, JSONB, mature ecosystem",
                },
                {
                    "category": "Cache",
                    "technology": "Redis",
                    "version": "7+",
                    "rationale": "Session storage, rate limiting, pub/sub",
                },
            ],
            "security": {
                "auth_flow": (
                    "JWT-based: client authenticates via auth-service, "
                    "receives access+refresh tokens. API Gateway validates "
                    "JWT on all requests."
                ),
                "trust_boundaries": [
                    "Internet <-> API Gateway",
                    "API Gateway <-> Internal Services",
                    "Services <-> Database",
                ],
                "encryption": "TLS 1.3 in transit, AES-256 at rest",
            },
            "architecture_decisions": [
                {
                    "title": "Use FastAPI for backend services",
                    "context": "Need async Python framework with OpenAPI",
                    "decision": "FastAPI selected over Django/Flask",
                    "consequences": "Faster dev, auto-docs, async support",
                },
                {
                    "title": "JWT for authentication",
                    "context": "Need stateless auth for microservices",
                    "decision": "JWT access tokens with refresh rotation",
                    "consequences": "Stateless, scalable, requires key management",
                },
            ],
            "mermaid_diagram": (
                "graph TD\n"
                "  Client --> API[API Gateway]\n"
                "  API --> Auth[Auth Service]\n"
                "  API --> Core[Core Service]\n"
                "  Auth --> DB[(PostgreSQL)]\n"
                "  Core --> DB\n"
                "  Auth --> Redis[(Redis)]\n"
            ),
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("services") or len(data.get("services", [])) < 2:
                issues.append("Fewer than 2 services defined")
            if not data.get("database"):
                issues.append("Missing database design")
            if not data.get("technology_stack"):
                issues.append("Missing technology stack")
            if not data.get("security"):
                issues.append("Missing security architecture")
            if not data.get("architecture_decisions"):
                issues.append("Missing architecture decisions")

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Complete architecture"] if not issues else []
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
