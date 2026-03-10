"""Testes do TransactionRepository."""

from datetime import UTC, date, datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.models.category import CategoryType
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


@pytest.fixture
def mock_db():
    db = MagicMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def category_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create(mock_db, user_id, category_id):
    """create() adiciona transação, commit e refresh."""
    repo = TransactionRepository(mock_db)
    mock_db.refresh.side_effect = lambda obj: obj

    result = await repo.create(
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("100.00"),
        type=CategoryType.expense,
        description="Almoço",
        transaction_date=date(2025, 3, 1),
    )

    mock_db.add.assert_called_once()
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once()
    assert result.amount == Decimal("100.00")
    assert result.type == CategoryType.expense


@pytest.mark.asyncio
async def test_get_by_id(mock_db, user_id, category_id):
    """get_by_id() retorna transação ou None."""
    repo = TransactionRepository(mock_db)
    tx = Transaction(
        id=uuid4(),
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("50"),
        type=CategoryType.income,
        description=None,
        transaction_date=date(2025, 3, 1),
        created_at=datetime.now(UTC),
    )
    mock_db.get.return_value = tx

    result = await repo.get_by_id(tx.id)

    mock_db.get.assert_awaited_once_with(Transaction, tx.id)
    assert result is tx


@pytest.mark.asyncio
async def test_get_by_id_not_found(mock_db):
    """get_by_id() retorna None quando não existe."""
    repo = TransactionRepository(mock_db)
    mock_db.get.return_value = None

    result = await repo.get_by_id(uuid4())

    assert result is None


@pytest.mark.asyncio
async def test_list_by_filters_no_filters(mock_db, user_id):
    """list_by_filters() sem filtros executa query e retorna lista."""
    repo = TransactionRepository(mock_db)
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    result = await repo.list_by_filters(user_id)

    assert result == []
    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_by_filters_with_month_year(mock_db, user_id, category_id):
    """list_by_filters() com month e year aplica filtros."""
    repo = TransactionRepository(mock_db)
    tx = Transaction(
        id=uuid4(),
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("10"),
        type=CategoryType.expense,
        description=None,
        transaction_date=date(2025, 3, 15),
        created_at=datetime.now(UTC),
    )
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [tx]
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    result = await repo.list_by_filters(user_id, month=3, year=2025)

    assert len(result) == 1
    assert result[0] is tx


@pytest.mark.asyncio
async def test_list_by_filters_with_type_and_category(mock_db, user_id, category_id):
    """list_by_filters() com type e category_id."""
    repo = TransactionRepository(mock_db)
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result = MagicMock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    await repo.list_by_filters(
        user_id, type=CategoryType.expense, category_id=category_id
    )

    mock_db.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_monthly_totals(mock_db, user_id):
    """get_monthly_totals() retorna (income, expense) do mês."""
    repo = TransactionRepository(mock_db)
    income_result = MagicMock()
    income_result.scalar.return_value = Decimal("1000.00")
    expense_result = MagicMock()
    expense_result.scalar.return_value = Decimal("300.00")
    mock_db.execute.side_effect = [income_result, expense_result]

    income, expense = await repo.get_monthly_totals(user_id, month=3, year=2025)

    assert income == Decimal("1000.00")
    assert expense == Decimal("300.00")
    assert mock_db.execute.await_count == 2


@pytest.mark.asyncio
async def test_get_monthly_totals_none_returns_zero(mock_db, user_id):
    """get_monthly_totals() usa 0 quando scalar retorna None."""
    repo = TransactionRepository(mock_db)
    mock_db.execute.side_effect = [
        MagicMock(scalar=MagicMock(return_value=None)),
        MagicMock(scalar=MagicMock(return_value=None)),
    ]

    income, expense = await repo.get_monthly_totals(user_id, month=1, year=2025)

    assert income == Decimal("0")
    assert expense == Decimal("0")


@pytest.mark.asyncio
async def test_update_partial(mock_db, user_id, category_id):
    """update() atualiza apenas campos passados."""
    repo = TransactionRepository(mock_db)
    tx = Transaction(
        id=uuid4(),
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("50"),
        type=CategoryType.expense,
        description="Old",
        transaction_date=date(2025, 3, 1),
        created_at=datetime.now(UTC),
    )
    new_cat_id = uuid4()

    result = await repo.update(
        tx,
        category_id=new_cat_id,
        amount=Decimal("75"),
        description="New",
    )

    assert tx.category_id == new_cat_id
    assert tx.amount == Decimal("75")
    assert tx.description == "New"
    mock_db.commit.assert_awaited_once()
    mock_db.refresh.assert_awaited_once_with(tx)
    assert result is tx


@pytest.mark.asyncio
async def test_update_transaction_date(mock_db, user_id, category_id):
    """update() atualiza transaction_date."""
    repo = TransactionRepository(mock_db)
    tx = Transaction(
        id=uuid4(),
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("10"),
        type=CategoryType.income,
        description=None,
        transaction_date=date(2025, 2, 1),
        created_at=datetime.now(UTC),
    )
    new_date = date(2025, 3, 10)

    result = await repo.update(tx, transaction_date=new_date)

    assert tx.transaction_date == new_date
    assert result is tx
