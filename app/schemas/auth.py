from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class CognitoTokenPayload(BaseModel):
    sub: str
    exp: int
    iss: str
    email: Optional[str]
    token_use: Optional[str]
    client_id: Optional[str]
    username: Optional[str]


class RegisterRequest(BaseModel):
    email: EmailStr = Field(..., min_length=1)
    password: str = Field(..., min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    email: EmailStr = Field(..., min_length=1)
    refresh_token: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int
