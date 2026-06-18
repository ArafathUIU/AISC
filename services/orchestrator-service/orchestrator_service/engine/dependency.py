"""Dependency Resolver — ensures task dependencies are satisfied before execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from uuid import UUID


class DependencyStatus(StrEnum):
    WAITING = "waiting"
    READY = "ready"
    BLOCKED = "blocked"
    COMPLETED = "completed"


@dataclass
class DependencyNode:
    task_id: UUID
    depends_on: list[UUID] = field(default_factory=list)
    depended_by: list[UUID] = field(default_factory=list)
    status: DependencyStatus = DependencyStatus.WAITING


class DependencyResolver:
    def __init__(self) -> None:
        self._nodes: dict[UUID, DependencyNode] = {}
        self._completed: set[UUID] = set()

    def add_task(self, task_id: UUID, depends_on: list[UUID] | None = None) -> None:
        node = DependencyNode(task_id=task_id, depends_on=depends_on or [])
        self._nodes[task_id] = node
        for dep_id in node.depends_on:
            if dep_id in self._nodes:
                self._nodes[dep_id].depended_by.append(task_id)

        if not node.depends_on or all(dep in self._completed for dep in node.depends_on):
            node.status = DependencyStatus.READY

    def mark_completed(self, task_id: UUID) -> list[UUID]:
        newly_unblocked: list[UUID] = []
        node = self._nodes.get(task_id)
        if node is None:
            return newly_unblocked

        node.status = DependencyStatus.COMPLETED
        self._completed.add(task_id)

        for dependent_id in node.depended_by:
            dependent = self._nodes.get(dependent_id)
            if dependent is None or dependent.status == DependencyStatus.BLOCKED:
                continue
            if all(dep in self._completed for dep in dependent.depends_on):
                dependent.status = DependencyStatus.READY
                newly_unblocked.append(dependent_id)

        return newly_unblocked

    def mark_failed(self, task_id: UUID) -> list[UUID]:
        blocked: list[UUID] = []
        node = self._nodes.get(task_id)
        if node is None:
            return blocked

        for dependent_id in node.depended_by:
            dependent = self._nodes.get(dependent_id)
            if dependent and dependent.status != DependencyStatus.BLOCKED:
                dependent.status = DependencyStatus.BLOCKED
                blocked.append(dependent_id)
                blocked.extend(self.mark_failed(dependent_id))

        return blocked

    def is_ready(self, task_id: UUID) -> bool:
        node = self._nodes.get(task_id)
        if node is None:
            return True
        return node.status == DependencyStatus.READY

    def get_blocked_tasks(self) -> list[UUID]:
        return [
            tid for tid, node in self._nodes.items()
            if node.status == DependencyStatus.BLOCKED
        ]
