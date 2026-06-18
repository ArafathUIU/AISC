"""Auth service unit tests."""

import pytest
from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestHealth:
    def test_health_returns_200(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "auth-service"


class TestAuthRoutes:
    def test_register_validation(self) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "not-an-email", "password": "short", "display_name": ""},
        )
        assert response.status_code == 422

    def test_login_missing_credentials(self) -> None:
        response = client.post("/api/v1/auth/login", json={})
        assert response.status_code == 422

    def test_register_valid_request(self) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "securepassword123",
                "display_name": "Test User",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


class TestUserManagement:
    def test_list_users_requires_auth(self) -> None:
        response = client.get("/api/v1/users/")
        assert response.status_code == 401


class TestPublicPaths:
    def test_health_is_public(self) -> None:
        response = client.get("/health")
        assert response.status_code == 200

    def test_auth_register_is_public(self) -> None:
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "a@b.com", "password": "12345678", "display_name": "X"},
        )
        assert response.status_code == 201


class TestProtectedPaths:
    def test_unauthenticated_request(self) -> None:
        response = client.get("/api/v1/users/")
        assert response.status_code == 401
