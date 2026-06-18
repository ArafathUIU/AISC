"""AISC Scoring Engine — metric definitions, evaluation, and loop control."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class GateType(StrEnum):
    REQUIREMENTS = "requirements"
    ARCHITECTURE = "architecture"
    CODE = "code"
    TESTING = "testing"
    SECURITY = "security"
    DEPLOYMENT = "deployment"


@dataclass
class MetricDef:
    name: str
    weight: float
    threshold: float
    critical: bool = False
    description: str = ""


@dataclass
class GateConfig:
    gate_type: GateType
    minimum_score: float
    max_iterations: int
    metrics: list[MetricDef]
    death_penalties: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class MetricResult:
    metric_name: str
    score: float
    weight: float
    passed: bool
    justification: str


@dataclass
class EvaluationResult:
    artifact_id: str
    gate_type: GateType
    aggregate_score: float
    metric_results: list[MetricResult]
    passed: bool
    iteration: int
    feedback: str = ""


@dataclass
class LoopState:
    artifact_id: str
    gate_type: GateType
    current_iteration: int = 1
    max_iterations: int = 5
    threshold: float = 90.0
    score_history: list[float] = field(default_factory=list)
    stuck_count: int = 0


REQUIREMENTS_GATE = GateConfig(
    gate_type=GateType.REQUIREMENTS,
    minimum_score=90.0,
    max_iterations=5,
    metrics=[
        MetricDef("completeness", 0.25, 90.0, True, "All required sections filled"),
        MetricDef("clarity", 0.20, 85.0, False, "Unambiguous language"),
        MetricDef("consistency", 0.20, 85.0, False, "No internal contradictions"),
        MetricDef("feasibility", 0.20, 85.0, False, "Technically achievable"),
        MetricDef("business_alignment", 0.15, 90.0, True, "Solves stated problem"),
    ],
)

ARCHITECTURE_GATE = GateConfig(
    gate_type=GateType.ARCHITECTURE,
    minimum_score=90.0,
    max_iterations=5,
    metrics=[
        MetricDef("scalability", 0.25, 90.0, True, "Handles 10x load"),
        MetricDef("reliability", 0.20, 85.0, True, "No single points of failure"),
        MetricDef("security", 0.25, 90.0, True, "Trust boundaries defined"),
        MetricDef("maintainability", 0.15, 80.0, False, "Loose coupling"),
        MetricDef("cost_efficiency", 0.15, 75.0, False, "Resource estimates"),
    ],
)

CODE_GATE = GateConfig(
    gate_type=GateType.CODE,
    minimum_score=92.0,
    max_iterations=7,
    metrics=[
        MetricDef("complexity", 0.20, 85.0, False, "Cyclomatic complexity"),
        MetricDef("maintainability", 0.20, 85.0, False, "Readability index"),
        MetricDef("testability", 0.20, 90.0, True, "Injectable dependencies"),
        MetricDef("performance", 0.20, 85.0, False, "No N+1 queries"),
        MetricDef("security", 0.20, 95.0, True, "No vulnerabilities"),
    ],
)

TESTING_GATE = GateConfig(
    gate_type=GateType.TESTING,
    minimum_score=95.0,
    max_iterations=5,
    metrics=[
        MetricDef("coverage", 0.30, 90.0, True, "Line coverage percentage"),
        MetricDef("mutation_score", 0.30, 80.0, True, "Mutants killed"),
        MetricDef("reliability", 0.20, 95.0, True, "No flaky tests"),
        MetricDef("edge_cases", 0.20, 85.0, False, "Boundary conditions covered"),
    ],
)

SECURITY_GATE = GateConfig(
    gate_type=GateType.SECURITY,
    minimum_score=98.0,
    max_iterations=3,
    metrics=[
        MetricDef("vulnerability_scan", 0.35, 95.0, True, "SAST findings"),
        MetricDef("llm_review", 0.25, 95.0, True, "LLM security review"),
        MetricDef("secret_detection", 0.20, 100.0, True, "Zero secrets"),
        MetricDef("dependency_audit", 0.10, 90.0, False, "CVE check"),
        MetricDef("compliance", 0.10, 90.0, False, "OWASP/GDPR"),
    ],
)

DEPLOYMENT_GATE = GateConfig(
    gate_type=GateType.DEPLOYMENT,
    minimum_score=95.0,
    max_iterations=3,
    metrics=[
        MetricDef("stability", 0.40, 95.0, True, "Error rate post-deploy"),
        MetricDef("availability", 0.35, 99.0, True, "Health check success"),
        MetricDef("performance", 0.25, 90.0, False, "Latency vs baseline"),
    ],
)

GATES: dict[GateType, GateConfig] = {
    GateType.REQUIREMENTS: REQUIREMENTS_GATE,
    GateType.ARCHITECTURE: ARCHITECTURE_GATE,
    GateType.CODE: CODE_GATE,
    GateType.TESTING: TESTING_GATE,
    GateType.SECURITY: SECURITY_GATE,
    GateType.DEPLOYMENT: DEPLOYMENT_GATE,
}


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def evaluate_artifact(
    artifact_id: str,
    gate_type: GateType,
    metric_scores: dict[str, float],
    justifications: dict[str, str] | None = None,
    iteration: int = 1,
) -> EvaluationResult:
    gate = GATES.get(gate_type)
    if gate is None:
        raise ValueError(f"Unknown gate type: {gate_type}")

    if justifications is None:
        justifications = {}

    metric_results: list[MetricResult] = []
    weighted_sum = 0.0

    for metric in gate.metrics:
        raw = clamp(metric_scores.get(metric.name, 0.0))
        weighted_sum += raw * metric.weight
        metric_results.append(MetricResult(
            metric_name=metric.name,
            score=raw,
            weight=metric.weight,
            passed=raw >= metric.threshold,
            justification=justifications.get(metric.name, ""),
        ))

    aggregate = clamp(weighted_sum)

    for penalty in gate.death_penalties:
        condition = penalty.get("condition", lambda _r: False)
        if condition(metric_results):
            aggregate = min(aggregate, penalty.get("max_score", aggregate))

    critical_pass = all(
        r.passed for r in metric_results
        for m in gate.metrics
        if m.name == r.metric_name and m.critical
    )

    feedback = ""
    if not critical_pass:
        failed_critical = [
            r.metric_name for r in metric_results
            if not r.passed
            for m in gate.metrics
            if m.name == r.metric_name and m.critical
        ]
        feedback = f"Critical metrics failed: {', '.join(failed_critical)}"
    elif aggregate < gate.minimum_score:
        feedback = f"Score {aggregate:.1f} below threshold {gate.minimum_score}"

    return EvaluationResult(
        artifact_id=artifact_id,
        gate_type=gate_type,
        aggregate_score=round(aggregate, 1),
        metric_results=metric_results,
        passed=aggregate >= gate.minimum_score and critical_pass,
        iteration=iteration,
        feedback=feedback,
    )
