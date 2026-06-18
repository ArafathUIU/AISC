"""AISC Orchestrator Service — CEO-level project coordination."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aisc_utils import configure_logging, get_logger, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.orchestrator import router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging("orchestrator-service", settings.log_level)
    logger.info("orchestrator_starting", port=8002)
    yield
    logger.info("orchestrator_stopping")


app = FastAPI(
    title="AISC Orchestrator Service",
    description="CEO-level coordination: workflow engine, agent scheduling, dependency resolution",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api/v1", tags=["orchestrator"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "orchestrator-service"}
