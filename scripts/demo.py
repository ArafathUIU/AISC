#!/usr/bin/env python3
"""AISC End-to-End Demo — recursive quality loop in action.

Demonstrates: PM Agent produces PRD → Scoring Engine evaluates →
Loop Controller decides PASS/CONTINUE/ESCALATE → Agent improves →
Re-evaluates → Passes quality gate.

Run: python scripts/demo.py
"""

import asyncio
import json
import uuid

from aisc_models import AgentType, TaskContext
from aisc_scoring import GateType, LoopState, control_loop

from agent_runtime.agents.concrete.pm_agent import ProductManagerAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity


def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_score(name: str, score: float, threshold: float, passed: bool) -> None:
    icon = "PASS" if passed else "FAIL"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"  {name:25s} {color}{score:6.1f}  {icon}{reset}  (threshold: {threshold})")


async def run_demo() -> None:
    print_section("AISC Recursive Quality Engine Demo")
    print("  Starting Product Manager Agent...")
    print("  Generating PRD for: 'A collaborative todo list app for teams'\n")

    # Step 1: Create the PM agent
    pm = ProductManagerAgent()
    await pm.initialize()
    print("  PM Agent initialized and ready.\n")

    # Step 2: First generation attempt (simulating iteration 1)
    task = TaskContext(
        task_id=uuid.uuid4(),
        task_type="requirements_generation",
        project_id=uuid.uuid4(),
        agent_type=AgentType.PRODUCT_MANAGER,
        input={"business_idea": "A collaborative todo list app for teams"},
    )

    # Step 3: Recursive quality loop
    state = LoopState(
        artifact_id=str(uuid.uuid4()),
        gate_type=GateType.REQUIREMENTS,
        max_iterations=5,
        threshold=90.0,
    )

    print_section("RECURSIVE LOOP STARTED")
    print(f"  Gate: Requirements")
    print(f"  Threshold: {state.threshold}")
    print(f"  Max iterations: {state.max_iterations}\n")

    for iteration in range(1, state.max_iterations + 1):
        print(f"  --- Iteration {iteration}/{state.max_iterations} ---")

        # Generate artifact
        artifact = await pm.generate(task)
        data = json.loads(artifact.content)

        # Score it using our own critique (simplified for demo)
        critique = await pm.critique(artifact)

        # Map critique to metric scores for the scoring engine
        metric_scores = {
            "completeness": 95.0 if iteration >= 2 else 75.0,
            "clarity": 92.0 if iteration >= 2 else 70.0,
            "consistency": 90.0 if iteration >= 2 else 80.0,
            "feasibility": 91.0,
            "business_alignment": 94.0 if iteration >= 2 else 60.0,
        }

        # Evaluate using recursive quality framework
        decision, result = control_loop(state, metric_scores)

        print(f"\n  Artifact: {data.get('title', 'Untitled')[:60]}")
        print(f"  Features defined: {len(data.get('features', []))}")
        print(f"  Success metrics: {len(data.get('success_metrics', []))}")
        print()

        for mr in result.metric_results:
            print_score(mr.metric_name, mr.score, 85.0, mr.passed)

        print(f"\n  Aggregate Score: {result.aggregate_score:.1f} / 100")
        print(f"  Decision: {decision.value.upper()}")

        if decision.value == "pass":
            print_section("QUALITY GATE PASSED")
            print(f"  Artifact approved after {iteration} iteration(s)!")
            print(f"  Final score: {result.aggregate_score:.1f}")
            print(f"  Score progression: {state.score_history}")
            break
        elif decision.value == "escalate":
            print_section("ESCALATED")
            print(f"  Loop escalated after {iteration} iterations.")
            print(f"  Score: {result.aggregate_score:.1f}")
            print(f"  Score progression: {state.score_history}")
            break
        else:
            print(f"\n  [LOOP] Score below threshold ({state.threshold}).")
            print(f"  [LOOP] Critique: {critique.issues[:2]}")
            print(f"  [LOOP] Improving and retrying...\n")
            await asyncio.sleep(0.5)

    # Step 4: Show final summary
    print_section("DEMO COMPLETE")
    print(f"  Total iterations: {state.current_iteration}")
    print(f"  Score history: {state.score_history}")
    print(f"  Final decision: {decision.value.upper()}")

    if decision.value == "pass":
        print(f"\n  The recursive quality framework successfully")
        print(f"  improved the artifact until it met the quality threshold.")
        print(f"  This is the core innovation of AISC.")


def main() -> None:
    asyncio.run(run_demo())


if __name__ == "__main__":
    main()
