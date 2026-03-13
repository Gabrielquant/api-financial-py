from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request

from app.core.exceptions import UnauthorizedError
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_get_current_user_success():
    from app.api.deps import get_current_user

    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid-token"}
    mock_db = MagicMock()

    with (
        patch(
            "app.api.deps.get_token_from_authorization_header",
            return_value="valid-token",
        ),
        patch(
            "app.api.deps.decode_and_validate_cognito_token",
            new_callable=AsyncMock,
            return_value=MagicMock(sub="cognito-sub-123"),
        ),
        patch("app.api.deps.UserRepository") as MockUserRepo,
    ):
        mock_repo = MockUserRepo.return_value
        mock_user = User(
            id=MagicMock(),
            email="u@e.com",
            cognito_id="cognito-sub-123",
            role=UserRole.user,
            created_at=MagicMock(),
            updated_at=MagicMock(),
        )
        mock_repo.get_by_cognito_id = AsyncMock(return_value=mock_user)

        result = await get_current_user(request, mock_db)
        assert result is mock_user
        mock_repo.get_by_cognito_id.assert_called_once_with("cognito-sub-123")


@pytest.mark.asyncio
async def test_get_current_user_not_found_raises_unauthorized():
    from app.api.deps import get_current_user

    request = MagicMock(spec=Request)
    request.headers = {"Authorization": "Bearer valid-token"}
    mock_db = MagicMock()

    with (
        patch(
            "app.api.deps.get_token_from_authorization_header",
            return_value="valid-token",
        ),
        patch(
            "app.api.deps.decode_and_validate_cognito_token",
            new_callable=AsyncMock,
            return_value=MagicMock(sub="cognito-sub-unknown"),
        ),
        patch("app.api.deps.UserRepository") as MockUserRepo,
    ):
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_cognito_id = AsyncMock(return_value=None)

        with pytest.raises(UnauthorizedError) as exc_info:
            await get_current_user(request, mock_db)
        assert "not found" in exc_info.value.detail.lower()
