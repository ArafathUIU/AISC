"""AISC Debate Service — multi-agent consensus and improvement."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class DebateStatus(StrEnum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    CONSENSUS = "consensus"
    RESOLVED = "resolved"
    DEADLOCKED = "deadlocked"


class ConsensusDecision(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    CONFLICT = "conflict"
    ESCALATE = "escalate"


@dataclass
class ReviewerResult:
    reviewer_id: UUID = field(default_factory=uuid4)
    reviewer_name: str = ""
    overall_score: float = 0.0
    metric_scores: dict[str, float] = field(default_factory=dict)
    issues: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)
    improvements: list[str] = field(default_factory=list)


@dataclass
class DebateRound:
    round_number: int = 1
    reviewer_results: list[ReviewerResult] = field(default_factory=list)
    consensus_decision: ConsensusDecision = ConsensusDecision.CONFLICT
    agreement_score: float = 0.0
    resolution_note: str = ""


@dataclass
class Debate:
    id: UUID = field(default_factory=uuid4)
    artifact_id: UUID = field(default_factory=uuid4)
    status: DebateStatus = DebateStatus.OPEN
    threshold: float = 90.0
    max_rounds: int = 3
    rounds: list[DebateRound] = field(default_factory=list)
    final_decision: ConsensusDecision | None = None
    improved_content: str | None = None

    def current_round(self) -> DebateRound | None:
        if not self.rounds:
            return None
        return self.rounds[-1]

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "artifact_id": str(self.artifact_id),
            "status": self.status.value,
            "threshold": self.threshold,
            "current_round": len(self.rounds),
            "max_rounds": self.max_rounds,
            "final_decision": (
                self.final_decision.value if self.final_decision else None
            ),
        }


class DebateEngine:
    def __init__(self) -> None:
        self._debates: dict[UUID, Debate] = {}

    def create(self, artifact_id: UUID, threshold: float = 90.0) -> Debate:
        debate = Debate(artifact_id=artifact_id, threshold=threshold)
        self._debates[debate.id] = debate
        return debate

    def get(self, debate_id: UUID) -> Debate | None:
        return self._debates.get(debate_id)

    def submit_reviews(
        self, debate_id: UUID, reviews: list[ReviewerResult],
    ) -> DebateRound:
        debate = self._debates[debate_id]
        debate.status = DebateStatus.CONSENSUS

        round_num = len(debate.rounds) + 1
        debate_round = DebateRound(round_number=round_num, reviewer_results=reviews)

        if len(reviews) < 2:
            debate_round.consensus_decision = ConsensusDecision.ESCALATE
            debate.rounds.append(debate_round)
            return debate_round

        scores = [r.overall_score for r in reviews]
        avg_score = sum(scores) / len(scores)
        passed_count = sum(1 for s in scores if s >= debate.threshold)

        if passed_count >= len(reviews):
            debate_round.consensus_decision = ConsensusDecision.PASS
        elif passed_count == 0:
            debate_round.consensus_decision = ConsensusDecision.FAIL
        elif passed_count > len(reviews) / 2:
            debate_round.consensus_decision = ConsensusDecision.PASS
            debate_round.resolution_note = (
                f"Majority passes ({passed_count}/{len(reviews)}) at avg {avg_score:.1f}"
            )
        else:
            debate_round.consensus_decision = ConsensusDecision.CONFLICT

        debate_round.agreement_score = self._compute_agreement(reviews)

        if (
            round_num >= debate.max_rounds
            and debate_round.consensus_decision == ConsensusDecision.CONFLICT
        ):
            debate_round.consensus_decision = ConsensusDecision.ESCALATE
            debate_round.resolution_note = "Max rounds reached without consensus"

        debate.rounds.append(debate_round)
        return debate_round

    def resolve(self, debate_id: UUID, decision: ConsensusDecision) -> None:
        debate = self._debates[debate_id]
        debate.final_decision = decision
        debate.status = (
            DebateStatus.RESOLVED if decision != ConsensusDecision.ESCALATE
            else DebateStatus.DEADLOCKED
        )

    def _compute_agreement(self, reviews: list[ReviewerResult]) -> float:
        if len(reviews) < 2:
            return 0.0

        scores = [r.overall_score for r in reviews]
        max_diff = max(scores) - min(scores)
        if max_diff == 0:
            return 1.0

        agreement = 1.0 - (max_diff / 100.0)

        all_issues: set[str] = set()
        common_issues: set[str] | None = None
        for r in reviews:
            if common_issues is None:
                common_issues = {i.lower() for i in r.issues}
            else:
                common_issues &= {i.lower() for i in r.issues}
            all_issues |= {i.lower() for i in r.issues}

        if all_issues:
            issue_overlap = len(common_issues or set()) / len(all_issues)
            agreement = (agreement + issue_overlap) / 2

        return round(max(0.0, min(1.0, agreement)), 3)


debate_engine = DebateEngine()
