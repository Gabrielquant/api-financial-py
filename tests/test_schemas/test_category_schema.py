"""Testes dos schemas de categoria (validators e model_config)."""

import uuid
from datetime import UTC, datetime

import pytest

from app.models.category import CategoryType
from app.schemas.category import (
    CategoryCreate,
    CategoryResponse,
    CategoryUpdate,
)


def test_category_create_strip_name_returns_stripped():
    """CategoryCreate strip_name retorna string sem espaços."""
    data = CategoryCreate(name="  Alimentação  ", type=CategoryType.expense)
    assert data.name == "Alimentação"


def test_category_create_strip_name_non_string_returns_unchanged():
    """CategoryCreate strip_name com valor não-string retorna o valor (linha 20)."""
    result = CategoryCreate.strip_name(123)
    assert result == 123


def test_category_update_strip_name_none_returns_none():
    """CategoryUpdate strip_name com None retorna None (linha 31)."""
    data = CategoryUpdate(name=None, type=CategoryType.income)
    assert data.name is None


def test_category_update_strip_name_string_returns_stripped():
    """CategoryUpdate strip_name com string retorna stripped (linha 32-33)."""
    data = CategoryUpdate(name="  Transporte  ", type=None)
    assert data.name == "Transporte"


def test_category_update_strip_name_non_string_returns_unchanged():
    """CategoryUpdate strip_name com valor não-string retorna o valor (linha 34)."""
    result = CategoryUpdate.strip_name(123)
    assert result == 123


def test_category_response_from_attributes():
    """CategoryResponse model_config from_attributes (linha 43)."""
    from app.models.category import Category

    cat = Category(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        name="Test",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )
    resp = CategoryResponse.model_validate(cat)
    assert resp.name == "Test"
    assert resp.type == CategoryType.expense
    assert resp.id == cat.id
