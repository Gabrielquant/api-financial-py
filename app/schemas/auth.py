"""Schemas de autenticação (LoginRequest, TokenResponse, etc.)."""

from pydantic import BaseModel, EmailStr, Field


class CognitoTokenPayload(BaseModel):
    sub: str
    exp: int
    iss: str
    email: str | None = None
    token_use: str | None = None
    client_id: str | None = None
    username: str | None = None


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    email: EmailStr
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
