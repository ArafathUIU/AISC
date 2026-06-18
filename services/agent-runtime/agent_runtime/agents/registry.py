"""Agent Registry — tracks all registered agent instances."""

from __future__ import annotations

from .base import BaseAgent


class AgentRegistry:
    def __init__(self) -> None:
        self._agents: dict[str, BaseAgent] = {}

    def register(self, agent: BaseAgent) -> None:
        self._agents[agent.name] = agent

    def get(self, name: str) -> BaseAgent | None:
        return self._agents.get(name)

    def list(self) -> list[BaseAgent]:
        return list(self._agents.values())

    def get_by_type(self, agent_type: str) -> list[BaseAgent]:
        return [a for a in self._agents.values() if a.agent_type.value == agent_type]

    def get_idle_by_type(self, agent_type: str) -> list[BaseAgent]:
        from .base import AgentStatus
        return [
            a for a in self._agents.values()
            if a.agent_type.value == agent_type and a.status == AgentStatus.IDLE
        ]


agent_registry = AgentRegistry()
