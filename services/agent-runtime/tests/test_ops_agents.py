"""DevOps and Monitoring Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.devops_agent import DevOpsAgent
from agent_runtime.agents.concrete.monitoring_agent import MonitoringAgent
from aisc_models import AgentType, Artifact, ArtifactType, TaskContext


def _make_task(task_type: str, agent_type: AgentType, **inputs: object) -> TaskContext:
    return TaskContext(
        task_id=uuid.uuid4(),
        task_type=task_type,
        project_id=uuid.uuid4(),
        agent_type=agent_type,
        input=dict(inputs),
    )


class TestDevOpsAgent:
    def test_agent_type(self) -> None:
        agent = DevOpsAgent()
        assert agent.agent_type == AgentType.DEVOPS

    def test_generates_dockerfile(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DevOpsAgent()
            task = _make_task(
                "infra_generation", AgentType.DEVOPS,
                app_name="test-app",
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.DEPLOYMENT_CONFIG

            data = json.loads(artifact.content)
            assert "dockerfiles" in data
            assert len(data["dockerfiles"]) >= 1
            assert "kubernetes" in data
            assert "cicd" in data

        asyncio.run(run())

    def test_generates_k8s_manifests(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DevOpsAgent()
            task = _make_task("infra", AgentType.DEVOPS, app_name="svc")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            k8s = data["kubernetes"]
            assert len(k8s["deployments"]) >= 1
            assert len(k8s["services"]) >= 1
            assert "replicas: 3" in k8s["deployments"][0]["content"]

        asyncio.run(run())

    def test_generates_cicd(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DevOpsAgent()
            task = _make_task("infra", AgentType.DEVOPS, app_name="app")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            cicd = data["cicd"]
            assert "content" in cicd
            assert "actions/checkout" in cicd["content"]

        asyncio.run(run())

    def test_critique_catches_missing_sections(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DevOpsAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.DEPLOYMENT_CONFIG,
                name="bad",
                content='{"dockerfiles": [], "kubernetes": {}}',
                created_by_agent="devops",
            )
            critique = await agent.critique(bad)
            assert len(critique.issues) >= 2

        asyncio.run(run())


class TestMonitoringAgent:
    def test_agent_type(self) -> None:
        agent = MonitoringAgent()
        assert agent.agent_type == AgentType.MONITORING

    def test_generates_monitoring_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = MonitoringAgent()
            task = _make_task(
                "monitoring_analysis", AgentType.MONITORING,
                service="user-service",
                metrics='{"p95_latency": 450, "error_rate": 0.02}',
            )
            artifact = await agent.run(task)

            data = json.loads(artifact.content)
            assert "anomalies" in data
            assert len(data["anomalies"]) >= 1
            assert "alerts" in data
            assert len(data["alerts"]) >= 1
            assert "health_summary" in data
            assert data["health_summary"]["services_healthy"] >= 0

        asyncio.run(run())

    def test_generates_alerts(self) -> None:
        import asyncio

        async def run() -> None:
            agent = MonitoringAgent()
            task = _make_task(
                "monitoring", AgentType.MONITORING, service="payment-svc",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            alert = data["alerts"][0]
            assert alert["severity"] == "high"
            assert len(alert["suggested_actions"]) >= 2

        asyncio.run(run())

    def test_critique_catches_empty_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = MonitoringAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.SECURITY_REPORT,
                name="bad",
                content='{"alerts": [], "health_summary": {"services_healthy": 0}}',
                created_by_agent="monitoring",
            )
            critique = await agent.critique(bad)
            assert "Zero services" in str(critique.issues)

        asyncio.run(run())
