"""Testes das rotas de transações (/transactions)."""

from datetime import date
from decimal import Decimal
from uuid import uuid4

from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.category import CategoryType
from app.models.transaction import Transaction


@pytest.fixture
def category_id(test_user):
    return uuid4()


@pytest.fixture
def transaction_model(test_user, category_id):
    """Transação fake retornada pelo service mock."""
    from datetime import datetime, timezone

    return Transaction(
        id=uuid4(),
        user_id=test_user.id,
        category_id=category_id,
        amount=Decimal("150.00"),
        type=CategoryType.expense,
        description="Supermercado",
        transaction_date=date(2025, 3, 1),
        created_at=datetime.now(timezone.utc),
    )


def test_create_transaction_success(
    client_with_user, test_user, category_id, transaction_model
):
    """POST /transactions retorna 201 e transação quando o service cria."""
    with patch("app.api.routers.transactions.TransactionService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.create = AsyncMock(return_value=transaction_model)
        resp = client_with_user.post(
            "/transactions",
            json={
                "category_id": str(category_id),
                "amount": 150.00,
                "type": "expense",
                "description": "Supermercado",
                "transaction_date": "2025-03-01",
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert float(data["amount"]) == 150.0
    assert data["type"] == "expense"
    assert data["description"] == "Supermercado"


def test_create_transaction_validation(client_with_user, category_id):
    """POST /transactions com amount <= 0 retorna 422."""
    resp = client_with_user.post(
        "/transactions",
        json={
            "category_id": str(category_id),
            "amount": 0,
            "type": "expense",
            "transaction_date": "2025-03-01",
        },
    )
    assert resp.status_code == 422


def test_list_transactions_success(client_with_user, transaction_model):
    """GET /transactions retorna 200 e lista de transações."""
    with patch("app.api.routers.transactions.TransactionService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_by_user = AsyncMock(return_value=[transaction_model])
        resp = client_with_user.get("/transactions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert float(data["items"][0]["amount"]) == 150.0


def test_list_transactions_with_filters(client_with_user):
    """GET /transactions?month=3&year=2025 retorna 200."""
    with patch("app.api.routers.transactions.TransactionService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.list_by_user = AsyncMock(return_value=[])
        resp = client_with_user.get("/transactions?month=3&year=2025")
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


def test_monthly_summary_success(client_with_user):
    """GET /transactions/monthly-summary retorna 200 e resumo."""
    with patch("app.api.routers.transactions.TransactionService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.get_monthly_summary = AsyncMock(
            return_value={
                "month": 3,
                "year": 2025,
                "total_income": Decimal("5000"),
                "total_expense": Decimal("3000"),
                "balance": Decimal("2000"),
                "saving_rate": Decimal("0.4"),
            }
        )
        resp = client_with_user.get("/transactions/monthly-summary?month=3&year=2025")
    assert resp.status_code == 200
    data = resp.json()
    assert data["month"] == 3
    assert data["year"] == 2025
    assert float(data["total_income"]) == 5000.0
    assert float(data["total_expense"]) == 3000.0
    assert float(data["balance"]) == 2000.0


def test_update_transaction_success(client_with_user, transaction_model, category_id):
    """PATCH /transactions/:id retorna 200 e transação atualizada."""
    transaction_model.amount = Decimal("200.00")
    with patch("app.api.routers.transactions.TransactionService") as MockService:
        mock_instance = MockService.return_value
        mock_instance.update = AsyncMock(return_value=transaction_model)
        resp = client_with_user.patch(
            f"/transactions/{transaction_model.id}",
            json={"amount": 200.00},
        )
    assert resp.status_code == 200
    assert float(resp.json()["amount"]) == 200.0


def test_transactions_require_auth(client: TestClient):
    """Rotas de transações sem token retornam 401."""
    resp = client.get("/transactions")
    assert resp.status_code == 401
