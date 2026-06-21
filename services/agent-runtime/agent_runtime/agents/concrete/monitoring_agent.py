"""Monitoring Agent — anomaly detection, alert generation, log analysis."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

MONITORING_SYSTEM_PROMPT = """\
You are an expert SRE/Monitoring Engineer. Analyze system metrics, logs,
and traces to detect anomalies, generate alerts, and provide insights.

Output ONLY valid JSON:
{
  "anomalies": [
    {
      "service": "service-name",
      "metric": "latency|error_rate|cpu|memory",
      "current_value": 0.0,
      "baseline": 0.0,
      "deviation_sigma": 0.0,
      "severity": "critical|high|medium|low",
      "started_at": "ISO8601"
    }
  ],
  "alerts": [
    {
      "severity": "critical|high|medium|low",
      "title": "...",
      "description": "...",
      "suggested_actions": ["..."]
    }
  ],
  "health_summary": {
    "services_healthy": 0,
    "services_degraded": 0,
    "services_down": 0
  },
  "recommendations": ["..."],
  "summary": "..."
}
"""


class MonitoringAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(
            name="monitoring-agent", agent_type=AgentType.MONITORING,
        )
        self._router = router
        self.logger = get_logger("agent.monitoring")

    async def generate(self, task: TaskContext) -> Artifact:
        service_name = task.input.get("service", "unknown")
        metrics_data = task.input.get("metrics", "{}")

        messages = [
            {"role": "system", "content": MONITORING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze metrics for {service_name}:\n{metrics_data}"
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
            content = self._build_mock_analysis(service_name)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.SECURITY_REPORT,
            name=f"Monitoring Report: {service_name}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"service": service_name},
        )

    def _build_mock_analysis(self, service_name: str) -> str:
        return json.dumps({
            "anomalies": [
                {
                    "service": service_name,
                    "metric": "latency",
                    "current_value": 450.0,
                    "baseline": 120.0,
                    "deviation_sigma": 3.8,
                    "severity": "high",
                    "started_at": "2026-06-18T10:00:00Z",
                },
            ],
            "alerts": [
                {
                    "severity": "high",
                    "title": f"P95 latency spike in {service_name}",
                    "description": "Latency 3.8x above baseline for 5 minutes",
                    "suggested_actions": [
                        "Check database connection pool",
                        "Review recent deployments",
                        "Analyze query performance",
                    ],
                },
            ],
            "health_summary": {
                "services_healthy": 11,
                "services_degraded": 1,
                "services_down": 0,
            },
            "recommendations": [
                "Increase connection pool size",
                "Add caching for hot queries",
                "Set up auto-scaling for the service",
            ],
            "summary": "1 anomaly detected, 1 alert generated, 11/12 services healthy",
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("health_summary"):
                issues.append("Missing health summary")
            if not data.get("alerts"):
                issues.append("No alerts generated (empty report)")

            health = data.get("health_summary", {})
            total = (
                health.get("services_healthy", 0)
                + health.get("services_degraded", 0)
                + health.get("services_down", 0)
            )
            if total == 0:
                issues.append("Zero services in health summary")

            score = 100.0 - (len(issues) * 20)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Complete monitoring report"] if not issues else []
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
