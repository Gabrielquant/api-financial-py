"""Schemas de autenticação (LoginRequest, TokenResponse, etc.)."""

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    """Payload para POST /auth/register."""

    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    """Payload para POST /auth/login."""

    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    """Resposta com tokens do Cognito."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
