"""Security Agent — vulnerability scanning, secret detection, dependency audit."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

SECURITY_SYSTEM_PROMPT = """\
You are an expert Security Engineer. Audit code for vulnerabilities
and generate a detailed security report.

Check for:
- SQL injection vectors
- XSS vulnerabilities
- Missing input validation
- Broken authentication/authorization
- Hardcoded secrets
- Insecure dependency versions
- Missing rate limiting
- Improper error handling (info leakage)

Output ONLY valid JSON:
{
  "findings": [
    {
      "severity": "critical|high|medium|low",
      "category": "injection|auth|xss|secret|dependency|other",
      "location": "file:line",
      "description": "...",
      "recommendation": "...",
      "cve_id": null
    }
  ],
  "secret_scan": {
    "secrets_found": 0,
    "details": []
  },
  "dependency_audit": {
    "critical_cves": 0,
    "high_cves": 0,
    "outdated_packages": []
  },
  "overall_risk": "critical|high|medium|low",
  "summary": "..."
}
"""

_MOCK_FINDINGS = [
    {
        "severity": "medium",
        "category": "injection",
        "location": "src/routes/users.py:15",
        "description": "User input not validated before database query",
        "recommendation": "Use Pydantic models for input validation",
        "cve_id": None,
    },
    {
        "severity": "low",
        "category": "other",
        "location": "src/services/user_service.py:12",
        "description": "Generic exception handling may leak internal info",
        "recommendation": "Use specific exception types",
        "cve_id": None,
    },
]


class SecurityAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(
            name="security-agent", agent_type=AgentType.SECURITY,
        )
        self._router = router
        self.logger = get_logger("agent.security")

    async def generate(self, task: TaskContext) -> Artifact:
        code = task.input.get("code", task.input.get("source_code", ""))

        messages = [
            {"role": "system", "content": SECURITY_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Audit this code for security issues:\n{code}",
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.2, max_tokens=4096,
                complexity=TaskComplexity.MODERATE,
            )
            content = response.content
        else:
            content = self._build_mock_report()

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.SECURITY_REPORT,
            name="Security Audit Report",
            content=content,
            created_by_agent=self.agent_type.value,
        )

    def _build_mock_report(self) -> str:
        return json.dumps({
            "findings": _MOCK_FINDINGS,
            "secret_scan": {
                "secrets_found": 0,
                "details": [],
            },
            "dependency_audit": {
                "critical_cves": 0,
                "high_cves": 1,
                "outdated_packages": ["requests<2.32"],
            },
            "overall_risk": "medium",
            "summary": (
                "2 findings: 1 medium, 1 low. No critical vulnerabilities."
            ),
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("findings"):
                issues.append("No security findings (likely incomplete scan)")
            if not data.get("secret_scan"):
                issues.append("Missing secret scan section")
            if not data.get("dependency_audit"):
                issues.append("Missing dependency audit")
            if not data.get("overall_risk"):
                issues.append("Missing overall risk rating")

            findings = data.get("findings", [])
            critical_count = sum(
                1 for f in findings if f.get("severity") == "critical"
            )
            if critical_count > 0:
                issues.append(
                    f"{critical_count} critical findings - must fix before deploy"
                )

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Complete security scan"] if not issues else []
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
