"""Segurança: secret hash Cognito, extração/validação JWT (Cognito)."""

import base64
import hmac
import hashlib

import httpx
from fastapi import Request
from jose import JWTError, jwk, jwt

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.schemas.auth import CognitoTokenPayload


def cognito_secret_hash(username: str, client_id: str, client_secret: str) -> str:
    """Calcula o SECRET_HASH para Cognito (app client com secret).

    Obrigatório em SignUp e InitiateAuth quando o app client tem client secret.
    """
    message = username + client_id
    dig = hmac.new(
        client_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64.b64encode(dig).decode("utf-8")


def get_token_from_authorization_header(request: Request) -> str:
    """Extrai o token Bearer do header Authorization.

    Raises:
        UnauthorizedError: Se o header estiver ausente ou em formato inválido.
    """
    auth = request.headers.get("Authorization")
    if not auth or not auth.startswith("Bearer "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    token = auth[7:].strip()
    if not token:
        raise UnauthorizedError("Missing or invalid Authorization header")
    return token


async def decode_and_validate_cognito_token(token: str) -> CognitoTokenPayload:
    """Decodifica o JWT e valida assinatura e claims com o JWKS do Cognito.

    Valida: assinatura (JWKS), iss, exp.

    Returns:
        Payload tipado (CognitoTokenPayload).

    Raises:
        UnauthorizedError: Se o token for inválido ou expirado.
    """
    jwks_url = (
        f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/"
        f"{settings.COGNITO_USER_POOL_ID}/.well-known/jwks.json"
    )
    async with httpx.AsyncClient() as client:
        try:
            jwks_response = await client.get(jwks_url, timeout=10.0)
            jwks_response.raise_for_status()
            jwks = jwks_response.json()
        except Exception as e:
            raise UnauthorizedError("Could not fetch Cognito JWKS") from e

    try:
        unverified = jwt.get_unverified_header(token)
        kid = unverified.get("kid")
        if not kid:
            raise UnauthorizedError("Invalid token")
        key_entry = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key_entry:
            raise UnauthorizedError("Invalid token")
        public_key = jwk.construct(key_entry)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_exp": True, "verify_aud": False},
        )
        iss = f"https://cognito-idp.{settings.COGNITO_REGION}.amazonaws.com/{settings.COGNITO_USER_POOL_ID}"
        if payload.get("iss") != iss:
            raise UnauthorizedError("Invalid token")
        return CognitoTokenPayload(
            sub=payload["sub"],
            exp=payload["exp"],
            iss=payload["iss"],
            email=payload.get("email"),
            token_use=payload.get("token_use"),
            client_id=payload.get("client_id"),
            username=payload.get("username"),
        )
    except JWTError as e:
        raise UnauthorizedError("Invalid or expired token") from e
