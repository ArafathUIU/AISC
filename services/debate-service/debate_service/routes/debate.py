"""Debate routes — create, review, resolve debates."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, HTTPException

from ..engine import ConsensusDecision, ReviewerResult, debate_engine

router = APIRouter()


@router.post("")
async def create_debate(body: dict[str, Any]) -> dict[str, Any]:
    artifact_id = UUID(body["artifact_id"])
    threshold = body.get("threshold", 90.0)
    debate = debate_engine.create(artifact_id, threshold)
    return debate.to_dict()


@router.get("/{debate_id}")
async def get_debate(debate_id: UUID) -> dict[str, Any]:
    debate = debate_engine.get(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")
    return debate.to_dict()


@router.post("/{debate_id}/reviews")
async def submit_reviews(
    debate_id: UUID, body: dict[str, Any],
) -> dict[str, Any]:
    debate = debate_engine.get(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    reviews_data = body.get("reviews", [])
    reviews = [
        ReviewerResult(
            reviewer_name=r.get("reviewer_name", "unknown"),
            overall_score=r.get("overall_score", 0.0),
            metric_scores=r.get("metric_scores", {}),
            issues=r.get("issues", []),
            strengths=r.get("strengths", []),
            improvements=r.get("improvements", []),
        )
        for r in reviews_data
    ]

    debate_round = debate_engine.submit_reviews(debate_id, reviews)

    return {
        "round": debate_round.round_number,
        "consensus": debate_round.consensus_decision.value,
        "agreement_score": debate_round.agreement_score,
        "resolution_note": debate_round.resolution_note,
        "reviewer_count": len(debate_round.reviewer_results),
    }


@router.post("/{debate_id}/resolve")
async def resolve_debate(
    debate_id: UUID, body: dict[str, Any],
) -> dict[str, Any]:
    debate = debate_engine.get(debate_id)
    if debate is None:
        raise HTTPException(status_code=404, detail="Debate not found")

    decision = ConsensusDecision(body.get("decision", "pass"))
    debate_engine.resolve(debate_id, decision)
    return {"status": debate.status.value, "decision": decision.value}
