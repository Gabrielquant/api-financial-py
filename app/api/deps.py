from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    decode_and_validate_cognito_token,
    get_token_from_authorization_header,
)
from app.db.session import get_db
from app.models.user import User
from app.repositories.user_repository import UserRepository

__all__ = ["get_db", "get_current_user"]


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    token = get_token_from_authorization_header(request)
    payload = await decode_and_validate_cognito_token(token)
    user = await UserRepository(db).get_by_cognito_id(payload.sub)
    if user is None:
        raise UnauthorizedError("User not found")
    return user
