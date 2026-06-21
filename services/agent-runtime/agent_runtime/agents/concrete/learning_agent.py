"""Learning Agent — extracts patterns, optimizes prompts, validates knowledge."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

LEARNING_SYSTEM_PROMPT = """\
You are an AI Learning Engineer. Analyze historical iteration data to extract
patterns, optimize prompts, and improve future agent performance.

Analyze:
1. What distinguishes passing from failing outputs?
2. What prompt patterns led to first-iteration passes?
3. What common mistakes caused failures?
4. What improvement strategies were most effective?
5. What prompt modifications would improve success rate?

Output ONLY valid JSON:
{
  "patterns": [
    {
      "type": "success_pattern|failure_pattern|prompt_improvement",
      "description": "specific actionable pattern",
      "evidence_strength": "strong|moderate|weak",
      "confidence": 0.0-1.0,
      "source_count": N,
      "applicable_agents": ["agent_type"]
    }
  ],
  "statistics": {
    "records_analyzed": N,
    "pass_rate": 0.0,
    "avg_iterations_to_pass": 0.0,
    "avg_score_improvement": 0.0
  },
  "prompt_optimizations": [
    {
      "agent_type": "...",
      "current_issue": "...",
      "suggested_fix": "...",
      "expected_impact": "high|medium|low"
    }
  ],
  "validations": [
    {
      "pattern_id": "...",
      "still_valid": true,
      "new_confidence": 0.0,
      "trend": "strengthening|stable|weakening"
    }
  ],
  "summary": "..."
}
"""


class LearningAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="learning-agent", agent_type=AgentType.LEARNING)
        self._router = router
        self.logger = get_logger("agent.learning")

    async def generate(self, task: TaskContext) -> Artifact:
        records = task.input.get("learning_records", [])
        agent_type = task.input.get("agent_type", "unknown")

        messages = [
            {"role": "system", "content": LEARNING_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Analyze {len(records)} learning records for {agent_type}"
                ),
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.3, max_tokens=4096,
                complexity=TaskComplexity.COMPLEX,
            )
            content = response.content
        else:
            content = self._build_mock_analysis(agent_type, len(records))

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.RESEARCH_REPORT,
            name=f"Learning Analysis: {agent_type}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"agent_type": agent_type, "records_analyzed": len(records)},
        )

    def _build_mock_analysis(self, agent_type: str, record_count: int) -> str:
        return json.dumps({
            "patterns": [
                {
                    "type": "success_pattern",
                    "description": (
                        f"{agent_type} outputs with explicit structure "
                        "pass quality gates in fewer iterations"
                    ),
                    "evidence_strength": "strong",
                    "confidence": 0.89,
                    "source_count": 42,
                    "applicable_agents": [agent_type],
                },
                {
                    "type": "failure_pattern",
                    "description": (
                        "Missing success metrics in PRDs causes "
                        "business_alignment score to fail"
                    ),
                    "evidence_strength": "moderate",
                    "confidence": 0.76,
                    "source_count": 18,
                    "applicable_agents": ["product_manager"],
                },
                {
                    "type": "prompt_improvement",
                    "description": (
                        "Add explicit instruction to include quantified "
                        "KPIs for each feature"
                    ),
                    "evidence_strength": "strong",
                    "confidence": 0.92,
                    "source_count": 35,
                    "applicable_agents": ["product_manager"],
                },
            ],
            "statistics": {
                "records_analyzed": record_count or 100,
                "pass_rate": 0.73,
                "avg_iterations_to_pass": 2.8,
                "avg_score_improvement": 8.5,
            },
            "prompt_optimizations": [
                {
                    "agent_type": agent_type,
                    "current_issue": "Output lacks structure",
                    "suggested_fix": "Add explicit JSON output template to system prompt",
                    "expected_impact": "high",
                },
            ],
            "validations": [
                {
                    "pattern_id": "pat-001",
                    "still_valid": True,
                    "new_confidence": 0.91,
                    "trend": "strengthening",
                },
            ],
            "summary": (
                f"Analyzed {record_count or 100} records for {agent_type}. "
                "3 patterns extracted, 1 prompt optimization suggested."
            ),
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("patterns"):
                issues.append("No patterns extracted")
            if not data.get("statistics"):
                issues.append("Missing statistics section")
            if not data.get("prompt_optimizations"):
                issues.append("No prompt optimizations suggested")

            patterns = data.get("patterns", [])
            strong = sum(
                1 for p in patterns if p.get("evidence_strength") == "strong"
            )
            if strong == 0 and len(patterns) > 0:
                issues.append("No strong patterns found")

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    [f"Extracted {len(patterns)} actionable patterns"]
                    if not issues else []
                ),
                improvements=issues,
            )
        except json.JSONDecodeError:
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=0.0,
                issues=["Output is not valid JSON"],
                strengths=[],
                improvements=["Return valid JSON"],
            )


class KnowledgeAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(
            name="knowledge-agent", agent_type=AgentType.KNOWLEDGE,
        )
        self._router = router
        self.logger = get_logger("agent.knowledge")
        self._knowledge_base: dict[str, list[dict]] = {}

    async def generate(self, task: TaskContext) -> Artifact:
        query = task.input.get("query", task.input.get("question", ""))
        entity_type = task.input.get("entity_type", "")

        stored = self._knowledge_base.get(entity_type, [])
        matching = [
            item for item in stored
            if query.lower() in json.dumps(item).lower()
        ][:5]

        content = json.dumps({
            "query": query,
            "entity_type": entity_type,
            "results": matching,
            "total_found": len(matching),
            "source": "knowledge_graph",
        })

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.RESEARCH_REPORT,
            name=f"Knowledge Query: {query[:50]}",
            content=content,
            created_by_agent=self.agent_type.value,
        )

    def store(self, entity_type: str, data: dict) -> None:
        self._knowledge_base.setdefault(entity_type, []).append(data)

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []
            if not data.get("query"):
                issues.append("Missing query")
            score = 100.0 - (len(issues) * 20)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=["Valid query response"] if not issues else [],
                improvements=issues,
            )
        except json.JSONDecodeError:
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=0.0,
                issues=["Output is not valid JSON"],
                strengths=[],
                improvements=["Return valid JSON"],
            )
