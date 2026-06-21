"""Learning and Knowledge Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.learning_agent import (
    KnowledgeAgent,
    LearningAgent,
)
from aisc_models import AgentType, Artifact, ArtifactType, TaskContext


def _make_task(**inputs: object) -> TaskContext:
    return TaskContext(
        task_id=uuid.uuid4(),
        task_type="learning_analysis",
        project_id=uuid.uuid4(),
        agent_type=AgentType.LEARNING,
        input=dict(inputs),
    )


class TestLearningAgent:
    def test_agent_type(self) -> None:
        agent = LearningAgent()
        assert agent.agent_type == AgentType.LEARNING

    def test_extracts_patterns(self) -> None:
        import asyncio

        async def run() -> None:
            agent = LearningAgent()
            task = _make_task(
                learning_records=[
                    {"score": 95, "passed": True, "iterations": 1},
                    {"score": 88, "passed": False, "iterations": 3},
                ],
                agent_type="product_manager",
            )
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            assert "patterns" in data
            assert len(data["patterns"]) >= 2
            assert data["patterns"][0]["type"] == "success_pattern"

        asyncio.run(run())

    def test_generates_statistics(self) -> None:
        import asyncio

        async def run() -> None:
            agent = LearningAgent()
            task = _make_task(learning_records=[{}] * 100, agent_type="developer")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            stats = data["statistics"]
            assert stats["pass_rate"] > 0
            assert stats["avg_iterations_to_pass"] > 0

        asyncio.run(run())

    def test_suggests_prompt_optimizations(self) -> None:
        import asyncio

        async def run() -> None:
            agent = LearningAgent()
            task = _make_task(learning_records=[{}] * 10, agent_type="architect")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            optimizations = data["prompt_optimizations"]
            assert len(optimizations) >= 1
            assert "expected_impact" in optimizations[0]

        asyncio.run(run())

    def test_validates_existing_patterns(self) -> None:
        import asyncio

        async def run() -> None:
            agent = LearningAgent()
            task = _make_task(learning_records=[{}] * 50, agent_type="qa")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            validations = data["validations"]
            assert len(validations) >= 1
            assert validations[0]["trend"] == "strengthening"

        asyncio.run(run())

    def test_critique_checks_completeness(self) -> None:
        import asyncio

        async def run() -> None:
            agent = LearningAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.RESEARCH_REPORT, name="bad",
                content='{"patterns": [], "statistics": {}}',
                created_by_agent="learning",
            )
            critique = await agent.critique(bad)
            assert "No prompt optimizations" in str(critique.issues)

        asyncio.run(run())


class TestKnowledgeAgent:
    def test_agent_type(self) -> None:
        agent = KnowledgeAgent()
        assert agent.agent_type == AgentType.KNOWLEDGE

    def test_queries_knowledge_base(self) -> None:
        import asyncio

        async def run() -> None:
            agent = KnowledgeAgent()
            agent.store("project", {"id": "p1", "name": "Test Project"})
            agent.store("project", {"id": "p2", "name": "Another Project"})

            task = _make_task(query="Test Project", entity_type="project")
            artifact = await agent.run(task)
            data = json.loads(artifact.content)

            assert data["total_found"] >= 1
            assert "Test Project" in json.dumps(data["results"])

        asyncio.run(run())

    def test_critique_validates_output(self) -> None:
        import asyncio

        async def run() -> None:
            agent = KnowledgeAgent()
            task = _make_task(query="test")
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0

        asyncio.run(run())
