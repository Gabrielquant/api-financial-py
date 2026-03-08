"""Fixtures compartilhadas para os testes."""

import uuid
from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.user import User, UserRole

_now = datetime.now(timezone.utc)


@pytest.fixture
def test_user_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def test_user(test_user_id: uuid.UUID) -> User:
    """Usuário fake para override de get_current_user nas rotas protegidas."""
    return User(
        id=test_user_id,
        email="test@example.com",
        cognito_id="cognito-sub-123",
        role=UserRole.user,
        created_at=_now,
        updated_at=_now,
    )


@pytest.fixture
def client_with_user(test_user: User):
    """TestClient com get_current_user override retornando test_user."""
    from app.api.deps import get_current_user

    async def override_get_current_user() -> User:
        return test_user

    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def client():
    """TestClient sem autenticação (para rotas públicas como auth e health)."""
    with TestClient(app) as c:
        yield c
