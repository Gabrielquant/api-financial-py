"""Schemas de transação (TransactionCreate, TransactionResponse, MonthlySummary, etc.)."""

from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.category import CategoryType

class TransactionBaseModel(BaseModel):
    category_id: UUID
    amount: Decimal = Field(..., gt=0)
    type: CategoryType
    description: Optional[str] = Field(None, max_length=500)
    transaction_date: date

class TransactionCreate(TransactionBaseModel):
    pass

class TransactionUpdate(TransactionBaseModel):
    category_id: Optional[UUID] 
    amount: Optional[Decimal] = Field(None, gt=0)
    type: Optional[CategoryType] 
    description: Optional[str] 
    transaction_date: Optional[date] 


class TransactionResponse(BaseModel):
    id: UUID
    user_id: UUID
    category_id: UUID
    amount: Decimal
    type: CategoryType
    description: Optional[str]
    transaction_date: date
    created_at: datetime

    model_config = {"from_attributes": True}


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int


class MonthlySummaryResponse(BaseModel):
    month: int
    year: int
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    saving_rate: Decimal
