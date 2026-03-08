"""Rotas de transações."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.category import CategoryType
from app.models.user import User
from app.schemas.transaction import (
    MonthlySummaryResponse,
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdate,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", status_code=201, response_model=TransactionResponse)
async def create_transaction(
    body: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    """Cria transação (receita ou despesa) do usuário autenticado."""
    transaction = await TransactionService(db).create(current_user.id, body)
    return TransactionResponse.model_validate(transaction)


@router.get("", response_model=TransactionListResponse)
async def list_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    month: int | None = Query(None, ge=1, le=12),
    year: int | None = Query(None, ge=1900, le=2100),
    transaction_type: CategoryType | None = Query(None, alias="type"),
    category_id: UUID | None = None,
) -> TransactionListResponse:
    """Lista transações do usuário autenticado com filtros opcionais."""
    items = await TransactionService(db).list_by_user(
        current_user.id,
        month=month,
        year=year,
        type=transaction_type,
        category_id=category_id,
    )
    return TransactionListResponse(
        items=[TransactionResponse.model_validate(t) for t in items],
        total=len(items),
    )


@router.get("/monthly-summary", response_model=MonthlySummaryResponse)
async def get_monthly_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=1900, le=2100),
) -> MonthlySummaryResponse:
    """Retorna resumo financeiro mensal do usuário autenticado."""
    summary = await TransactionService(db).get_monthly_summary(current_user.id, month, year)
    return MonthlySummaryResponse(**summary)


@router.patch("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    body: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    """Atualiza transação do usuário autenticado."""
    transaction = await TransactionService(db).update(transaction_id, current_user.id, body)
    return TransactionResponse.model_validate(transaction)
