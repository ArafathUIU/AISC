"""AISC RAG Service — retrieval-augmented generation pipeline."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aisc_utils import configure_logging, get_logger, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.rag import router as rag_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging("rag-service", settings.log_level)
    logger.info("rag_service_starting", port=8006)
    yield
    logger.info("rag_service_stopping")


app = FastAPI(
    title="AISC RAG Service",
    description="Retrieval-Augmented Generation pipeline",
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

app.include_router(rag_router, prefix="/api/v1/rag", tags=["rag"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "rag-service"}
