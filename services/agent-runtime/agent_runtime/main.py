"""AISC Agent Runtime — hosts and executes all AI agents."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from aisc_utils import configure_logging, get_logger, settings
from fastapi import FastAPI

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging("agent-runtime", settings.log_level)
    logger.info("agent_runtime_starting", port=8003)
    yield
    logger.info("agent_runtime_stopping")


app = FastAPI(
    title="AISC Agent Runtime",
    description="AI agent lifecycle management, LLM providers, and tool execution",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "agent-runtime"}


@app.get("/api/v1/agents")
async def list_agents() -> dict[str, Any]:
    from agent_runtime.agents.registry import agent_registry
    return {
        "agents": [
            {"name": a.name, "type": a.agent_type, "status": "idle"}
            for a in agent_registry.list()
        ],
    }
