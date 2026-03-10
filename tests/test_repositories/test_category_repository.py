from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.category import Category, CategoryType
from app.repositories.category_repository import CategoryRepository


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.delete = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def user_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    new_cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="Alimentação",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", new_cat.id) or obj

    result = await repo.create(
        user_id=user_id, name="Alimentação", type=CategoryType.expense
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()
    assert result.name == "Alimentação"
    assert result.type == CategoryType.expense


@pytest.mark.asyncio
async def test_get_by_id(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="X",
        type=CategoryType.income,
        created_at=datetime.now(UTC),
    )
    mock_db.get.return_value = cat

    result = await repo.get_by_id(cat.id)

    mock_db.get.assert_awaited_once_with(Category, cat.id)
    assert result is cat


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_db):
    repo = CategoryRepository(mock_db)
    mock_db.get.return_value = None

    result = await repo.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_user_and_name_and_type(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="Alimentação",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = cat
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_user_and_name_and_type(
        user_id=user_id, name="Alimentação", type=CategoryType.expense
    )

    assert result is cat
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_by_user_id(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cats = [
        Category(
            id=uuid4(),
            user_id=user_id,
            name="A",
            type=CategoryType.expense,
            created_at=datetime.now(UTC),
        ),
        Category(
            id=uuid4(),
            user_id=user_id,
            name="B",
            type=CategoryType.income,
            created_at=datetime.now(UTC),
        ),
    ]
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = cats
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    result = await repo.list_by_user_id(user_id)

    assert result == cats
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="X",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )

    await repo.delete(cat)

    mock_db.delete.assert_called_once_with(cat)
    mock_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_name_only(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="Old",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )

    result = await repo.update(cat, name="New")

    assert cat.name == "New"
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(cat)
    assert result is cat


@pytest.mark.asyncio
async def test_update_type_only(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="X",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )

    result = await repo.update(cat, type=CategoryType.income)

    assert cat.type == CategoryType.income
    mock_db.commit.assert_awaited_once()
    assert result is cat


@pytest.mark.asyncio
async def test_update_both(mock_db, user_id):
    repo = CategoryRepository(mock_db)
    cat = Category(
        id=uuid4(),
        user_id=user_id,
        name="A",
        type=CategoryType.expense,
        created_at=datetime.now(UTC),
    )

    result = await repo.update(cat, name="B", type=CategoryType.income)

    assert cat.name == "B"
    assert cat.type == CategoryType.income
    mock_db.commit.assert_awaited_once()
    assert result is cat
