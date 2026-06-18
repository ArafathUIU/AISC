"""Workflow DAG Engine — directed acyclic graph of tasks with ordering."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class NodeStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


class WorkflowStatus(StrEnum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WorkflowNode:
    id: UUID = field(default_factory=uuid4)
    name: str = ""
    task_type: str = ""
    agent_type: str = ""
    status: NodeStatus = NodeStatus.PENDING
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    dependencies: list[UUID] = field(default_factory=list)


@dataclass
class WorkflowDAG:
    id: UUID = field(default_factory=uuid4)
    project_id: UUID = field(default_factory=uuid4)
    name: str = ""
    status: WorkflowStatus = WorkflowStatus.CREATED
    nodes: dict[UUID, WorkflowNode] = field(default_factory=dict)
    edges: list[tuple[UUID, UUID]] = field(default_factory=list)

    def add_node(self, node: WorkflowNode) -> None:
        if node.id in self.nodes:
            raise ValueError(f"Node {node.id} already exists")
        self.nodes[node.id] = node

    def add_edge(self, from_id: UUID, to_id: UUID) -> None:
        if from_id not in self.nodes or to_id not in self.nodes:
            raise ValueError("Edge references unknown node")
        self.edges.append((from_id, to_id))
        self.nodes[to_id].dependencies.append(from_id)

    def get_ready_nodes(self) -> list[WorkflowNode]:
        ready = []
        for node in self.nodes.values():
            if node.status != NodeStatus.PENDING:
                continue
            if self._dependencies_satisfied(node):
                ready.append(node)
        return ready

    def _dependencies_satisfied(self, node: WorkflowNode) -> bool:
        return all(
            self.nodes[dep].status == NodeStatus.COMPLETED
            for dep in node.dependencies
        )

    def topological_order(self) -> list[WorkflowNode]:
        in_degree: dict[UUID, int] = dict.fromkeys(self.nodes, 0)
        for _from_id, to_id in self.edges:
            in_degree[to_id] = in_degree.get(to_id, 0) + 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        result: list[WorkflowNode] = []

        while queue:
            nid = queue.pop(0)
            result.append(self.nodes[nid])
            for from_id, to_id in self.edges:
                if from_id == nid:
                    in_degree[to_id] -= 1
                    if in_degree[to_id] == 0:
                        queue.append(to_id)

        if len(result) != len(self.nodes):
            raise ValueError("Cycle detected in workflow DAG")
        return result

    def detect_cycles(self) -> list[list[UUID]]:
        try:
            self.topological_order()
            return []
        except ValueError:
            pass

        visited: set[UUID] = set()
        rec_stack: set[UUID] = set()
        cycles: list[list[UUID]] = []

        def dfs(nid: UUID, path: list[UUID]) -> None:
            visited.add(nid)
            rec_stack.add(nid)
            path.append(nid)
            for from_id, to_id in self.edges:
                if from_id == nid:
                    if to_id in rec_stack:
                        cycle_start = path.index(to_id)
                        cycles.append(list(path[cycle_start:]))
                    elif to_id not in visited:
                        dfs(to_id, path)
            rec_stack.discard(nid)
            path.pop()

        for nid in self.nodes:
            if nid not in visited:
                dfs(nid, [])

        return cycles

    def is_complete(self) -> bool:
        return all(
            node.status in (NodeStatus.COMPLETED, NodeStatus.FAILED)
            for node in self.nodes.values()
        )

    def has_failures(self) -> bool:
        return any(
            node.status == NodeStatus.FAILED
            for node in self.nodes.values()
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": str(self.id),
            "project_id": str(self.project_id),
            "name": self.name,
            "status": self.status.value,
            "nodes": {
                str(nid): {
                    "id": str(node.id),
                    "name": node.name,
                    "task_type": node.task_type,
                    "agent_type": node.agent_type,
                    "status": node.status.value,
                    "dependencies": [str(d) for d in node.dependencies],
                }
                for nid, node in self.nodes.items()
            },
            "edges": [
                {"from": str(f), "to": str(t)}
                for f, t in self.edges
            ],
        }
