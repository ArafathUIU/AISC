"""Research and Architect Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.architect_agent import ArchitectAgent
from agent_runtime.agents.concrete.research_agent import ResearchAgent
from aisc_models import AgentType, Artifact, ArtifactType, TaskContext


def _make_task(task_type: str, agent_type: AgentType, **inputs: object) -> TaskContext:
    return TaskContext(
        task_id=uuid.uuid4(),
        task_type=task_type,
        project_id=uuid.uuid4(),
        agent_type=agent_type,
        input=dict(inputs),
    )


class TestResearchAgent:
    def test_agent_type(self) -> None:
        agent = ResearchAgent()
        assert agent.agent_type == AgentType.RESEARCH

    def test_generates_research_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ResearchAgent()
            task = _make_task(
                "research",
                AgentType.RESEARCH,
                question="Compare React vs Vue for dashboards",
                research_type="technology",
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.RESEARCH_REPORT

            data = json.loads(artifact.content)
            assert "research_question" in data
            assert "findings" in data
            assert len(data["findings"]) >= 2
            assert "recommendations" in data
            assert "sources" in data
            assert "limitations" in data

        asyncio.run(run())

    def test_critique_validates_sections(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ResearchAgent()
            task = _make_task(
                "research", AgentType.RESEARCH,
                question="Test research",
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0
            assert len(critique.issues) == 0

        asyncio.run(run())

    def test_critique_detects_incomplete(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ResearchAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.RESEARCH_REPORT,
                name="bad",
                content='{"research_question": "test"}',
                created_by_agent="research",
            )
            critique = await agent.critique(bad)
            assert critique.overall_score < 100
            assert len(critique.issues) > 0

        asyncio.run(run())


class TestArchitectAgent:
    def test_agent_type(self) -> None:
        agent = ArchitectAgent()
        assert agent.agent_type == AgentType.ARCHITECT

    def test_generates_architecture_doc(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ArchitectAgent()
            task = _make_task(
                "architecture",
                AgentType.ARCHITECT,
                requirements="Build a todo list app with user auth",
                prd='{"title": "Todo App"}',
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.ARCHITECTURE_DOC

            data = json.loads(artifact.content)
            assert "services" in data
            assert len(data["services"]) >= 2
            assert "database" in data
            assert "technology_stack" in data
            assert "security" in data
            assert "architecture_decisions" in data

        asyncio.run(run())

    def test_critique_validates_sections(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ArchitectAgent()
            task = _make_task(
                "architecture", AgentType.ARCHITECT,
                requirements="Test app",
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0

        asyncio.run(run())

    def test_critique_detects_missing_services(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ArchitectAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.ARCHITECTURE_DOC,
                name="bad",
                content='{"services": [], "database": {}}',
                created_by_agent="architect",
            )
            critique = await agent.critique(bad)
            assert critique.overall_score < 100
            assert any("services" in i.lower() for i in critique.issues)

        asyncio.run(run())
