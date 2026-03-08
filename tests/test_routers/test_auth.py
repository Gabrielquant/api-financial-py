"""Testes das rotas de autenticação (/auth)."""

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.schemas.auth import TokenResponse


def test_register_success(client: TestClient):
    """POST /auth/register retorna 201 e mensagem quando o serviço registra com sucesso."""
    with patch("app.api.routers.auth.auth_service.register", new_callable=AsyncMock) as mock_register:
        mock_register.return_value = {"message": "User registered. Email verified. You can sign in."}
        resp = client.post(
            "/auth/register",
            json={"email": "new@example.com", "password": "senha1234"},
        )
    assert resp.status_code == 201
    assert resp.json()["message"] == "User registered. Email verified. You can sign in."
    mock_register.assert_called_once()


def test_register_validation(client: TestClient):
    """POST /auth/register com senha curta retorna 422."""
    resp = client.post(
        "/auth/register",
        json={"email": "new@example.com", "password": "short"},
    )
    assert resp.status_code == 422


def test_login_success(client: TestClient):
    """POST /auth/login retorna 200 e tokens quando credenciais são válidas."""
    with patch("app.api.routers.auth.auth_service.login", new_callable=AsyncMock) as mock_login:
        mock_login.return_value = TokenResponse(
            access_token="access",
            refresh_token="refresh",
            token_type="Bearer",
            expires_in=3600,
        )
        resp = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "senha123"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "access"
    assert data["refresh_token"] == "refresh"
    assert data["token_type"] == "Bearer"
    assert data["expires_in"] == 3600


def test_login_unauthorized(client: TestClient):
    """POST /auth/login retorna 401 quando o serviço levanta UnauthorizedError."""
    from app.core.exceptions import UnauthorizedError
    with patch("app.api.routers.auth.auth_service.login", new_callable=AsyncMock) as mock_login:
        mock_login.side_effect = UnauthorizedError("Credentials are invalid")
        resp = client.post(
            "/auth/login",
            json={"email": "user@example.com", "password": "wrong"},
        )
    assert resp.status_code == 401
    assert "detail" in resp.json()


def test_refresh_success(client: TestClient):
    """POST /auth/refresh retorna 200 e novos tokens."""
    with patch("app.api.routers.auth.auth_service.refresh", new_callable=AsyncMock) as mock_refresh:
        mock_refresh.return_value = TokenResponse(
            access_token="new_access",
            refresh_token="new_refresh",
            token_type="Bearer",
            expires_in=3600,
        )
        resp = client.post(
            "/auth/refresh",
            json={"email": "user@example.com", "refresh_token": "old_refresh"},
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["access_token"] == "new_access"


def test_me_returns_current_user(client_with_user, test_user):
    """GET /auth/me retorna o usuário autenticado (via override)."""
    resp = client_with_user.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == test_user.email
    assert str(data["id"]) == str(test_user.id)
