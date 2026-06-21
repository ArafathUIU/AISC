"""Self-Healing Agent — autonomous incident detection, RCA, patching, recovery."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

SELF_HEALING_SYSTEM_PROMPT = """\
You are an expert SRE and Debugging Engineer. Perform incident analysis,
root cause analysis, and generate validated patches for production issues.

Follow this process:
1. Gather evidence (logs, metrics, traces)
2. Form hypothesis about root cause
3. Validate hypothesis against evidence
4. Generate minimal, focused patch
5. Create regression test that reproduces the bug
6. Assess patch risk and confidence
7. Output structured incident report with RCA and patch

Output ONLY valid JSON:
{
  "incident_id": "...",
  "rca": {
    "root_cause": "specific technical root cause",
    "confidence": 0.0-1.0,
    "evidence": ["evidence point 1", "evidence point 2"],
    "affected_code": "file:line",
    "is_known_pattern": true/false,
    "similar_incidents": ["uuid"]
  },
  "patch": {
    "description": "one-line summary",
    "code_diff": "unified diff of changes",
    "affected_files": ["file1.py", "file2.py"],
    "risk_assessment": "low|medium|high",
    "risk_rationale": "explanation"
  },
  "regression_test": {
    "content": "test code that reproduces and verifies fix",
    "expected_pass": true
  },
  "auto_deploy_decision": {
    "should_auto_deploy": true/false,
    "confidence_threshold_met": true/false,
    "recommendation": "auto_deploy|human_review|escalate"
  },
  "rollback_plan": "steps to rollback if patch causes issues"
}
"""

_MOCK_RCA = {
    "root_cause": (
        "Connection pool exhaustion in /api/users endpoint due to "
        "missing connection.close() in finally block of create_user function"
    ),
    "confidence": 0.87,
    "evidence": [
        "Error logs: 'QueuePool limit of size 10 overflow 20 reached'",
        "Trace shows create_user opens connection but never closes",
        "Connection pool metrics show gradual leak over 4 hours",
    ],
    "affected_code": "src/routes/users.py:15-22",
    "is_known_pattern": True,
    "similar_incidents": ["inc-001", "inc-007", "inc-012"],
}

_MOCK_PATCH = {
    "description": "Add connection.close() in finally block of create_user",
    "code_diff": (
        "@@ -15,8 +15,14 @@ async def create_user(body: UserCreate):\n"
        "     conn = await get_db_connection()\n"
        "+    try:\n"
        "         user = await conn.execute(\n"
        "             insert(User).values(email=body.email, ...)\n"
        "         )\n"
        "+        return user\n"
        "+    finally:\n"
        "+        await conn.close()\n"
        "-    return user"
    ),
    "affected_files": ["src/routes/users.py"],
    "risk_assessment": "low",
    "risk_rationale": "Minimal change, well-established pattern, test covers the fix",
}

_MOCK_REGRESSION_TEST = (
    "import asyncio\n"
    "from src.routes.users import create_user\n\n"
    "async def test_connection_returned_to_pool():\n"
    "    pool = await create_test_pool(size=1)\n"
    "    for _ in range(50):\n"
    '        await create_user(UserCreate(email="x@y.com", ...), pool)\n'
    "    stats = pool.get_stats()\n"
    "    assert stats.overflow == 0, 'Pool overflow detected - connection leak'\n"
)


class SelfHealingAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(
            name="self-healing-agent", agent_type=AgentType.SELF_HEALING,
        )
        self._router = router
        self.logger = get_logger("agent.self_healing")

    async def generate(self, task: TaskContext) -> Artifact:
        incident_desc = task.input.get("incident_description", "")
        service_name = task.input.get("service", "unknown")
        severity = task.input.get("severity", "high")

        messages = [
            {"role": "system", "content": SELF_HEALING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Incident: {incident_desc}\n"
                    f"Service: {service_name}\n"
                    f"Severity: {severity}"
                ),
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.3, max_tokens=4096,
                complexity=TaskComplexity.COMPLEX,
            )
            content = response.content
        else:
            content = self._build_mock_healing(service_name, severity)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.SECURITY_REPORT,
            name=f"Self-Healing Report: {service_name}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"service": service_name, "severity": severity},
        )

    def _build_mock_healing(self, service_name: str, severity: str) -> str:
        rca_conf = 0.95 if severity == "critical" else 0.87
        rca = {**_MOCK_RCA, "confidence": rca_conf}
        should_auto = severity != "critical" and rca_conf >= 0.85
        return json.dumps({
            "incident_id": str(uuid4()),
            "service": service_name,
            "severity": severity,
            "rca": rca,
            "patch": _MOCK_PATCH,
            "regression_test": {
                "content": _MOCK_REGRESSION_TEST,
                "expected_pass": True,
            },
            "auto_deploy_decision": {
                "should_auto_deploy": should_auto,
                "confidence_threshold_met": rca_conf >= 0.70,
                "recommendation": (
                    "auto_deploy" if should_auto
                    else "human_review" if rca_conf >= 0.50
                    else "escalate"
                ),
            },
            "rollback_plan": (
                "git revert the patch commit. Verify connection pool "
                "returns to normal. Monitor for 5 minutes."
            ),
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("rca"):
                issues.append("Missing root cause analysis")
            if not data.get("patch"):
                issues.append("Missing patch")
            if not data.get("regression_test"):
                issues.append("Missing regression test")
            if not data.get("auto_deploy_decision"):
                issues.append("Missing auto-deploy decision")
            if not data.get("rollback_plan"):
                issues.append("Missing rollback plan")

            rca = data.get("rca", {})
            conf = rca.get("confidence", 0)
            if conf < 0.50:
                issues.append(f"RCA confidence too low: {conf:.0%}")
            if not rca.get("evidence"):
                issues.append("No evidence provided for RCA")

            patch = data.get("patch", {})
            if not patch.get("code_diff"):
                issues.append("No code diff in patch")
            risk = patch.get("risk_assessment", "")
            if risk == "high":
                issues.append("High-risk patch requires human review")

            score = 100.0 - (len(issues) * 12)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Complete incident analysis with patch"]
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
