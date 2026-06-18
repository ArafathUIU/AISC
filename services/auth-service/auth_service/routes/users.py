"""Auth service — user management routes."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_users() -> list:
    return []
