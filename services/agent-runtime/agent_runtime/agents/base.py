"""Agent Base Class — defines the interface all AISC agents must implement."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Any
from uuid import uuid4

from aisc_models import AgentType, Artifact, Critique, TaskContext
from aisc_utils import get_logger


class AgentStatus(StrEnum):
    CREATED = "created"
    INITIALIZING = "initializing"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    TERMINATED = "terminated"


class BaseAgent(ABC):
    def __init__(self, name: str, agent_type: AgentType) -> None:
        self.name = name
        self.agent_type = agent_type
        self.status = AgentStatus.CREATED
        self.logger = get_logger(f"agent.{name}")

    async def initialize(self) -> None:
        self.status = AgentStatus.INITIALIZING
        await self.on_init()
        self.status = AgentStatus.IDLE

    async def run(self, task: TaskContext) -> Artifact:
        self.status = AgentStatus.BUSY
        start = time.monotonic()
        try:
            await self.on_start(task)
            result = await self.generate(task)
            await self.on_complete(task, result)
            return result
        except Exception as e:
            self.status = AgentStatus.ERROR
            await self.on_error(task, e)
            raise
        finally:
            elapsed = time.monotonic() - start
            self.logger.info(
                "agent_run_complete",
                task_id=task.task_id,
                duration_ms=int(elapsed * 1000),
            )
            if self.status != AgentStatus.ERROR:
                self.status = AgentStatus.IDLE

    @abstractmethod
    async def generate(self, task: TaskContext) -> Artifact:
        ...

    async def critique(self, artifact: Artifact) -> Critique:
        return Critique(
            artifact_id=artifact.id,
            reviewer_id=uuid4(),
            overall_score=100.0,
            issues=[],
            strengths=["Self-review skipped"],
            improvements=[],
        )

    async def improve(self, artifact: Artifact, critique: Critique) -> Artifact:  # noqa: ARG002
        return artifact

    async def on_init(self) -> None:  # noqa: B027
        pass

    async def on_start(self, task: TaskContext) -> None:
        self.logger.info("agent_task_started", task_id=task.task_id, task_type=task.task_type)

    async def on_complete(self, task: TaskContext, result: Artifact) -> None:
        self.logger.info("agent_task_completed", task_id=task.task_id, artifact_id=result.id)

    async def on_error(self, task: TaskContext, error: Exception) -> None:
        self.logger.exception("agent_task_error", task_id=task.task_id, error=str(error))

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "agent_type": self.agent_type.value,
            "status": self.status.value,
        }
