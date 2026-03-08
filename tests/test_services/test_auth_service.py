"""Testes do serviço de autenticação."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.exceptions import ConflictError, UnauthorizedError
from app.schemas.auth import TokenResponse


@pytest.mark.asyncio
async def test_register_success():
    """register() cria usuário no Cognito e no banco quando não existe."""
    with (
        patch(
            "app.services.auth_service._run_cognito_sign_up", new_callable=AsyncMock
        ) as mock_sign_up,
        patch(
            "app.services.auth_service._run_cognito_confirm_and_verify",
            new_callable=AsyncMock,
        ) as mock_confirm,
        patch("app.services.auth_service.UserRepository") as MockUserRepo,
    ):
        mock_sign_up.return_value = "cognito-sub-123"
        mock_db = MagicMock()
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_cognito_id = AsyncMock(return_value=None)
        mock_repo.create = AsyncMock()

        from app.services import auth_service

        result = await auth_service.register(
            email="new@example.com",
            password="senha12345",
            db=mock_db,
        )
        assert result["message"] == "User registered. Email verified. You can sign in."
        mock_sign_up.assert_called_once()
        mock_confirm.assert_called_once()
        mock_repo.create.assert_called_once_with(
            email="new@example.com", cognito_id="cognito-sub-123"
        )


@pytest.mark.asyncio
async def test_register_username_exists_raises_conflict():
    """register() levanta ConflictError quando Cognito retorna UsernameExistsException."""
    err = ClientError(
        {"Error": {"Code": "UsernameExistsException", "Message": "Exists"}}, "SignUp"
    )
    with patch(
        "app.services.auth_service._run_cognito_sign_up",
        new_callable=AsyncMock,
        side_effect=err,
    ):
        from app.services import auth_service

        mock_db = MagicMock()
        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register(
                email="existing@example.com",
                password="senha12345",
                db=mock_db,
            )
        assert (
            "already registered" in exc_info.value.detail.lower()
            or "exists" in str(exc_info.value.detail).lower()
        )


@pytest.mark.asyncio
async def test_login_user_not_in_db_raises_unauthorized():
    """login() levanta UnauthorizedError quando usuário não existe no banco."""
    mock_db = MagicMock()
    with patch("app.services.auth_service.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_email = AsyncMock(return_value=None)
        from app.services import auth_service

        with pytest.raises(UnauthorizedError) as exc_info:
            await auth_service.login(
                email="unknown@example.com",
                password="senha123",
                db=mock_db,
            )
        assert (
            "invalid" in exc_info.value.detail.lower()
            or "credentials" in exc_info.value.detail.lower()
        )


@pytest.mark.asyncio
async def test_login_success_returns_tokens():
    """login() retorna TokenResponse quando Cognito autentica."""
    mock_db = MagicMock()
    with (
        patch("app.services.auth_service.UserRepository") as MockUserRepo,
        patch(
            "app.services.auth_service._run_cognito_initiate_auth",
            new_callable=AsyncMock,
        ) as mock_auth,
    ):
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_email = AsyncMock(return_value=MagicMock())  # user exists
        mock_auth.return_value = {
            "AuthenticationResult": {
                "AccessToken": "access",
                "RefreshToken": "refresh",
                "TokenType": "Bearer",
                "ExpiresIn": 3600,
            }
        }
        from app.services import auth_service

        result = await auth_service.login(
            email="user@example.com",
            password="senha123",
            db=mock_db,
        )
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access"
        assert result.refresh_token == "refresh"
        assert result.expires_in == 3600


@pytest.mark.asyncio
async def test_refresh_user_not_found_raises_unauthorized():
    """refresh() levanta UnauthorizedError quando usuário não existe no banco."""
    mock_db = MagicMock()
    with patch("app.services.auth_service.UserRepository") as MockUserRepo:
        mock_repo = MockUserRepo.return_value
        mock_repo.get_by_email = AsyncMock(return_value=None)
        from app.services import auth_service

        with pytest.raises(UnauthorizedError):
            await auth_service.refresh(
                refresh_token="some-refresh",
                email="unknown@example.com",
                db=mock_db,
            )
