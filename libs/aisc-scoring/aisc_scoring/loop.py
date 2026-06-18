"""AISC Scoring — loop controller for recursive quality cycles."""

from __future__ import annotations

from enum import StrEnum

from .engine import (
    EvaluationResult,
    LoopState,
    evaluate_artifact,
)


class LoopDecision(StrEnum):
    CONTINUE = "continue"
    PASS = "pass"
    ESCALATE = "escalate"


def control_loop(
    state: LoopState,
    metric_scores: dict[str, float],
    justifications: dict[str, str] | None = None,
) -> tuple[LoopDecision, EvaluationResult]:
    result = evaluate_artifact(
        artifact_id=state.artifact_id,
        gate_type=state.gate_type,
        metric_scores=metric_scores,
        justifications=justifications,
        iteration=state.current_iteration,
    )

    state.score_history.append(result.aggregate_score)

    if result.passed:
        return LoopDecision.PASS, result

    if state.current_iteration >= state.max_iterations:
        return LoopDecision.ESCALATE, result

    if _is_degrading(state):
        state.stuck_count += 1
        if state.stuck_count >= 2:
            return LoopDecision.ESCALATE, result

    if _is_stuck(state):
        state.stuck_count += 1
        if state.stuck_count >= 3:
            return LoopDecision.ESCALATE, result

    if result.aggregate_score < 30:
        return LoopDecision.ESCALATE, result

    state.current_iteration += 1
    return LoopDecision.CONTINUE, result


def _is_degrading(state: LoopState) -> bool:
    if len(state.score_history) < 2:
        return False
    return state.score_history[-1] < state.score_history[-2]


def _is_stuck(state: LoopState) -> bool:
    if len(state.score_history) < 3:
        return False
    recent = state.score_history[-3:]
    improvements = [recent[i] - recent[i - 1] for i in range(1, len(recent))]
    avg_improvement = sum(improvements) / len(improvements)
    return avg_improvement < 1.0
