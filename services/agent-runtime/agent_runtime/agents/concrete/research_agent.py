"""Research Agent — investigates technologies, competitors, and domain knowledge."""

from __future__ import annotations

import json
from uuid import uuid4

from aisc_models import AgentType, Artifact, ArtifactType, Critique, TaskContext
from aisc_utils import get_logger

from agent_runtime.agents.base import BaseAgent
from agent_runtime.llm.router import LLMRouter, TaskComplexity

RESEARCH_SYSTEM_PROMPT = """\
You are an expert Research Analyst. Investigate technologies, competitors,
and domains thoroughly. Provide structured, cited, actionable research.

Follow this structure:
1. Research Question — restate clearly
2. Findings — key discoveries with citations
3. Technology/Competitor Analysis — structured comparison
4. Recommendations — clear, actionable recommendations with confidence levels
5. Limitations — what's missing, what's uncertain
6. Sources — all cited sources

For technology evaluations, score on: maturity, community, performance,
learning curve, ecosystem, licensing (each 0-10).

Output ONLY valid JSON:
{
  "research_question": "...",
  "findings": [{"finding": "...", "source": "..."}],
  "analysis": {
    "type": "technology|competitor",
    "items": [
      {"name": "...", "scores": {"maturity": 8, "community": 7},
       "pros": ["..."], "cons": ["..."], "recommendation": "..."}
    ]
  },
  "recommendations": [
    {"recommendation": "...", "confidence": "high|medium|low",
     "rationale": "..."}
  ],
  "limitations": ["..."],
  "sources": [{"title": "...", "url": "...", "type": "doc|article|api_ref"}]
}
"""


class ResearchAgent(BaseAgent):
    def __init__(self, router: LLMRouter | None = None) -> None:
        super().__init__(name="research-agent", agent_type=AgentType.RESEARCH)
        self._router = router
        self.logger = get_logger("agent.research")

    async def generate(self, task: TaskContext) -> Artifact:
        question = task.input.get("question", task.input.get("description", ""))
        research_type = task.input.get("research_type", "technology")

        messages = [
            {"role": "system", "content": RESEARCH_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"Research ({research_type}): {question}",
            },
        ]

        if self._router:
            response = await self._router.route(
                messages, temperature=0.5, max_tokens=4096,
                complexity=TaskComplexity.MODERATE,
            )
            content = response.content
        else:
            content = self._build_mock_research(question, research_type)

        return Artifact(
            project_id=task.project_id,
            task_id=task.task_id,
            type=ArtifactType.RESEARCH_REPORT,
            name=f"Research: {question[:50]}",
            content=content,
            created_by_agent=self.agent_type.value,
            metadata={"question": question, "research_type": research_type},
        )

    def _build_mock_research(self, question: str, research_type: str) -> str:
        return json.dumps({
            "research_question": question,
            "findings": [
                {
                    "finding": f"Primary analysis of {question}",
                    "source": "Industry research (2024)",
                },
                {
                    "finding": f"Secondary sources confirm {question} trends",
                    "source": "Technical documentation review",
                },
            ],
            "analysis": {
                "type": research_type,
                "items": [
                    {
                        "name": "Option A",
                        "scores": {
                            "maturity": 9, "community": 8, "performance": 7,
                            "learning_curve": 6, "ecosystem": 8, "licensing": 9,
                        },
                        "pros": ["Mature ecosystem", "Large community"],
                        "cons": ["Steep learning curve", "Performance overhead"],
                        "recommendation": "Best for enterprise use cases",
                    },
                ],
            },
            "recommendations": [
                {
                    "recommendation": "Adopt Option A for production use",
                    "confidence": "high",
                    "rationale": "Strong maturity and community support",
                },
            ],
            "limitations": [
                "Research based on publicly available data only",
                "Performance benchmarks from vendor documentation",
            ],
            "sources": [
                {
                    "title": "Official Documentation",
                    "url": "https://docs.example.com",
                    "type": "doc",
                },
            ],
        })

    async def critique(self, artifact: Artifact) -> Critique:
        try:
            data = json.loads(artifact.content)
            issues: list[str] = []

            if not data.get("research_question"):
                issues.append("Missing research question")
            if not data.get("findings") or len(data.get("findings", [])) < 2:
                issues.append("Fewer than 2 findings")
            if not data.get("recommendations") or len(
                data.get("recommendations", [])
            ) < 1:
                issues.append("No recommendations provided")
            if not data.get("sources") or len(data.get("sources", [])) < 1:
                issues.append("No sources cited")
            if not data.get("limitations"):
                issues.append("Missing limitations section")

            score = 100.0 - (len(issues) * 15)
            return Critique(
                artifact_id=artifact.id,
                reviewer_id=uuid4(),
                overall_score=max(0.0, score),
                issues=issues,
                strengths=(
                    ["Well-structured research"] if not issues else []
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
