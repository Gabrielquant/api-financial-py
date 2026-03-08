"""Schemas de transação (TransactionCreate, TransactionResponse, MonthlySummary, etc.)."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.category import CategoryType


class TransactionCreate(BaseModel):
    """Payload para criar transação."""

    category_id: UUID
    amount: Decimal = Field(..., gt=0)
    type: CategoryType
    description: str | None = Field(None, max_length=500)
    transaction_date: date


class TransactionUpdate(BaseModel):
    """Payload para atualizar transação (PATCH)."""

    category_id: UUID | None = None
    amount: Decimal | None = Field(None, gt=0)
    type: CategoryType | None = None
    description: str | None = None
    transaction_date: date | None = None


class TransactionResponse(BaseModel):
    """Resposta de uma transação."""

    id: UUID
    user_id: UUID
    category_id: UUID
    amount: Decimal
    type: CategoryType
    description: str | None
    transaction_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    """Resposta de listagem de transações."""

    items: list[TransactionResponse]
    total: int


class MonthlySummaryResponse(BaseModel):
    """Resumo financeiro mensal."""

    month: int
    year: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    saving_rate: Decimal
