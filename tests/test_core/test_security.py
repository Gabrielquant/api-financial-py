"""Testes do módulo core.security."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import UnauthorizedError


def test_cognito_secret_hash():
    """cognito_secret_hash retorna base64 do HMAC-SHA256."""
    from app.core.security import cognito_secret_hash

    result = cognito_secret_hash("user", "client-id", "client-secret")
    assert isinstance(result, str)
    assert len(result) > 0
    # resultado é base64
    import base64

    decoded = base64.b64decode(result)
    assert len(decoded) == 32


def test_get_token_from_authorization_header_success():
    """get_token_from_authorization_header retorna o token quando Bearer é válido."""
    from app.core.security import get_token_from_authorization_header

    request = MagicMock()
    request.headers = {"Authorization": "Bearer my-jwt-token"}
    assert get_token_from_authorization_header(request) == "my-jwt-token"


def test_get_token_from_authorization_header_missing_raises():
    """get_token_from_authorization_header levanta quando Authorization está ausente."""
    from app.core.security import get_token_from_authorization_header

    request = MagicMock()
    request.headers = {}
    with pytest.raises(UnauthorizedError) as exc_info:
        get_token_from_authorization_header(request)
    assert (
        "Missing" in exc_info.value.detail or "invalid" in exc_info.value.detail.lower()
    )


def test_get_token_from_authorization_header_not_bearer_raises():
    """get_token_from_authorization_header levanta quando não é Bearer."""
    from app.core.security import get_token_from_authorization_header

    request = MagicMock()
    request.headers = {"Authorization": "Basic xyz"}
    with pytest.raises(UnauthorizedError):
        get_token_from_authorization_header(request)


def test_get_token_from_authorization_header_empty_token_raises():
    """get_token_from_authorization_header levanta quando token após Bearer está vazio."""
    from app.core.security import get_token_from_authorization_header

    request = MagicMock()
    request.headers = {"Authorization": "Bearer   "}
    with pytest.raises(UnauthorizedError):
        get_token_from_authorization_header(request)


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_success():
    """decode_and_validate_cognito_token retorna payload quando JWKS e token são válidos."""
    from app.core.security import decode_and_validate_cognito_token

    fake_jwks = {
        "keys": [
            {
                "kid": "kid1",
                "kty": "RSA",
                "n": "x",
                "e": "AQAB",
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = fake_jwks
    mock_response.raise_for_status = MagicMock()

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(return_value=mock_response)
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.core.security.httpx.AsyncClient", return_value=mock_client_instance),
        patch(
            "app.core.security.jwt.get_unverified_header", return_value={"kid": "kid1"}
        ),
        patch("app.core.security.jwk.construct"),
        patch("app.core.security.jwt.decode") as mock_decode,
        patch("app.core.security.settings") as mock_settings,
    ):
        mock_settings.COGNITO_REGION = "us-east-1"
        mock_settings.COGNITO_USER_POOL_ID = "pool-123"
        mock_decode.return_value = {
            "sub": "cognito-sub-123",
            "exp": 9999999999,
            "iss": "https://cognito-idp.us-east-1.amazonaws.com/pool-123",
            "email": "u@e.com",
            "token_use": "access",
            "client_id": "client",
            "username": "u@e.com",
        }

        result = await decode_and_validate_cognito_token("fake.token.here")
        assert result.sub == "cognito-sub-123"
        assert result.email == "u@e.com"


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_no_kid_raises():
    """decode_and_validate_cognito_token levanta quando header não tem kid."""
    from app.core.security import decode_and_validate_cognito_token

    mock_response = MagicMock()
    mock_response.json.return_value = {"keys": []}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.core.security.httpx.AsyncClient", return_value=mock_client),
        patch("app.core.security.jwt.get_unverified_header", return_value={}),
    ):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_cognito_token("token")
        assert "Invalid" in exc_info.value.detail


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_key_not_found_raises():
    """decode_and_validate_cognito_token levanta quando kid não está em keys."""
    from app.core.security import decode_and_validate_cognito_token

    mock_response = MagicMock()
    mock_response.json.return_value = {"keys": [{"kid": "other"}]}
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.core.security.httpx.AsyncClient", return_value=mock_client),
        patch(
            "app.core.security.jwt.get_unverified_header",
            return_value={"kid": "missing"},
        ),
    ):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_cognito_token("token")
        assert "Invalid" in exc_info.value.detail


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_iss_mismatch_raises():
    from app.core.security import decode_and_validate_cognito_token

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "keys": [{"kid": "kid1", "kty": "RSA", "n": "x", "e": "AQAB"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.core.security.httpx.AsyncClient", return_value=mock_client),
        patch(
            "app.core.security.jwt.get_unverified_header", return_value={"kid": "kid1"}
        ),
        patch("app.core.security.jwk.construct"),
        patch("app.core.security.jwt.decode") as mock_decode,
        patch("app.core.security.settings") as mock_settings,
    ):
        mock_settings.COGNITO_REGION = "us-east-1"
        mock_settings.COGNITO_USER_POOL_ID = "pool-123"
        mock_decode.return_value = {
            "sub": "sub",
            "exp": 999,
            "iss": "https://wrong-issuer.com",
            "email": "u@e.com",
            "token_use": "access",
            "client_id": "c",
            "username": "u",
        }
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_cognito_token("token")
        assert "Invalid" in exc_info.value.detail


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_jwt_error_raises():
    from jose import JWTError

    from app.core.security import decode_and_validate_cognito_token

    mock_response = MagicMock()
    mock_response.json.return_value = {
        "keys": [{"kid": "k", "kty": "RSA", "n": "x", "e": "AQAB"}]
    }
    mock_response.raise_for_status = MagicMock()
    mock_client = MagicMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("app.core.security.httpx.AsyncClient", return_value=mock_client),
        patch("app.core.security.jwt.get_unverified_header", return_value={"kid": "k"}),
        patch("app.core.security.jwk.construct"),
        patch("app.core.security.jwt.decode", side_effect=JWTError("expired")),
    ):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_cognito_token("token")
        assert (
            "expired" in exc_info.value.detail.lower()
            or "invalid" in exc_info.value.detail.lower()
        )


@pytest.mark.asyncio
async def test_decode_and_validate_cognito_token_fetch_jwks_fails_raises():
    from app.core.security import decode_and_validate_cognito_token

    mock_client_instance = MagicMock()
    mock_client_instance.get = AsyncMock(side_effect=Exception("Network error"))
    mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.core.security.httpx.AsyncClient",
        return_value=mock_client_instance,
    ):
        with pytest.raises(UnauthorizedError) as exc_info:
            await decode_and_validate_cognito_token("token")
        assert (
            "JWKS" in exc_info.value.detail or "fetch" in exc_info.value.detail.lower()
        )
