"""Repositório de transações."""

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import CategoryType
from app.models.transaction import Transaction


class TransactionRepository:
    """Acesso a dados de Transaction."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: UUID,
        category_id: UUID,
        amount: Decimal,
        type: CategoryType,
        description: str | None,
        transaction_date: date,
    ) -> Transaction:
        """Cria uma transação no banco."""
        transaction = Transaction(
            user_id=user_id,
            category_id=category_id,
            amount=amount,
            type=type,
            description=description,
            transaction_date=transaction_date,
        )
        self._db.add(transaction)
        await self._db.commit()
        await self._db.refresh(transaction)
        return transaction

    async def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        """Busca transação por id."""
        return await self._db.get(Transaction, transaction_id)

    async def list_by_filters(
        self,
        user_id: UUID,
        *,
        month: int | None = None,
        year: int | None = None,
        type: CategoryType | None = None,
        category_id: UUID | None = None,
    ) -> list[Transaction]:
        """Lista transações do usuário com filtros opcionais."""
        q = select(Transaction).where(Transaction.user_id == user_id)
        if month is not None:
            q = q.where(func.extract("month", Transaction.transaction_date) == month)
        if year is not None:
            q = q.where(func.extract("year", Transaction.transaction_date) == year)
        if type is not None:
            q = q.where(Transaction.type == type)
        if category_id is not None:
            q = q.where(Transaction.category_id == category_id)
        q = q.order_by(
            Transaction.transaction_date.desc(), Transaction.created_at.desc()
        )
        result = await self._db.execute(q)
        return list(result.scalars().all())

    async def get_monthly_totals(
        self,
        user_id: UUID,
        month: int,
        year: int,
    ) -> tuple[Decimal, Decimal]:
        """Retorna (total_income, total_expense) do mês/ano para o usuário."""
        income_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == CategoryType.income,
            func.extract("month", Transaction.transaction_date) == month,
            func.extract("year", Transaction.transaction_date) == year,
        )
        expense_q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user_id,
            Transaction.type == CategoryType.expense,
            func.extract("month", Transaction.transaction_date) == month,
            func.extract("year", Transaction.transaction_date) == year,
        )
        income_result = await self._db.execute(income_q)
        expense_result = await self._db.execute(expense_q)
        income = income_result.scalar() or Decimal("0")
        expense = expense_result.scalar() or Decimal("0")
        return (Decimal(income), Decimal(expense))

    async def update(
        self,
        transaction: Transaction,
        *,
        category_id: UUID | None = None,
        amount: Decimal | None = None,
        type: CategoryType | None = None,
        description: str | None = None,
        transaction_date: date | None = None,
    ) -> Transaction:
        """Atualiza transação."""
        if category_id is not None:
            transaction.category_id = category_id
        if amount is not None:
            transaction.amount = amount
        if type is not None:
            transaction.type = type
        if description is not None:
            transaction.description = description
        if transaction_date is not None:
            transaction.transaction_date = transaction_date
        await self._db.commit()
        await self._db.refresh(transaction)
        return transaction
