"""AISC Debate Service — FastAPI app."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routes.debate import router as debate_router

app = FastAPI(
    title="AISC Debate Service",
    description="Multi-agent consensus and artifact improvement",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(debate_router, prefix="/api/v1/debates", tags=["debates"])


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "healthy", "service": "debate-service"}
