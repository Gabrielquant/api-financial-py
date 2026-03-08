"""Testes do serviço de transações."""

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.category import Category, CategoryType
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionCreate, TransactionUpdate


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def user_id():
    return uuid4()


@pytest.fixture
def category_id():
    return uuid4()


@pytest.mark.asyncio
async def test_create_category_not_found_raises(mock_db, user_id, category_id):
    """create() levanta NotFoundError quando categoria não existe."""
    with patch("app.services.transaction_service.CategoryRepository") as MockCatRepo:
        mock_cat_repo = MockCatRepo.return_value
        mock_cat_repo.get_by_id = AsyncMock(return_value=None)
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        data = TransactionCreate(
            category_id=category_id,
            amount=Decimal("100"),
            type=CategoryType.expense,
            transaction_date=date(2025, 3, 1),
        )
        with pytest.raises(NotFoundError) as exc_info:
            await svc.create(user_id, data)
        assert "categoria" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_category_other_user_raises_forbidden(
    mock_db, user_id, category_id
):
    """create() levanta ForbiddenError quando categoria é de outro usuário."""
    other_id = uuid4()
    cat = Category(
        id=category_id, user_id=other_id, name="X", type=CategoryType.expense
    )
    with patch("app.services.transaction_service.CategoryRepository") as MockCatRepo:
        mock_cat_repo = MockCatRepo.return_value
        mock_cat_repo.get_by_id = AsyncMock(return_value=cat)
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        data = TransactionCreate(
            category_id=category_id,
            amount=Decimal("100"),
            type=CategoryType.expense,
            transaction_date=date(2025, 3, 1),
        )
        with pytest.raises(ForbiddenError):
            await svc.create(user_id, data)


@pytest.mark.asyncio
async def test_create_type_mismatch_raises_bad_request(mock_db, user_id, category_id):
    """create() levanta BadRequestError quando tipo da transação != tipo da categoria."""
    cat = Category(
        id=category_id, user_id=user_id, name="Despesa", type=CategoryType.expense
    )
    with patch("app.services.transaction_service.CategoryRepository") as MockCatRepo:
        mock_cat_repo = MockCatRepo.return_value
        mock_cat_repo.get_by_id = AsyncMock(return_value=cat)
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        data = TransactionCreate(
            category_id=category_id,
            amount=Decimal("100"),
            type=CategoryType.income,  # categoria é expense
            transaction_date=date(2025, 3, 1),
        )
        with pytest.raises(BadRequestError) as exc_info:
            await svc.create(user_id, data)
        assert "tipo" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_create_success(mock_db, user_id, category_id):
    """create() chama repositório e retorna transação."""
    cat = Category(
        id=category_id, user_id=user_id, name="Despesa", type=CategoryType.expense
    )
    txn = Transaction(
        id=uuid4(),
        user_id=user_id,
        category_id=category_id,
        amount=Decimal("100"),
        type=CategoryType.expense,
        description="Test",
        transaction_date=date(2025, 3, 1),
    )
    with (
        patch("app.services.transaction_service.CategoryRepository") as MockCatRepo,
        patch("app.services.transaction_service.TransactionRepository") as MockTxnRepo,
    ):
        mock_cat_repo = MockCatRepo.return_value
        mock_cat_repo.get_by_id = AsyncMock(return_value=cat)
        mock_txn_repo = MockTxnRepo.return_value
        mock_txn_repo.create = AsyncMock(return_value=txn)
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        data = TransactionCreate(
            category_id=category_id,
            amount=Decimal("100"),
            type=CategoryType.expense,
            description="Test",
            transaction_date=date(2025, 3, 1),
        )
        result = await svc.create(user_id, data)
        assert result.amount == Decimal("100")
        mock_txn_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_get_monthly_summary(mock_db, user_id):
    """get_monthly_summary() retorna totais e saving_rate."""
    with patch("app.services.transaction_service.TransactionRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_monthly_totals = AsyncMock(
            return_value=(Decimal("5000"), Decimal("3000"))
        )
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        result = await svc.get_monthly_summary(user_id, 3, 2025)
        assert result["month"] == 3
        assert result["year"] == 2025
        assert result["total_income"] == Decimal("5000")
        assert result["total_expense"] == Decimal("3000")
        assert result["balance"] == Decimal("2000")
        assert result["saving_rate"] == Decimal("0.4")


@pytest.mark.asyncio
async def test_update_not_found_raises(mock_db, user_id, category_id):
    """update() levanta NotFoundError quando transação não existe."""
    with patch("app.services.transaction_service.TransactionRepository") as MockRepo:
        mock_repo = MockRepo.return_value
        mock_repo.get_by_id = AsyncMock(return_value=None)
        from app.services.transaction_service import TransactionService

        svc = TransactionService(mock_db)
        with pytest.raises(NotFoundError):
            await svc.update(uuid4(), user_id, TransactionUpdate(amount=Decimal("200")))
