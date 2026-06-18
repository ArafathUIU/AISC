"""Auth service — JWT middleware for route protection."""

from typing import Any

import jwt
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

JWT_SECRET = "dev-secret-change-in-production"
JWT_ALGORITHM = "HS256"

PUBLIC_PATHS: set[str] = {
    "/api/v1/auth/register",
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/health",
    "/metrics",
    "/favicon.ico",
    "/docs",
    "/openapi.json",
}


class JWTAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Any) -> Any:
        path = request.url.path.rstrip("/")
        if path in PUBLIC_PATHS or path.startswith("/docs") or path.startswith("/openapi"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(status_code=401, content={"detail": "Missing authorization header"})

        token = auth_header.removeprefix("Bearer ")
        try:
            decoded: dict[str, Any] = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.state.user_id = decoded["sub"]
            request.state.user_role = decoded.get("role", "viewer")
        except jwt.ExpiredSignatureError:
            return JSONResponse(status_code=401, content={"detail": "Token expired"})
        except jwt.InvalidTokenError:
            return JSONResponse(status_code=401, content={"detail": "Invalid token"})

        return await call_next(request)


def require_permission(permission: str):  # type: ignore[no-untyped-def]
    async def dependency(request: Request) -> str:
        user_role: str = getattr(request.state, "user_role", "viewer")

        role_permissions: dict[str, set[str]] = {
            "admin": {
                "projects:create", "projects:read", "projects:update", "projects:delete",
                "projects:manage_members", "artifacts:create", "artifacts:read",
                "artifacts:update", "artifacts:approve", "deployments:execute",
                "deployments:rollback", "deployments:approve", "agents:manage",
                "config:manage", "audit:read",
            },
            "developer": {
                "projects:create", "projects:read", "projects:update",
                "artifacts:create", "artifacts:read", "artifacts:update",
                "deployments:execute",
            },
            "viewer": {"projects:read", "artifacts:read"},
        }

        allowed = role_permissions.get(user_role, set())
        if permission not in allowed:
            raise HTTPException(status_code=403, detail=f"Missing permission: {permission}")
        return user_role

    return dependency
