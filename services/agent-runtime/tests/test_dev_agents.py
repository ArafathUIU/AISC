"""Developer, QA, and Security Agent tests."""

import json
import uuid

from agent_runtime.agents.concrete.developer_agent import DeveloperAgent
from agent_runtime.agents.concrete.qa_agent import QAAgent
from agent_runtime.agents.concrete.security_agent import SecurityAgent
from aisc_models import AgentType, Artifact, ArtifactType, TaskContext


def _make_task(task_type: str, agent_type: AgentType, **inputs: object) -> TaskContext:
    return TaskContext(
        task_id=uuid.uuid4(),
        task_type=task_type,
        project_id=uuid.uuid4(),
        agent_type=agent_type,
        input=dict(inputs),
    )


class TestDeveloperAgent:
    def test_agent_type(self) -> None:
        agent = DeveloperAgent()
        assert agent.agent_type == AgentType.DEVELOPER

    def test_generates_code(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DeveloperAgent()
            task = _make_task(
                "code_generation", AgentType.DEVELOPER,
                api_spec="Create a user CRUD API",
                language="python", framework="fastapi",
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.SOURCE_CODE

            data = json.loads(artifact.content)
            assert "files" in data
            assert len(data["files"]) == 3
            assert data["files"][0]["language"] == "python"
            assert "dependencies" in data
            assert len(data["dependencies"]) == 3

        asyncio.run(run())

    def test_critique_validates_code(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DeveloperAgent()
            task = _make_task(
                "code_generation", AgentType.DEVELOPER,
                api_spec="test",
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0
            assert len(critique.issues) == 0

        asyncio.run(run())

    def test_critique_detects_empty_files(self) -> None:
        import asyncio

        async def run() -> None:
            agent = DeveloperAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.SOURCE_CODE,
                name="bad",
                content='{"files": [{"path": "x.py", "content": ""}], "dependencies": []}',
                created_by_agent="developer",
            )
            critique = await agent.critique(bad)
            assert "Empty file" in str(critique.issues)
            assert "No dependencies" in str(critique.issues)

        asyncio.run(run())


class TestQAAgent:
    def test_agent_type(self) -> None:
        agent = QAAgent()
        assert agent.agent_type == AgentType.QA

    def test_generates_tests(self) -> None:
        import asyncio

        async def run() -> None:
            agent = QAAgent()
            task = _make_task(
                "test_generation", AgentType.QA,
                source_code="def add(a, b): return a + b",
                requirements="Must handle integers",
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.TEST_FILE

            data = json.loads(artifact.content)
            assert "test_files" in data
            assert len(data["test_files"]) == 2
            assert data["test_count"] >= 3

        asyncio.run(run())

    def test_tests_contain_assertions(self) -> None:
        import asyncio

        async def run() -> None:
            agent = QAAgent()
            task = _make_task("test_generation", AgentType.QA, source_code="x")
            artifact = await agent.run(task)

            data = json.loads(artifact.content)
            for tf in data["test_files"]:
                assert "assert" in tf["content"]

        asyncio.run(run())

    def test_critique_validates_coverage(self) -> None:
        import asyncio

        async def run() -> None:
            agent = QAAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.TEST_FILE, name="bad",
                content='{"test_files": [], "test_count": 1}',
                created_by_agent="qa",
            )
            critique = await agent.critique(bad)
            assert "No test files" in str(critique.issues)
            assert "Fewer than 3" in str(critique.issues)

        asyncio.run(run())


class TestSecurityAgent:
    def test_agent_type(self) -> None:
        agent = SecurityAgent()
        assert agent.agent_type == AgentType.SECURITY

    def test_generates_security_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SecurityAgent()
            task = _make_task(
                "security_audit", AgentType.SECURITY,
                code="SELECT * FROM users WHERE id = '" + "user_input'",
            )
            artifact = await agent.run(task)
            assert artifact.type == ArtifactType.SECURITY_REPORT

            data = json.loads(artifact.content)
            assert "findings" in data
            assert len(data["findings"]) >= 2
            assert "secret_scan" in data
            assert "dependency_audit" in data
            assert data["overall_risk"] == "medium"

        asyncio.run(run())

    def test_critique_validates_report(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SecurityAgent()
            task = _make_task(
                "security_audit", AgentType.SECURITY, code="test",
            )
            artifact = await agent.run(task)
            critique = await agent.critique(artifact)
            assert critique.overall_score == 100.0
            assert len(critique.issues) == 0

        asyncio.run(run())

    def test_critique_flags_missing_sections(self) -> None:
        import asyncio

        async def run() -> None:
            agent = SecurityAgent()
            bad = Artifact(
                project_id=uuid.uuid4(),
                type=ArtifactType.SECURITY_REPORT,
                name="bad",
                content='{"findings": []}',
                created_by_agent="security",
            )
            critique = await agent.critique(bad)
            assert "Missing secret scan" in str(critique.issues)
            assert "Missing dependency audit" in str(critique.issues)

        asyncio.run(run())
