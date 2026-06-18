"""AISC Auth Service — FastAPI application."""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from aisc_utils import configure_logging, get_logger, settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from auth_service.middleware.auth import JWTAuthMiddleware
from auth_service.routes import auth, users

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    configure_logging("auth-service", settings.log_level)
    logger.info("auth_service_starting", port=8001)
    yield
    logger.info("auth_service_stopping")


app = FastAPI(
    title="AISC Auth Service",
    description="Authentication, authorization, and user management",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(JWTAuthMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "auth-service"}
