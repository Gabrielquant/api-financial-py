"""Testes das rotas de categorias (/categories)."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.category import Category, CategoryType


@pytest.fixture
def category_model(test_user):
    """Categoria fake retornada pelo service mock."""
    from datetime import datetime, timezone

    return Category(
        id=uuid.uuid4(),
        user_id=test_user.id,
        name="Alimentação",
        type=CategoryType.expense,
        created_at=datetime.now(timezone.utc),
    )


def test_create_category_success(client_with_user, test_user, category_model):
    """POST /categories retorna 201 e categoria quando o service cria."""
    with patch("app.api.routers.categories.CategoryService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create = AsyncMock(return_value=category_model)
        resp = client_with_user.post(
            "/categories",
            json={"name": "Alimentação", "type": "expense"},
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Alimentação"
    assert data["type"] == "expense"
    assert "id" in data


def test_create_category_validation(client_with_user):
    """POST /categories com nome vazio retorna 422."""
    resp = client_with_user.post(
        "/categories",
        json={"name": "", "type": "expense"},
    )
    assert resp.status_code == 422


def test_list_categories_success(client_with_user, test_user, category_model):
    """GET /categories retorna 200 e lista de categorias."""
    with patch("app.api.routers.categories.CategoryService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_by_user = AsyncMock(return_value=[category_model])
        resp = client_with_user.get("/categories")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["name"] == "Alimentação"


def test_list_categories_empty(client_with_user):
    """GET /categories retorna 200 com lista vazia."""
    with patch("app.api.routers.categories.CategoryService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_by_user = AsyncMock(return_value=[])
        resp = client_with_user.get("/categories")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0
    assert resp.json()["items"] == []


def test_update_category_success(client_with_user, category_model):
    """PATCH /categories/:id retorna 200 e categoria atualizada."""
    category_model.name = "Alimentação Atualizada"
    with patch("app.api.routers.categories.CategoryService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.update = AsyncMock(return_value=category_model)
        resp = client_with_user.patch(
            f"/categories/{category_model.id}",
            json={"name": "Alimentação Atualizada"},
        )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Alimentação Atualizada"


def test_delete_category_success(client_with_user, category_model):
    """DELETE /categories/:id retorna 204."""
    with patch("app.api.routers.categories.CategoryService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.delete = AsyncMock(return_value=None)
        resp = client_with_user.delete(f"/categories/{category_model.id}")
    assert resp.status_code == 204


def test_categories_require_auth(client: TestClient):
    """Rotas de categorias sem token retornam 401."""
    resp = client.get("/categories")
    assert resp.status_code == 401
