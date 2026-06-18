import asyncio
import uuid
from datetime import UTC, datetime

import pytest
from aisc_models import EventEnvelope, AgentType, ArtifactType, GateType


class TestEventEnvelope:
    def test_default_values(self) -> None:
        event = EventEnvelope(
            event_type="ProjectCreated",
            source_service="orchestrator-service",
            payload={"project_name": "test"},
        )
        assert event.event_id is not None
        assert event.timestamp is not None
        assert event.correlation_id is not None
        assert event.version == "1.0"

    def test_full_envelope(self) -> None:
        project_id = uuid.uuid4()
        task_id = uuid.uuid4()
        event = EventEnvelope(
            event_type="TaskCompleted",
            source_service="agent-runtime",
            source_agent="developer-001",
            project_id=project_id,
            task_id=task_id,
            payload={"artifact_ids": [str(uuid.uuid4())]},
        )
        assert event.project_id == project_id
        assert event.task_id == task_id
        assert event.source_agent == "developer-001"

    def test_serialization(self) -> None:
        event = EventEnvelope(
            event_type="ArtifactScored",
            source_service="scoring-engine",
            payload={"aggregate_score": 93.5, "passed": True},
        )
        data = event.model_dump(mode="json")
        assert data["event_type"] == "ArtifactScored"
        assert data["payload"]["aggregate_score"] == 93.5
        assert data["payload"]["passed"] is True

    def test_deserialization(self) -> None:
        data = {
            "event_id": str(uuid.uuid4()),
            "event_type": "ArtifactApproved",
            "timestamp": datetime.now(UTC).isoformat(),
            "source_service": "quality-gate-service",
            "correlation_id": str(uuid.uuid4()),
            "payload": {"artifact_id": str(uuid.uuid4()), "score": 94},
            "version": "1.0",
        }
        event = EventEnvelope.model_validate(data)
        assert event.event_type == "ArtifactApproved"
        assert event.source_service == "quality-gate-service"


class TestAgentTypeEnum:
    def test_all_agent_types(self) -> None:
        assert len(AgentType) == 15
        assert AgentType.ORCHESTRATOR == "orchestrator"
        assert AgentType.DEVELOPER == "developer"
        assert AgentType.SELF_HEALING == "self_healing"

    def test_agent_type_values(self) -> None:
        expected = {
            "orchestrator", "product_manager", "research", "architect",
            "developer", "qa", "security", "devops", "monitoring",
            "self_healing", "knowledge", "learning", "consensus",
            "improvement", "reviewer",
        }
        actual = {t.value for t in AgentType}
        assert actual == expected


class TestArtifactTypeEnum:
    def test_all_artifact_types(self) -> None:
        assert len(ArtifactType) == 12

    def test_key_artifact_types(self) -> None:
        assert ArtifactType.PRD == "prd"
        assert ArtifactType.SOURCE_CODE == "source_code"
        assert ArtifactType.TEST_FILE == "test_file"
        assert ArtifactType.SECURITY_REPORT == "security_report"


class TestGateTypeEnum:
    def test_all_gate_types(self) -> None:
        assert len(GateType) == 6
        assert GateType.REQUIREMENTS == "requirements"
        assert GateType.ARCHITECTURE == "architecture"
        assert GateType.CODE == "code"
        assert GateType.TESTING == "testing"
        assert GateType.SECURITY == "security"
        assert GateType.DEPLOYMENT == "deployment"


class TestModelConstraints:
    def test_artifact_score_range(self) -> None:
        from aisc_models import MetricScore
        valid = MetricScore(
            metric_name="completeness",
            score=85.5,
            weight=0.25,
            justification="Good coverage",
            passed=True,
        )
        assert valid.score == 85.5
        assert valid.passed is True

    def test_evaluation_result(self) -> None:
        from aisc_models import MetricScore, EvaluationResult
        result = EvaluationResult(
            artifact_id=uuid.uuid4(),
            gate_type=GateType.CODE,
            aggregate_score=93.5,
            metric_scores=[
                MetricScore(metric_name="complexity", score=95, weight=0.2, justification="Clean", passed=True),
                MetricScore(metric_name="security", score=92, weight=0.2, justification="No issues", passed=True),
            ],
            passed=True,
            iteration=3,
        )
        assert result.passed is True
        assert result.iteration == 3
        assert len(result.metric_scores) == 2

    def test_critique_structure(self) -> None:
        from aisc_models import Critique
        critique = Critique(
            artifact_id=uuid.uuid4(),
            reviewer_id=uuid.uuid4(),
            overall_score=84,
            metric_scores={"scalability": 78, "security": 90},
            issues=["No horizontal scaling defined"],
            strengths=["Good service decomposition"],
            improvements=["Add auto-scaling rules"],
        )
        assert len(critique.issues) == 1
        assert len(critique.strengths) == 1
        assert len(critique.improvements) == 1

    def test_loop_state(self) -> None:
        from aisc_models import LoopState
        state = LoopState(
            artifact_id=uuid.uuid4(),
            gate_type=GateType.REQUIREMENTS,
            threshold=90.0,
            score_history=[72.0, 84.0],
        )
        assert state.current_iteration == 1
        assert state.max_iterations == 5
        assert len(state.score_history) == 2
