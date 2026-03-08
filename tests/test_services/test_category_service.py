"""Testes do serviço de categorias."""

from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.category import Category, CategoryType
from app.schemas.category import CategoryCreate, CategoryUpdate


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create_success(mock_db, user_id):
    """create() insere categoria quando nome/tipo não existem."""
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_user_and_name_and_type = AsyncMock(return_value=None)
        new_cat = Category(id=uuid4(), user_id=user_id, name="Alimentação", type=CategoryType.expense)
        mock_repo.create = AsyncMock(return_value=new_cat)
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        data = CategoryCreate(name="Alimentação", type=CategoryType.expense)
        result = await svc.create(user_id, data)
        assert result.name == "Alimentação"
        assert result.type == CategoryType.expense
        mock_repo.create.assert_called_once_with(user_id=user_id, name="Alimentação", type=CategoryType.expense)


@pytest.mark.asyncio
async def test_create_duplicate_name_type_raises_conflict(mock_db, user_id):
    """create() levanta ConflictError quando nome+tipo já existem."""
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_user_and_name_and_type = AsyncMock(return_value=MagicMock())
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        data = CategoryCreate(name="Alimentação", type=CategoryType.expense)
        with pytest.raises(ConflictError) as exc_info:
            await svc.create(user_id, data)
        assert "já existe" in exc_info.value.detail.lower() or "categoria" in exc_info.value.detail.lower()


def test_create_empty_name_rejected_by_schema():
    """CategoryCreate rejeita nome só com espaços (strip + min_length=1 no schema)."""
    from pydantic import ValidationError
    from app.schemas.category import CategoryCreate
    from app.models.category import CategoryType
    with pytest.raises(ValidationError):
        CategoryCreate(name="   ", type=CategoryType.expense)


@pytest.mark.asyncio
async def test_list_by_user(mock_db, user_id):
    """list_by_user() retorna lista do repositório."""
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        cats = [
            Category(id=uuid4(), user_id=user_id, name="A", type=CategoryType.income),
            Category(id=uuid4(), user_id=user_id, name="B", type=CategoryType.expense),
        ]
        mock_repo.list_by_user_id = AsyncMock(return_value=cats)
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        result = await svc.list_by_user(user_id)
        assert len(result) == 2
        mock_repo.list_by_user_id.assert_called_once_with(user_id)


@pytest.mark.asyncio
async def test_delete_not_found_raises(mock_db, user_id):
    """delete() levanta NotFoundError quando categoria não existe."""
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_id = AsyncMock(return_value=None)
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        with pytest.raises(NotFoundError):
            await svc.delete(uuid4(), user_id)


@pytest.mark.asyncio
async def test_delete_other_user_raises_forbidden(mock_db, user_id):
    """delete() levanta ForbiddenError quando categoria é de outro usuário."""
    other_id = uuid4()
    cat = Category(id=uuid4(), user_id=other_id, name="X", type=CategoryType.expense)
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_id = AsyncMock(return_value=cat)
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        with pytest.raises(ForbiddenError):
            await svc.delete(cat.id, user_id)


@pytest.mark.asyncio
async def test_update_success(mock_db, user_id):
    """update() atualiza nome e retorna categoria."""
    cat = Category(id=uuid4(), user_id=user_id, name="Old", type=CategoryType.expense)
    cat_updated = Category(id=cat.id, user_id=user_id, name="New", type=CategoryType.expense)
    with patch("app.services.category_service.CategoryRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_id = AsyncMock(return_value=cat)
        mock_repo.get_by_user_and_name_and_type = AsyncMock(return_value=None)
        mock_repo.update = AsyncMock(return_value=cat_updated)
        from app.services.category_service import CategoryService
        svc = CategoryService(mock_db)
        result = await svc.update(cat.id, user_id, CategoryUpdate(name="New"))
        assert result.name == "New"
        mock_repo.update.assert_called_once()
