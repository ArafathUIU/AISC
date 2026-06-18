"""Agent Scheduler — matches tasks to agents, manages priority queues."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from uuid import UUID


class Priority(IntEnum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass(order=True)
class QueuedTask:
    priority: int
    task_id: UUID = field(compare=False)
    task_type: str = field(compare=False)
    agent_type: str = field(compare=False)
    age: int = field(default=0, compare=False)
    input_data: dict = field(default_factory=dict, compare=False)


class AgentScheduler:
    def __init__(self) -> None:
        self._queues: dict[str, list[QueuedTask]] = {}
        self._available_agents: dict[str, int] = {}

    def update_availability(self, agent_type: str, count: int) -> None:
        self._available_agents[agent_type] = count

    def enqueue(self, task: QueuedTask) -> None:
        queue = self._queues.setdefault(task.agent_type, [])
        queue.append(task)
        queue.sort()

    def dequeue(self, agent_type: str) -> QueuedTask | None:
        queue = self._queues.get(agent_type, [])
        if not queue:
            return None
        return queue.pop(0)

    def get_pending_count(self, agent_type: str) -> int:
        return len(self._queues.get(agent_type, []))

    def age_tasks(self, agent_type: str) -> None:
        for task in self._queues.get(agent_type, []):
            task.age += 1
            task.priority = max(1, task.priority - (task.age // 10))

    def get_highest_priority(self, agent_type: str) -> QueuedTask | None:
        queue = self._queues.get(agent_type, [])
        return queue[0] if queue else None

    def remove_task(self, task_id: UUID) -> bool:
        for queue in self._queues.values():
            for i, task in enumerate(queue):
                if task.task_id == task_id:
                    queue.pop(i)
                    return True
        return False
