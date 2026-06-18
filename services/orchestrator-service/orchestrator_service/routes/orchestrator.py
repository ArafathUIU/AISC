"""Orchestrator routes — workflow management and project coordination."""

from typing import Any
from uuid import UUID, uuid4

from fastapi import APIRouter

from ..engine.escalation import EscalationHandler
from ..engine.scheduler import AgentScheduler
from ..engine.workflow import WorkflowDAG, WorkflowNode, WorkflowStatus

router = APIRouter()
workflows: dict[UUID, WorkflowDAG] = {}
scheduler = AgentScheduler()
escalations = EscalationHandler()


@router.post("/projects")
async def create_project(body: dict[str, Any]) -> dict[str, Any]:
    project_id = uuid4()
    dag = WorkflowDAG(project_id=project_id, name=body.get("name", "Untitled"))
    workflows[project_id] = dag
    return {"project_id": str(project_id), "name": dag.name}


@router.get("/projects/{project_id}/workflow")
async def get_workflow(project_id: UUID) -> dict[str, Any]:
    dag = workflows.get(project_id)
    if dag is None:
        return {"workflow": None}
    return {"workflow": dag.to_dict()}


@router.post("/projects/{project_id}/workflow/nodes")
async def add_workflow_node(project_id: UUID, body: dict[str, Any]) -> dict[str, Any]:
    dag = workflows.get(project_id)
    if dag is None:
        return {"error": "Project not found"}

    node = WorkflowNode(
        name=body.get("name", "Untitled"),
        task_type=body.get("task_type", "unknown"),
        agent_type=body.get("agent_type", "unknown"),
        input_data=body.get("input", {}),
    )
    dag.add_node(node)
    return {"node_id": str(node.id), "name": node.name}


@router.post("/projects/{project_id}/workflow/edges")
async def add_workflow_edge(project_id: UUID, body: dict[str, Any]) -> dict[str, Any]:
    dag = workflows.get(project_id)
    if dag is None:
        return {"error": "Project not found"}

    from_id = UUID(body["from"])
    to_id = UUID(body["to"])
    dag.add_edge(from_id, to_id)
    return {"status": "edge_added", "from": str(from_id), "to": str(to_id)}


@router.post("/projects/{project_id}/start")
async def start_workflow(project_id: UUID) -> dict[str, Any]:
    dag = workflows.get(project_id)
    if dag is None:
        return {"error": "Project not found"}

    try:
        order = dag.topological_order()
        dag.status = WorkflowStatus.RUNNING
        return {
            "status": "started",
            "node_count": len(order),
            "order": [str(n.id) for n in order],
        }
    except ValueError as e:
        cycles = dag.detect_cycles()
        return {
            "status": "failed",
            "error": str(e),
            "cycles": [[str(nid) for nid in c] for c in cycles],
        }


@router.get("/projects/{project_id}/workflow/ready")
async def get_ready_nodes(project_id: UUID) -> dict[str, Any]:
    dag = workflows.get(project_id)
    if dag is None:
        return {"ready": []}
    ready = dag.get_ready_nodes()
    return {"ready": [{"id": str(n.id), "name": n.name} for n in ready]}


@router.get("/escalations")
async def list_escalations() -> dict[str, Any]:
    open_esc = escalations.list_open()
    return {
        "escalations": [
            {
                "id": str(e.id),
                "type": e.escalation_type.value,
                "severity": e.severity.value,
                "title": e.title,
                "status": e.status,
            }
            for e in open_esc
        ],
    }
