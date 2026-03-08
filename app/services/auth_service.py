"""Serviço de autenticação (registro, login, sync com Cognito)."""

import json
import base64
from botocore.exceptions import ClientError
import boto3

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BadRequestError, ConflictError, UnauthorizedError
from app.core.security import cognito_secret_hash
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenResponse


def _cognito_client():
    """Client Cognito; usa credenciais do settings quando definidas (boto3 não lê .env)."""
    kwargs = {"region_name": settings.COGNITO_REGION}
    if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
        kwargs["aws_access_key_id"] = settings.AWS_ACCESS_KEY_ID
        kwargs["aws_secret_access_key"] = settings.AWS_SECRET_ACCESS_KEY
    return boto3.client("cognito-idp", **kwargs)


def _decode_id_token_payload(id_token: str) -> dict:
    """Decodifica o payload do IdToken JWT (apenas leitura; validação nas rotas protegidas)."""
    try:
        parts = id_token.split(".")
        if len(parts) != 3:
            return {}
        payload_b64 = parts[1]
        padding = 4 - len(payload_b64) % 4
        if padding != 4:
            payload_b64 += "=" * padding
        payload_json = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_json)
    except Exception:
        return {}


def register(email: str, password: str, db: Session) -> dict:
    """Registra usuário no Cognito (SignUp), confirma a conta e marca email como verificado."""
    client = _cognito_client()
    secret_hash = cognito_secret_hash(
        email,
        settings.COGNITO_CLIENT_ID,
        settings.COGNITO_CLIENT_SECRET,
    )
    try:
        sign_up_response = client.sign_up(
            ClientId=settings.COGNITO_CLIENT_ID,
            SecretHash=secret_hash,
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
                {"Name": "preferred_username", "Value": email},
            ],
        )
        cognito_sub = sign_up_response["UserSub"]

        client.admin_confirm_sign_up(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
        )
        client.admin_update_user_attributes(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Username=email,
            UserAttributes=[{"Name": "email_verified", "Value": "true"}],
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code == "UsernameExistsException":
            raise ConflictError("Email already registered") from e
        raise BadRequestError(e.response.get("Error", {}).get("Message", "Registration failed"))

    # Persiste usuário no banco com cognito_id (sub) e email
    repo = UserRepository(db)
    if not repo.get_by_cognito_id(cognito_sub):
        repo.create(email=email, cognito_id=cognito_sub)

    return {"message": "User registered. Email verified. You can sign in."}


def login(email: str, password: str, db: Session) -> TokenResponse:
    """Autentica no Cognito (InitiateAuth), sincroniza usuário local e retorna tokens."""
    client = _cognito_client()
    secret_hash = cognito_secret_hash(
        email,
        settings.COGNITO_CLIENT_ID,
        settings.COGNITO_CLIENT_SECRET,
    )
    try:
        response = client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": email,
                "PASSWORD": password,
                "SECRET_HASH": secret_hash,
            },
            ClientId=settings.COGNITO_CLIENT_ID,
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code", "")
        if error_code in ("NotAuthorizedException", "UserNotFoundException", "UserNotConfirmedException"):
            raise UnauthorizedError("Invalid credentials") from e
        raise UnauthorizedError(e.response.get("Error", {}).get("Message", "Authentication failed")) from e

    auth_result = response.get("AuthenticationResult")
    if not auth_result:
        raise UnauthorizedError("Authentication did not return tokens")

    id_token = auth_result.get("IdToken")
    if id_token:
        payload = _decode_id_token_payload(id_token)
        sub = payload.get("sub")
        token_email = payload.get("email") or email
        if sub:
            repo = UserRepository(db)
            user = repo.get_by_cognito_id(sub)
            if not user:
                repo.create(email=token_email, cognito_id=sub)

    return TokenResponse(
        access_token=auth_result["AccessToken"],
        refresh_token=auth_result["RefreshToken"],
        token_type=auth_result.get("TokenType", "Bearer"),
        expires_in=auth_result["ExpiresIn"],
    )
