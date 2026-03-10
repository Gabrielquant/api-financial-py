"""Testes do UserRepository."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.mark.asyncio
async def test_create(mock_db):
    """create() adiciona usuário, commit e refresh."""
    repo = UserRepository(mock_db)
    _now = datetime.now(UTC)
    mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", uuid4()) or obj

    result = await repo.create(
        email="user@example.com",
        cognito_id="cognito-sub-123",
        role=UserRole.user,
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()
    assert result.email == "user@example.com"
    assert result.cognito_id == "cognito-sub-123"
    assert result.role == UserRole.user


@pytest.mark.asyncio
async def test_create_admin(mock_db):
    """create() com role=admin."""
    repo = UserRepository(mock_db)
    mock_db.refresh.side_effect = lambda obj: obj

    result = await repo.create(
        email="admin@example.com",
        cognito_id="cognito-admin",
        role=UserRole.admin,
    )

    assert result.role == UserRole.admin


@pytest.mark.asyncio
async def test_get_by_id(mock_db):
    """get_by_id() retorna usuário ou None."""
    repo = UserRepository(mock_db)
    user = User(
        id=uuid4(),
        email="u@e.com",
        cognito_id="sub-1",
        role=UserRole.user,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mock_db.get.return_value = user

    result = await repo.get_by_id(user.id)

    mock_db.get.assert_awaited_once_with(User, user.id)
    assert result is user


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_db):
    """get_by_id() retorna None quando não existe."""
    repo = UserRepository(mock_db)
    mock_db.get.return_value = None

    result = await repo.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_get_by_email(mock_db):
    """get_by_email() retorna usuário ou None."""
    repo = UserRepository(mock_db)
    user = User(
        id=uuid4(),
        email="u@e.com",
        cognito_id="sub-1",
        role=UserRole.user,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_email("u@e.com")

    assert result is user
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_email_not_found(mock_db):
    """get_by_email() retorna None quando não existe."""
    repo = UserRepository(mock_db)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_email("unknown@e.com")

    assert result is None


@pytest.mark.asyncio
async def test_get_by_cognito_id(mock_db):
    """get_by_cognito_id() retorna usuário ou None."""
    repo = UserRepository(mock_db)
    user = User(
        id=uuid4(),
        email="u@e.com",
        cognito_id="cognito-sub-xyz",
        role=UserRole.user,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = user
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_cognito_id("cognito-sub-xyz")

    assert result is user
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_by_cognito_id_not_found(mock_db):
    """get_by_cognito_id() retorna None quando não existe."""
    repo = UserRepository(mock_db)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result

    result = await repo.get_by_cognito_id("unknown-sub")

    assert result is None
