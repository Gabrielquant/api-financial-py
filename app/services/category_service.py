from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.category import Category
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryCreate, CategoryUpdate


class CategoryService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._repo = CategoryRepository(db)

    def _normalize_name(self, name: str) -> str:
        return name.strip() if name else ""

    async def create(self, user_id: UUID, data: CategoryCreate) -> Category:

        name = self._normalize_name(data.name)
        if not name:
            raise ConflictError("Nome da categoria não pode ser vazio.")
        existing = await self._repo.get_by_user_and_name_and_type(
            user_id, name, data.type
        )
        if existing:
            raise ConflictError("Categoria já existe para este usuário e tipo.")
        return await self._repo.create(user_id=user_id, name=name, type=data.type)

    async def list_by_user(self, user_id: UUID) -> list[Category]:

        return await self._repo.list_by_user_id(user_id)

    async def get_by_id(self, category_id: UUID, user_id: UUID) -> Category | None:

        category = await self._repo.get_by_id(category_id)
        if category is None or category.user_id != user_id:
            return None
        return category

    async def delete(self, category_id: UUID, user_id: UUID) -> None:

        category = await self._repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        if category.user_id != user_id:
            raise ForbiddenError(
                "Você não pode deletar uma categoria de outro usuário."
            )
        await self._repo.delete(category)

    async def update(
        self,
        category_id: UUID,
        user_id: UUID,
        data: CategoryUpdate,
    ) -> Category:

        category = await self._repo.get_by_id(category_id)
        if category is None:
            raise NotFoundError("Categoria não encontrada.")
        if category.user_id != user_id:
            raise ForbiddenError(
                "Você não pode alterar uma categoria de outro usuário."
            )
        name = self._normalize_name(data.name) if data.name is not None else None
        if name is not None and not name:
            raise ConflictError("Nome da categoria não pode ser vazio.")
        new_type = data.type if data.type is not None else None
        if name is not None or new_type is not None:
            final_name = name if name is not None else category.name
            final_type = new_type if new_type is not None else category.type
            other = await self._repo.get_by_user_and_name_and_type(
                user_id, final_name, final_type
            )
            if other is not None and other.id != category_id:
                raise ConflictError("Categoria já existe para este usuário e tipo.")
            category = await self._repo.update(
                category,
                name=name if name is not None else category.name,
                type=new_type if new_type is not None else category.type,
            )
        return category
