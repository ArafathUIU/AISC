"""Memory service — store and search routes."""

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from ..stores.pg_store import Artifact, Project, pg_store
from ..stores.redis_store import redis_store

router = APIRouter()


class StoreRequest(BaseModel):
    tier: str
    key: str
    data: dict


@router.post("/store")
async def store_data(body: StoreRequest) -> dict[str, str]:
    if body.tier == "short":
        if not redis_store.is_connected:
            return {"status": "redis_unavailable", "tier": "short"}
        await redis_store.set(body.key, body.data)
        return {"status": "stored", "tier": "short", "key": body.key}
    return {"status": "unsupported_tier", "tier": body.tier}


@router.get("/search")
async def search_memory(
    q: str | None = None,
    tier: str | None = None,
    limit: int = 20,
    project_id: str | None = None,
) -> dict[str, object]:
    results: list = []
    if tier == "short" and q and redis_store.is_connected:
        keys = await redis_store.scan_keys(f"*{q}*")
        results = [{"key": k, "tier": "short"} for k in keys[:limit]]
    return {"results": results, "total": len(results)}


@router.get("/context/{agent_id}")
async def get_agent_context(agent_id: str, task_type: str | None = None) -> dict:
    agent_state = None
    if redis_store.is_connected:
        agent_state = await redis_store.get(f"aisc:agent:{agent_id}:state")
    return {
        "agent_id": agent_id,
        "agent_state": agent_state,
        "task_type": task_type,
    }


@router.get("/project/{project_id}/history")
async def get_project_history(project_id: str) -> dict[str, object]:
    try:
        async with await pg_store.session() as session:
            result = await session.execute(select(Project).where(Project.id == project_id))
            project = result.scalar_one_or_none()
            if not project:
                return {"project": None, "artifacts": []}

            art_result = await session.execute(
                select(Artifact).where(Artifact.project_id == project_id)
            )
            artifacts = art_result.scalars().all()

            return {
                "project": {"id": str(project.id), "name": project.name, "status": project.status},
                "artifacts": [
                    {"id": str(a.id), "type": a.type, "name": a.name, "version": a.version}
                    for a in artifacts
                ],
            }
    except Exception:
        return {"project": None, "artifacts": [], "error": "database_unavailable"}
