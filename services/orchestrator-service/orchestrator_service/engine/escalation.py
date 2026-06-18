"""Escalation Handler — routes issues to human review with full context."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class EscalationType(StrEnum):
    MAX_ITERATIONS = "max_iterations_exceeded"
    SCORE_DEGRADING = "score_degrading"
    SCORE_STUCK = "score_stuck"
    EARLY_ESCALATION = "early_escalation"
    SECURITY_CRITICAL = "security_critical"
    DEPLOYMENT_ROLLBACK = "deployment_rollback"
    COST_OVERRUN = "cost_overrun"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    CONSENSUS_DEADLOCK = "consensus_deadlock"
    AGENT_ERROR = "agent_error"


class EscalationSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Escalation:
    id: UUID = field(default_factory=uuid4)
    escalation_type: EscalationType = EscalationType.AGENT_ERROR
    severity: EscalationSeverity = EscalationSeverity.MEDIUM
    source_agent: str = ""
    target_role: str = "human_developer"
    title: str = ""
    context: dict[str, Any] = field(default_factory=dict)
    artifact_id: UUID | None = None
    task_id: UUID | None = None
    project_id: UUID | None = None
    status: str = "open"
    suggested_actions: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    timeout_at: datetime = field(
        default_factory=lambda: datetime.now(UTC) + timedelta(hours=4)
    )


class EscalationHandler:
    def __init__(self) -> None:
        self._escalations: dict[UUID, Escalation] = {}

    def create(self, escalation: Escalation) -> Escalation:
        self._escalations[escalation.id] = escalation
        return escalation

    def get(self, escalation_id: UUID) -> Escalation | None:
        return self._escalations.get(escalation_id)

    def resolve(
        self, escalation_id: UUID, resolution: str, resolved_by: str = "human",
    ) -> Escalation | None:
        esc = self._escalations.get(escalation_id)
        if esc:
            esc.status = "resolved"
            esc.context["resolution"] = resolution
            esc.context["resolved_by"] = resolved_by
        return esc

    def list_open(self) -> list[Escalation]:
        return [e for e in self._escalations.values() if e.status == "open"]

    def get_expired(self) -> list[Escalation]:
        now = datetime.now(UTC)
        return [e for e in self._escalations.values()
                if e.status == "open" and e.timeout_at < now]

    def create_quality_gate_escalation(
        self,
        gate_type: str,
        artifact_id: UUID,
        task_id: UUID,
        final_score: float,
        iterations: int,
        score_history: list[float],
    ) -> Escalation:
        return self.create(Escalation(
            escalation_type=EscalationType.MAX_ITERATIONS,
            severity=EscalationSeverity.HIGH,
            target_role=self._role_for_gate(gate_type),
            title=f"Quality gate '{gate_type}' not passed after {iterations} iterations",
            context={
                "gate_type": gate_type,
                "final_score": final_score,
                "iterations": iterations,
                "score_history": score_history,
            },
            artifact_id=artifact_id,
            task_id=task_id,
            suggested_actions=[
                f"Review the {gate_type} artifact",
                "Provide corrected version or lower threshold",
            ],
        ))

    def _role_for_gate(self, gate_type: str) -> str:
        roles = {
            "requirements": "human_product_manager",
            "architecture": "human_architect",
            "code": "human_developer",
            "testing": "human_qa",
            "security": "human_security_engineer",
            "deployment": "human_devops",
        }
        return roles.get(gate_type, "human_developer")

    def create_deadlock_escalation(
        self, task_a_id: UUID, task_b_id: UUID, project_id: UUID,
    ) -> Escalation:
        return self.create(Escalation(
            escalation_type=EscalationType.CIRCULAR_DEPENDENCY,
            severity=EscalationSeverity.HIGH,
            target_role="human_architect",
            title="Circular dependency detected in workflow",
            context={"task_a": str(task_a_id), "task_b": str(task_b_id)},
            project_id=project_id,
            suggested_actions=[
                "Break the circular dependency by reordering tasks",
                "Merge the dependent tasks into one",
            ],
            timeout_at=datetime.now(UTC) + timedelta(hours=2),
        ))
