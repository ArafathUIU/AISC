"""Auth service — user management routes."""

from typing import Any

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_users() -> list[dict[str, Any]]:
    return []
