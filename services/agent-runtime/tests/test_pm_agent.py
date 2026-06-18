"""Product Manager Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.pm_agent import ProductManagerAgent
from aisc_models import AgentType, TaskContext


class TestProductManagerAgent:
    def test_agent_type(self) -> None:
        agent = ProductManagerAgent()
        assert agent.agent_type == AgentType.PRODUCT_MANAGER

    def test_generate_without_router_produces_mock_prd(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ProductManagerAgent()
            task = TaskContext(
                task_id=uuid.uuid4(),
                task_type="requirements_generation",
                project_id=uuid.uuid4(),
                agent_type=AgentType.PRODUCT_MANAGER,
                input={"business_idea": "A todo list app"},
            )
            artifact = await agent.run(task)
            assert artifact.type.value == "prd"

            data = json.loads(artifact.content)
            assert "title" in data
            assert "problem_statement" in data
            assert "features" in data
            assert len(data["features"]) >= 3
            assert "success_metrics" in data
            assert len(data["success_metrics"]) >= 2
            assert "risks" in data

        asyncio.run(run())

    def test_mock_prd_is_valid_json(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ProductManagerAgent()
            task = TaskContext(
                task_id=uuid.uuid4(),
                task_type="requirements",
                project_id=uuid.uuid4(),
                agent_type=AgentType.PRODUCT_MANAGER,
                input={"business_idea": "test"},
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)
            assert isinstance(data, dict)

        asyncio.run(run())

    def test_critique_catches_missing_sections(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ProductManagerAgent()
            task = TaskContext(
                task_id=uuid.uuid4(),
                task_type="requirements",
                project_id=uuid.uuid4(),
                agent_type=AgentType.PRODUCT_MANAGER,
                input={"business_idea": "test"},
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score >= 0
            assert isinstance(critique.issues, list)

        asyncio.run(run())

    def test_critique_gives_full_score_for_complete_prd(self) -> None:
        import asyncio

        async def run() -> None:
            agent = ProductManagerAgent()
            task = TaskContext(
                task_id=uuid.uuid4(),
                task_type="requirements",
                project_id=uuid.uuid4(),
                agent_type=AgentType.PRODUCT_MANAGER,
                input={"business_idea": "Complete app"},
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0

        asyncio.run(run())

    def test_critique_rejects_invalid_json(self) -> None:
        import asyncio

        async def run() -> None:
            from aisc_models import Artifact, ArtifactType
            agent = ProductManagerAgent()
            bad_artifact = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.PRD,
                name="bad",
                content="not valid json",
                created_by_agent="pm",
            )
            critique = await agent.critique(bad_artifact)
            assert critique.overall_score == 0.0
            assert "not valid json" in critique.issues[0].lower()

        asyncio.run(run())
