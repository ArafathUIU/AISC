"""Debate service engine tests."""

from uuid import uuid4

from debate_service.engine import (
    ConsensusDecision,
    DebateEngine,
    DebateStatus,
    ReviewerResult,
)


class TestDebateEngine:
    def test_create_debate(self) -> None:
        engine = DebateEngine()
        artifact_id = uuid4()
        debate = engine.create(artifact_id, threshold=90.0)
        assert debate.status == DebateStatus.OPEN
        assert debate.threshold == 90.0
        assert debate.max_rounds == 3

    def test_get_debate(self) -> None:
        engine = DebateEngine()
        artifact_id = uuid4()
        debate = engine.create(artifact_id)
        retrieved = engine.get(debate.id)
        assert retrieved is debate

    def test_get_missing_returns_none(self) -> None:
        engine = DebateEngine()
        assert engine.get(uuid4()) is None

    def test_unanimous_pass(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=90.0)
        reviews = [
            ReviewerResult(reviewer_name="R1", overall_score=95.0),
            ReviewerResult(reviewer_name="R2", overall_score=92.0),
            ReviewerResult(reviewer_name="R3", overall_score=94.0),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.consensus_decision == ConsensusDecision.PASS

    def test_unanimous_fail(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=90.0)
        reviews = [
            ReviewerResult(reviewer_name="R1", overall_score=72.0),
            ReviewerResult(reviewer_name="R2", overall_score=68.0),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.consensus_decision == ConsensusDecision.FAIL

    def test_split_decision_majority_pass(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=90.0)
        reviews = [
            ReviewerResult(reviewer_name="R1", overall_score=95.0),
            ReviewerResult(reviewer_name="R2", overall_score=92.0),
            ReviewerResult(reviewer_name="R3", overall_score=70.0),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.consensus_decision == ConsensusDecision.PASS

    def test_conflict_when_low_agreement(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=90.0)
        reviews = [
            ReviewerResult(reviewer_name="R1", overall_score=95.0),
            ReviewerResult(reviewer_name="R2", overall_score=40.0),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.consensus_decision == ConsensusDecision.CONFLICT

    def test_agreement_score_perfect(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4())
        reviews = [
            ReviewerResult(reviewer_name="R1", overall_score=90.0),
            ReviewerResult(reviewer_name="R2", overall_score=90.0),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.agreement_score == 1.0

    def test_max_rounds_escalates_conflict(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=90.0)

        for _ in range(2):
            engine.submit_reviews(debate.id, [
                ReviewerResult(reviewer_name="R1", overall_score=95.0),
                ReviewerResult(reviewer_name="R2", overall_score=40.0),
            ])

        debate_round = engine.submit_reviews(debate.id, [
            ReviewerResult(reviewer_name="R1", overall_score=95.0),
            ReviewerResult(reviewer_name="R2", overall_score=40.0),
        ])
        assert debate_round.consensus_decision == ConsensusDecision.ESCALATE

    def test_resolve(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4())
        engine.resolve(debate.id, ConsensusDecision.PASS)
        assert debate.final_decision == ConsensusDecision.PASS
        assert debate.status == DebateStatus.RESOLVED

    def test_resolve_escalate_is_deadlocked(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4())
        engine.resolve(debate.id, ConsensusDecision.ESCALATE)
        assert debate.status == DebateStatus.DEADLOCKED

    def test_single_review_escalates(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4())
        reviews = [ReviewerResult(reviewer_name="R1", overall_score=95.0)]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.consensus_decision == ConsensusDecision.ESCALATE

    def test_issue_overlap_in_agreement(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4())
        reviews = [
            ReviewerResult(
                reviewer_name="R1", overall_score=95.0,
                issues=["Missing tests", "No docs"],
            ),
            ReviewerResult(
                reviewer_name="R2", overall_score=95.0,
                issues=["Missing tests", "Slow endpoint"],
            ),
        ]
        debate_round = engine.submit_reviews(debate.id, reviews)
        assert debate_round.agreement_score > 0.5

    def test_to_dict(self) -> None:
        engine = DebateEngine()
        debate = engine.create(uuid4(), threshold=92.0)
        d = debate.to_dict()
        assert d["threshold"] == 92.0
        assert d["status"] == "open"
        assert d["current_round"] == 0
