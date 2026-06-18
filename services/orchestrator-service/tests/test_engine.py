"""Orchestrator engine tests — workflow DAG, scheduler, dependency, escalation."""

from uuid import uuid4

import pytest
from orchestrator_service.engine.dependency import DependencyResolver
from orchestrator_service.engine.escalation import (
    Escalation,
    EscalationHandler,
    EscalationSeverity,
    EscalationType,
)
from orchestrator_service.engine.scheduler import AgentScheduler, QueuedTask
from orchestrator_service.engine.workflow import (
    NodeStatus,
    WorkflowDAG,
    WorkflowNode,
)


class TestWorkflowNode:
    def test_initial_status_is_pending(self) -> None:
        node = WorkflowNode(name="test")
        assert node.status == NodeStatus.PENDING

    def test_node_has_id(self) -> None:
        node = WorkflowNode(name="test")
        assert node.id is not None

    def test_node_input_data(self) -> None:
        node = WorkflowNode(name="test", input_data={"key": "value"})
        assert node.input_data["key"] == "value"


class TestWorkflowDAG:
    def test_add_node(self) -> None:
        dag = WorkflowDAG()
        node = WorkflowNode(name="test")
        dag.add_node(node)
        assert node.id in dag.nodes

    def test_add_duplicate_node_raises(self) -> None:
        dag = WorkflowDAG()
        node = WorkflowNode(name="test")
        dag.add_node(node)
        with pytest.raises(ValueError, match="already exists"):
            dag.add_node(node)

    def test_add_edge(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A")
        b = WorkflowNode(name="B")
        dag.add_node(a)
        dag.add_node(b)
        dag.add_edge(a.id, b.id)
        assert b.dependencies == [a.id]
        assert len(dag.edges) == 1

    def test_add_edge_unknown_node_raises(self) -> None:
        dag = WorkflowDAG()
        with pytest.raises(ValueError, match="unknown node"):
            dag.add_edge(uuid4(), uuid4())

    def test_topological_order_simple(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A")
        b = WorkflowNode(name="B")
        c = WorkflowNode(name="C")
        for n in (a, b, c):
            dag.add_node(n)
        dag.add_edge(a.id, b.id)
        dag.add_edge(b.id, c.id)
        order = dag.topological_order()
        names = [n.name for n in order]
        assert names == ["A", "B", "C"]

    def test_topological_order_parallel(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A")
        b = WorkflowNode(name="B")
        c = WorkflowNode(name="C")
        for n in (a, b, c):
            dag.add_node(n)
        dag.add_edge(a.id, b.id)
        dag.add_edge(a.id, c.id)
        order = dag.topological_order()
        assert order[0].name == "A"
        assert {n.name for n in order[1:]} == {"B", "C"}

    def test_cycle_detection(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A")
        b = WorkflowNode(name="B")
        dag.add_node(a)
        dag.add_node(b)
        dag.add_edge(a.id, b.id)
        dag.add_edge(b.id, a.id)
        cycles = dag.detect_cycles()
        assert len(cycles) > 0
        with pytest.raises(ValueError, match="Cycle"):
            dag.topological_order()

    def test_get_ready_nodes(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A")
        b = WorkflowNode(name="B")
        dag.add_node(a)
        dag.add_node(b)
        dag.add_edge(a.id, b.id)
        ready = dag.get_ready_nodes()
        assert len(ready) == 1
        assert ready[0].name == "A"

    def test_is_complete(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A", status=NodeStatus.COMPLETED)
        dag.add_node(a)
        assert dag.is_complete()

    def test_has_failures(self) -> None:
        dag = WorkflowDAG()
        a = WorkflowNode(name="A", status=NodeStatus.FAILED)
        dag.add_node(a)
        assert dag.has_failures()

    def test_to_dict(self) -> None:
        dag = WorkflowDAG(name="test_dag")
        node = WorkflowNode(name="test")
        dag.add_node(node)
        d = dag.to_dict()
        assert d["name"] == "test_dag"
        assert len(d["nodes"]) == 1


class TestAgentScheduler:
    def test_enqueue_and_dequeue(self) -> None:
        s = AgentScheduler()
        task_id = uuid4()
        s.enqueue(QueuedTask(
            priority=3, task_id=task_id, task_type="code_gen", agent_type="developer",
        ))
        dequeued = s.dequeue("developer")
        assert dequeued is not None
        assert dequeued.task_id == task_id

    def test_empty_queue_returns_none(self) -> None:
        s = AgentScheduler()
        assert s.dequeue("developer") is None

    def test_remove_task(self) -> None:
        s = AgentScheduler()
        task_id = uuid4()
        s.enqueue(QueuedTask(priority=5, task_id=task_id, task_type="t", agent_type="dev"))
        assert s.remove_task(task_id) is True
        assert s.dequeue("dev") is None

    def test_aging_reduces_priority(self) -> None:
        s = AgentScheduler()
        task_id = uuid4()
        s.enqueue(QueuedTask(priority=5, task_id=task_id, task_type="t", agent_type="dev"))
        for _ in range(50):
            s.age_tasks("dev")
        task = s.dequeue("dev")
        assert task is not None
        assert task.priority < 5


class TestDependencyResolver:
    def test_no_deps_is_ready(self) -> None:
        r = DependencyResolver()
        tid = uuid4()
        r.add_task(tid)
        assert r.is_ready(tid)

    def test_with_satisfied_deps(self) -> None:
        r = DependencyResolver()
        t1 = uuid4()
        t2 = uuid4()
        r.add_task(t1)
        r.add_task(t2, depends_on=[t1])
        assert not r.is_ready(t2)
        r.mark_completed(t1)
        assert r.is_ready(t2)

    def test_failed_dep_blocks_dependent(self) -> None:
        r = DependencyResolver()
        t1 = uuid4()
        t2 = uuid4()
        r.add_task(t1)
        r.add_task(t2, depends_on=[t1])
        blocked = r.mark_failed(t1)
        assert t2 in blocked


class TestEscalationHandler:
    def test_create_escalation(self) -> None:
        h = EscalationHandler()
        esc = h.create(Escalation(
            escalation_type=EscalationType.AGENT_ERROR,
            severity=EscalationSeverity.HIGH,
            title="Test escalation",
        ))
        assert esc.status == "open"

    def test_resolve_escalation(self) -> None:
        h = EscalationHandler()
        esc = h.create(Escalation(title="Test"))
        h.resolve(esc.id, "Fixed by human")
        assert esc.status == "resolved"

    def test_quality_gate_escalation(self) -> None:
        h = EscalationHandler()
        aid = uuid4()
        tid = uuid4()
        esc = h.create_quality_gate_escalation(
            "code", aid, tid, final_score=88, iterations=7,
            score_history=[72, 78, 84, 88, 88, 88, 88],
        )
        assert esc.escalation_type == EscalationType.MAX_ITERATIONS
        assert esc.severity == EscalationSeverity.HIGH
