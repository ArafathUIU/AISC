"""AISC Memory Service — Unified 4-tier memory access."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aisc_utils import configure_logging, get_logger, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from memory_service.routes.memory import router as memory_router
from memory_service.stores.pg_store import pg_store
from memory_service.stores.redis_store import redis_store

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging("memory-service", settings.log_level)
    logger.info("memory_service_starting", port=8007)

    await redis_store.connect()
    await pg_store.create_tables()
    logger.info("memory_stores_connected")

    yield

    await redis_store.disconnect()
    logger.info("memory_service_stopping")


app = FastAPI(
    title="AISC Memory Service",
    description="Unified 4-tier memory access (Redis, PostgreSQL, Qdrant, Neo4j)",
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

app.include_router(memory_router, prefix="/api/v1/memory", tags=["memory"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "memory-service"}
