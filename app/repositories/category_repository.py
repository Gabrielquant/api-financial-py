"""Repositório de categorias."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category, CategoryType


class CategoryRepository:
    """Acesso a dados de Category."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        user_id: UUID,
        name: str,
        type: CategoryType,
    ) -> Category:
        category = Category(
            user_id=user_id,
            name=name,
            type=type,
        )
        self._db.add(category)
        await self._db.commit()
        await self._db.refresh(category)
        return category

    async def get_by_id(self, category_id: UUID) -> Category | None:
        return await self._db.get(Category, category_id)

    async def get_by_user_and_name_and_type(
        self,
        user_id: UUID,
        name: str,
        type: CategoryType,
    ) -> Category | None:
        result = await self._db.execute(
            select(Category).where(
                Category.user_id == user_id,
                Category.name == name,
                Category.type == type,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_user_id(self, user_id: UUID) -> list[Category]:
        result = await self._db.execute(
            select(Category).where(Category.user_id == user_id).order_by(Category.name)
        )
        return list(result.scalars().all())

    async def delete(self, category: Category) -> None:
        await self._db.delete(category)
        await self._db.commit()

    async def update(
        self,
        category: Category,
        *,
        name: str | None = None,
        type: CategoryType | None = None,
    ) -> Category:
        if name is not None:
            category.name = name
        if type is not None:
            category.type = type
        await self._db.commit()
        await self._db.refresh(category)
        return category
