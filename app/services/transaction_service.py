from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.models.category import CategoryType
from app.repositories.category_repository import CategoryRepository
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionCreate, TransactionUpdate


class TransactionService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = TransactionRepository(db)
        self._category_repo = CategoryRepository(db)

    async def create(self, user_id: UUID, data: TransactionCreate):

        category = await self._category_repo.get_by_id(data.category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        if category.user_id != user_id:
            raise ForbiddenError("Você não pode usar uma categoria de outro usuário.")
        if data.type != category.type:
            raise BadRequestError(
                "O tipo da transação deve ser igual ao tipo da categoria."
            )
        return await self._repo.create(
            user_id=user_id,
            category_id=data.category_id,
            amount=data.amount,
            type=data.type,
            description=data.description,
            transaction_date=data.transaction_date,
        )

    async def list_by_user(
        self,
        user_id: UUID,
        *,
        month: int | None = None,
        year: int | None = None,
        type: CategoryType | None = None,
        category_id: UUID | None = None,
    ):

        return await self._repo.list_by_filters(
            user_id,
            month=month,
            year=year,
            type=type,
            category_id=category_id,
        )

    async def get_monthly_summary(self, user_id: UUID, month: int, year: int) -> dict:

        total_income, total_expense = await self._repo.get_monthly_totals(
            user_id, month, year
        )
        balance = total_income - total_expense
        if total_income > 0:
            saving_rate = balance / total_income
        else:
            saving_rate = Decimal("0")
        return {
            "month": month,
            "year": year,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance,
            "saving_rate": saving_rate,
        }

    async def get_by_id(self, transaction_id: UUID, user_id: UUID):

        transaction = await self._repo.get_by_id(transaction_id)
        if transaction is None or transaction.user_id != user_id:
            return None
        return transaction

    async def update(
        self, transaction_id: UUID, user_id: UUID, data: TransactionUpdate
    ):

        transaction = await self._repo.get_by_id(transaction_id)
        if transaction is None:
            raise NotFoundError("Transação não encontrada.")
        if transaction.user_id != user_id:
            raise ForbiddenError(
                "Você não pode alterar uma transação de outro usuário."
            )
        category_id = (
            data.category_id
            if data.category_id is not None
            else transaction.category_id
        )
        category = await self._category_repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        if category.user_id != user_id:
            raise ForbiddenError("Você não pode usar uma categoria de outro usuário.")
        new_type = data.type if data.type is not None else transaction.type
        if new_type != category.type:
            raise BadRequestError(
                "O tipo da transação deve ser igual ao tipo da categoria."
            )
        return await self._repo.update(
            transaction,
            category_id=data.category_id if data.category_id is not None else None,
            amount=data.amount,
            type=data.type,
            description=data.description,
            transaction_date=data.transaction_date,
        )
