"""Self-Healing Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.self_healing_agent import SelfHealingAgent
from aisc_models import AgentType, TaskContext


def _make_task(**inputs: object) -> TaskContext:
    return TaskContext(
        task_id=uuid.uuid4(),
        task_type="incident_response",
        project_id=uuid.uuid4(),
        agent_type=AgentType.SELF_HEALING,
        input=dict(inputs),
    )


class TestSelfHealingAgent:
    def test_agent_type(self) -> None:
        agent = SelfHealingAgent()
        assert agent.agent_type == AgentType.SELF_HEALING

    def test_generates_incident_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="500 errors on /api/users",
                service="user-service",
                severity="high",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            assert "rca" in data
            assert data["rca"]["confidence"] > 0.5
            assert len(data["rca"]["evidence"]) >= 2
            assert "patch" in data
            assert "code_diff" in data["patch"]
            assert "regression_test" in data
            assert "auto_deploy_decision" in data
            assert "rollback_plan" in data

        asyncio.run(run())

    def test_rca_has_evidence(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="DB pool exhaustion",
                service="payment-service",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            rca = data["rca"]
            assert len(rca["evidence"]) == 3
            assert "QueuePool" in rca["evidence"][0]

        asyncio.run(run())

    def test_patch_has_rollback_plan(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="Latency spike",
                service="api-gateway",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            assert "rollback_plan" in data
            assert "git revert" in data["rollback_plan"].lower()

        asyncio.run(run())

    def test_critical_severity_requires_human_review(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="Data corruption detected",
                service="db-service",
                severity="critical",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            decision = data["auto_deploy_decision"]
            assert decision["should_auto_deploy"] is False

        asyncio.run(run())

    def test_non_critical_can_auto_deploy(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="Minor memory leak",
                service="worker-service",
                severity="low",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            decision = data["auto_deploy_decision"]
            assert decision["recommendation"] == "auto_deploy"

        asyncio.run(run())

    def test_critique_validates_full_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="Test incident",
                service="test-svc",
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0
            assert len(critique.issues) == 0

        asyncio.run(run())

    def test_regression_test_reproduces_bug(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SelfHealingAgent()
            task = _make_task(
                incident_description="Connection leak",
                service="db-svc",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            reg_test = data["regression_test"]
            assert "pool" in reg_test["content"].lower()
            assert "overflow" in reg_test["content"]

        asyncio.run(run())
