"""Schemas de autenticação (LoginRequest, TokenResponse, etc.)."""

from pydantic import BaseModel, EmailStr, Field


class CognitoTokenPayload(BaseModel):
    """Contrato de saída do payload JWT validado pelo Cognito (IdToken/AccessToken)."""

    sub: str
    exp: int
    iss: str
    email: str | None = None
    token_use: str | None = None
    client_id: str | None = None
    username: str | None = None


class RegisterRequest(BaseModel):
    """Payload para POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Payload para POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    """Payload para POST /auth/refresh."""

    email: EmailStr
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Resposta com tokens do Cognito."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
