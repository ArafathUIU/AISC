"""Scoring engine and loop controller tests."""


import pytest
from aisc_scoring import (
    GATES,
    GateType,
    LoopDecision,
    LoopState,
    clamp,
    control_loop,
    evaluate_artifact,
)


class TestClamp:
    def test_clamp_in_range(self) -> None:
        assert clamp(50.0) == 50.0

    def test_clamp_below_zero(self) -> None:
        assert clamp(-10.0) == 0.0

    def test_clamp_above_hundred(self) -> None:
        assert clamp(150.0) == 100.0


class TestGateConfigs:
    def test_all_six_gates_defined(self) -> None:
        assert len(GATES) == 6
        assert GateType.REQUIREMENTS in GATES
        assert GateType.ARCHITECTURE in GATES
        assert GateType.CODE in GATES
        assert GateType.TESTING in GATES
        assert GateType.SECURITY in GATES
        assert GateType.DEPLOYMENT in GATES

    def test_requirements_gate(self) -> None:
        gate = GATES[GateType.REQUIREMENTS]
        assert gate.minimum_score == 90.0
        assert gate.max_iterations == 5
        assert len(gate.metrics) == 5

    def test_security_gate_highest_threshold(self) -> None:
        gate = GATES[GateType.SECURITY]
        assert gate.minimum_score == 98.0
        assert gate.max_iterations == 3

    def test_code_gate_most_iterations(self) -> None:
        gate = GATES[GateType.CODE]
        assert gate.max_iterations == 7

    def test_metric_weights_sum_to_one(self) -> None:
        for gate in GATES.values():
            total_weight = sum(m.weight for m in gate.metrics)
            assert total_weight == pytest.approx(1.0, abs=0.01)


class TestEvaluateArtifact:
    def test_all_metrics_pass_above_threshold(self) -> None:
        scores = {
            "completeness": 95, "clarity": 92, "consistency": 90,
            "feasibility": 91, "business_alignment": 94,
        }
        result = evaluate_artifact("art-1", GateType.REQUIREMENTS, scores)
        assert result.passed is True
        assert result.aggregate_score > 90
        assert len(result.metric_results) == 5

    def test_fails_when_below_threshold(self) -> None:
        scores = {
            "completeness": 80, "clarity": 80, "consistency": 80,
            "feasibility": 80, "business_alignment": 80,
        }
        result = evaluate_artifact("art-1", GateType.REQUIREMENTS, scores)
        assert result.passed is False
        assert result.aggregate_score < 90

    def test_fails_critical_metric_even_if_aggregate_passes(self) -> None:
        scores = {
            "completeness": 60, "clarity": 100, "consistency": 100,
            "feasibility": 100, "business_alignment": 100,
        }
        result = evaluate_artifact("art-1", GateType.REQUIREMENTS, scores)
        assert result.passed is False

    def test_unknown_gate_raises(self) -> None:
        with pytest.raises(ValueError, match="Unknown gate"):
            evaluate_artifact("x", "invalid_gate", {})  # type: ignore[arg-type]

    def test_justifications_stored(self) -> None:
        scores = {"coverage": 95, "mutation_score": 85, "reliability": 96, "edge_cases": 90}
        justifications = {"coverage": "All lines covered"}
        result = evaluate_artifact(
            "art-1", GateType.TESTING, scores, justifications,
        )
        assert result.metric_results[0].justification == "All lines covered"


class TestLoopController:
    def test_loop_passes_on_good_score(self) -> None:
        state = LoopState(artifact_id="a1", gate_type=GateType.REQUIREMENTS)
        scores = {
            "completeness": 95, "clarity": 92, "consistency": 90,
            "feasibility": 91, "business_alignment": 94,
        }
        decision, result = control_loop(state, scores)
        assert decision == LoopDecision.PASS
        assert result.passed is True

    def test_loop_continues_on_low_score(self) -> None:
        state = LoopState(artifact_id="a1", gate_type=GateType.REQUIREMENTS)
        scores = {
            "completeness": 70, "clarity": 70, "consistency": 70,
            "feasibility": 70, "business_alignment": 70,
        }
        decision, _ = control_loop(state, scores)
        assert decision == LoopDecision.CONTINUE
        assert state.current_iteration == 2

    def test_loop_escalates_at_max_iterations(self) -> None:
        state = LoopState(
            artifact_id="a1", gate_type=GateType.REQUIREMENTS,
            current_iteration=5, max_iterations=5,
        )
        scores = {
            "completeness": 70, "clarity": 70, "consistency": 70,
            "feasibility": 70, "business_alignment": 70,
        }
        decision, _ = control_loop(state, scores)
        assert decision == LoopDecision.ESCALATE

    def test_loop_escalates_on_degrading_scores(self) -> None:
        state = LoopState(
            artifact_id="a1", gate_type=GateType.REQUIREMENTS,
            score_history=[80.0, 75.0],
        )
        scores = {
            "completeness": 70, "clarity": 70, "consistency": 70,
            "feasibility": 70, "business_alignment": 70,
        }
        state.stuck_count = 1
        decision, _ = control_loop(state, scores)
        assert decision == LoopDecision.ESCALATE

    def test_loop_escalates_on_very_low_score(self) -> None:
        state = LoopState(artifact_id="a1", gate_type=GateType.REQUIREMENTS)
        scores = {
            "completeness": 10, "clarity": 10, "consistency": 10,
            "feasibility": 10, "business_alignment": 10,
        }
        decision, _ = control_loop(state, scores)
        assert decision == LoopDecision.ESCALATE
