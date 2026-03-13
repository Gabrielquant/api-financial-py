import asyncio
from typing import Any, cast

import boto3
from botocore.exceptions import ClientError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import cognito_secret_hash
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


def _cognito_client():
    kwargs = {"region_name": settings.COGNITO_REGION}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("cognito-idp", **kwargs)


async def _run_cognito_sign_up(email: str, password: str, secret_hash: str) -> str:

    def _sync() -> str:
        client = _cognito_client()
        resp = client.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "preferred_username", "Value": email},
            ],
        )
        return str(resp["UserSub"])

    return await asyncio.to_thread(_sync)


async def _run_cognito_confirm_and_verify(email: str) -> None:

    def _sync() -> None:
        client = _cognito_client()
        client.admin_confirm_sign_up(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
        client.admin_update_user_attributes(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[{"Name": "email_verified", "Value": "true"}],
        )

    await asyncio.to_thread(_sync)


async def _run_cognito_initiate_auth(
    email: str, password: str, secret_hash: str
) -> dict[str, Any]:

    def _sync() -> dict[str, Any]:
        client = _cognito_client()
        return cast(
            dict[str, Any],
            client.initiate_auth(
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": email,
                    "PASSWORD": password,
                    "SECRET_HASH": secret_hash,
                },
                ClientId=settings.COGNITO_CLIENT_ID,
            ),
        )

    return await asyncio.to_thread(_sync)


async def _run_cognito_refresh_token(
    refresh_token: str, secret_hash: str
) -> dict[str, Any]:

    def _sync() -> dict[str, Any]:
        client = _cognito_client()
        return cast(
            dict[str, Any],
            client.initiate_auth(
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={
                    "REFRESH_TOKEN": refresh_token,
                    "SECRET_HASH": secret_hash,
                },
                ClientId=settings.COGNITO_CLIENT_ID,
            ),
        )

    return await asyncio.to_thread(_sync)


async def register(email: str, password: str, db: AsyncSession) -> dict:
    secret_hash = cognito_secret_hash(
        email,
        settings.COGNITO_CLIENT_ID,
        settings.COGNITO_CLIENT_SECRET,
    )
    try:
        cognito_sub = await _run_cognito_sign_up(email, password, secret_hash)
        await _run_cognito_confirm_and_verify(email)

        user_repo = UserRepository(db)
        existing = await user_repo.get_by_cognito_id(cognito_sub)
        if not existing:
            await user_repo.create(email=email, cognito_id=cognito_sub)

        return {"message": "User registered. Email verified. You can sign in."}

    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "UsernameExistsException":
            raise ConflictError("Email already registered") from e
        raise BadRequestError(
            e.response.get("Error", {}).get("Message", "Registration failed")
        ) from e


async def login(email: str, password: str, db: AsyncSession) -> TokenResponse:
    user_repo = UserRepository(db)
    if not await user_repo.get_by_email(email):
        raise UnauthorizedError("Credentials are invalid")

    secret_hash = cognito_secret_hash(
        email,
        settings.COGNITO_CLIENT_ID,
        settings.COGNITO_CLIENT_SECRET,
    )
    try:
        response = await _run_cognito_initiate_auth(email, password, secret_hash)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in (
            "NotAuthorizedException",
            "UserNotFoundException",
            "UserNotConfirmedException",
        ):
            raise UnauthorizedError("Invalid credentials") from e
        raise UnauthorizedError(
            e.response.get("Error", {}).get("Message", "Authentication failed")
        ) from e

    auth_result = response.get("AuthenticationResult")
    if not auth_result:
        raise UnauthorizedError("Authentication did not return tokens")

    return TokenResponse(
        access_token=auth_result["AccessToken"],
        refresh_token=auth_result["RefreshToken"],
        token_type=auth_result.get("TokenType", "Bearer"),
        expires_in=auth_result["ExpiresIn"],
    )


async def refresh(refresh_token: str, email: str, db: AsyncSession) -> TokenResponse:

    user_repo = UserRepository(db)
    user = await user_repo.get_by_email(email)
    if not user:
        raise UnauthorizedError("Invalid or expired refresh token")

    secret_hash = cognito_secret_hash(
        user.cognito_id,
        settings.COGNITO_CLIENT_ID,
        settings.COGNITO_CLIENT_SECRET,
    )
    try:
        response = await _run_cognito_refresh_token(refresh_token, secret_hash)
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("NotAuthorizedException", "UserNotFoundException"):
            raise UnauthorizedError("Invalid or expired refresh token") from e
        raise UnauthorizedError(
            e.response.get("Error", {}).get("Message", "Refresh failed")
        ) from e

    auth_result = response.get("AuthenticationResult")
    if not auth_result:
        raise UnauthorizedError("Refresh did not return tokens")

    return TokenResponse(
        access_token=auth_result["AccessToken"],
        refresh_token=auth_result.get("RefreshToken") or refresh_token,
        token_type=auth_result.get("TokenType", "Bearer"),
        expires_in=auth_result["ExpiresIn"],
    )
