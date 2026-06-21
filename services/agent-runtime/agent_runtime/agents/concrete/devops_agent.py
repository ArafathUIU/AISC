"""DevOps Agent — generates Dockerfiles, K8s manifests, CI/CD pipelines."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

DEVOPS_SYSTEM_PROMPT = """\
You are an expert DevOps Engineer. Generate production-ready infrastructure
configurations from application code and architecture documents.

Include:
1. Dockerfiles (multi-stage, optimized)
2. Kubernetes manifests (Deployment, Service, HPA, PDB)
3. CI/CD pipeline (GitHub Actions)
4. Terraform skeleton for cloud infrastructure

Output ONLY valid JSON:
{
  "dockerfiles": [
    {"service": "name", "content": "Dockerfile content..."}
  ],
  "kubernetes": {
    "deployments": [{"name": "...", "content": "yaml..."}],
    "services": [{"name": "...", "content": "yaml..."}]
  },
  "cicd": {
    "content": "GitHub Actions workflow yaml...",
    "triggers": ["push", "pull_request"]
  },
  "summary": "..."
}
"""

_MOCK_DOCKERFILE = """\
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

_MOCK_K8S_DEPLOYMENT = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app-deployment
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: registry/my-app:latest
        ports:
        - containerPort: 8000
        resources:
          requests: {cpu: "250m", memory: "256Mi"}
          limits: {cpu: "500m", memory: "512Mi"}
"""

_MOCK_K8S_SVC = """\
apiVersion: v1
kind: Service
metadata:
  name: app-service
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8000
"""

_MOCK_CICD = """\
name: CI/CD
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install -r requirements.txt
      - run: pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: docker build -t app .
      - run: kubectl apply -f k8s/
"""


class DevOpsAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="devops-agent", agent_type=AgentType.DEVOPS)
        self._router = router
        self.logger = get_logger("agent.devops")

    async def generate(self, task: TaskContext) -> Artifact:
        app_name = task.input.get("app_name", "my-app")
        messages = [
            {"role": "system", "content": DEVOPS_SYSTEM_PROMPT},
            {"role": "user", "content": f"Generate infrastructure for: {app_name}"},
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.3, max_tokens=4096,
                complexity=TaskComplexity.MODERATE,
            )
            content = response.content
        else:
            content = self._build_mock_infra(app_name)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.DEPLOYMENT_CONFIG,
            name=f"Infrastructure for {app_name}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"app_name": app_name},
        )

    def _build_mock_infra(self, _app_name: str) -> str:
        return json.dumps({
            "dockerfiles": [{"service": "app", "content": _MOCK_DOCKERFILE}],
            "kubernetes": {
                "deployments": [
                    {"name": "app-deployment", "content": _MOCK_K8S_DEPLOYMENT},
                ],
                "services": [{"name": "app-service", "content": _MOCK_K8S_SVC}],
            },
            "cicd": {"content": _MOCK_CICD, "triggers": ["push", "pull_request"]},
            "summary": "Generated Dockerfile, K8s manifests, and CI/CD pipeline",
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("dockerfiles"):
                issues.append("No Dockerfiles generated")
            if not data.get("kubernetes"):
                issues.append("No Kubernetes manifests generated")
            if not data.get("cicd"):
                issues.append("No CI/CD pipeline generated")

            k8s = data.get("kubernetes", {})
            if not k8s.get("deployments"):
                issues.append("No K8s deployments defined")
            if not k8s.get("services"):
                issues.append("No K8s services defined")

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Complete infrastructure config"] if not issues else []
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
