"""Product Manager Agent — translates business ideas into structured PRDs."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

PM_SYSTEM_PROMPT = """\
You are an expert Product Manager. Translate a business idea into a
comprehensive, structured Product Requirements Document (PRD).

Follow this exact structure:

## Problem Statement
- What problem does this solve? Who has this problem?

## Target Users
- Who are the primary users? List personas with their needs.

## Success Metrics
- Define 3-5 measurable KPIs. Each must be SMART.

## Features
- List 5-10 features by priority (Must Have, Should Have, Could Have).

## Constraints
- Technical, business, timeline, and budget constraints.

## Assumptions & Dependencies
- What assumptions are we making? External dependencies?

## Risks
- Identify 3-5 key risks with mitigation strategies.

Output ONLY valid JSON:
{
  "title": "Product Title",
  "problem_statement": "...",
  "target_users": [{"persona": "...", "needs": "..."}],
  "success_metrics": [
    {"metric": "...", "target": "...", "timeline": "..."}
  ],
  "features": [
    {"name": "...", "description": "...",
     "priority": "must_have|should_have|could_have"}
  ],
  "constraints": ["..."],
  "assumptions": ["..."],
  "risks": [
    {"risk": "...", "severity": "high|medium|low",
     "mitigation": "..."}
  ],
  "summary": "one paragraph summary"
}
"""

_MOCK_RISKS = [
    {
        "risk": "Low user adoption",
        "severity": "high",
        "mitigation": "Marketing campaign, user research",
    },
    {
        "risk": "Technical complexity",
        "severity": "medium",
        "mitigation": "Start with MVP, iterate",
    },
    {
        "risk": "Timeline slippage",
        "severity": "medium",
        "mitigation": "Agile development, weekly reviews",
    },
]

_MOCK_FEATURES = [
    {
        "name": "Core functionality",
        "description": "Core {idea} feature",
        "priority": "must_have",
    },
    {
        "name": "User authentication",
        "description": "Secure login and registration",
        "priority": "must_have",
    },
    {
        "name": "User dashboard",
        "description": "Overview of user activity",
        "priority": "should_have",
    },
    {
        "name": "Notifications",
        "description": "Email and push notifications",
        "priority": "could_have",
    },
]

_MOCK_METRICS = [
    {
        "metric": "User adoption",
        "target": "1000 users in 3 months",
        "timeline": "3 months",
    },
    {
        "metric": "User satisfaction",
        "target": "4.0+ rating",
        "timeline": "6 months",
    },
    {
        "metric": "Response time",
        "target": "<200ms p95",
        "timeline": "launch",
    },
]


class ProductManagerAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="pm-agent", agent_type=AgentType.PRODUCT_MANAGER)
        self._router = router
        self.logger = get_logger("agent.pm")

    async def generate(self, task: TaskContext) -> Artifact:
        idea = task.input.get(
            "business_idea", task.input.get("description", "")
        )
        messages = [
            {"role": "system", "content": PM_SYSTEM_PROMPT},
            {"role": "user", "content": f"Create a PRD for: {idea}"},
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.7, max_tokens=4096,
                complexity=TaskComplexity.MODERATE,
            )
            content = response.content
        else:
            content = self._build_mock_prd(idea)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.PRD,
            name=f"PRD: {idea[:50]}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"idea": idea},
        )

    def _build_mock_prd(self, idea: str) -> str:
        features = [
            {**f, "description": f["description"].format(idea=idea)}
            for f in _MOCK_FEATURES
        ]
        summary = (
            f"A solution for {idea} that delivers core value "
            "quickly and iterates based on user feedback."
        )
        return json.dumps({
            "title": idea,
            "problem_statement": f"Users need a solution for: {idea}",
            "target_users": [
                {
                    "persona": "End User",
                    "needs": f"A working solution for {idea}",
                },
            ],
            "success_metrics": _MOCK_METRICS,
            "features": features,
            "constraints": [
                "Budget: $50K",
                "Timeline: 12 weeks",
                "Team: 2 developers",
            ],
            "assumptions": [
                "Users have internet access",
                "Users have email addresses",
            ],
            "risks": _MOCK_RISKS,
            "summary": summary,
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []
            if not data.get("title"):
                issues.append("Missing title")
            if not data.get("problem_statement"):
                issues.append("Missing problem statement")
            if not data.get("features") or len(data.get("features", [])) < 3:
                issues.append("Fewer than 3 features defined")
            if (
                not data.get("success_metrics")
                or len(data.get("success_metrics", [])) < 2
            ):
                issues.append("Fewer than 2 success metrics")

            score = 100.0 - (len(issues) * 20)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Has required sections"] if not issues else []
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
