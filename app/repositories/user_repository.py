from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create(
        self,
        *,
        email: str,
        cognito_id: str,
        role: UserRole = UserRole.user,
    ) -> User:

        user = User(
            email=email,
            cognito_id=cognito_id,
            role=role,
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._db.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_cognito_id(self, cognito_id: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.cognito_id == cognito_id)
        )
        return result.scalar_one_or_none()
