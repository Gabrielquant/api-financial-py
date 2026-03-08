"""Schemas de usuário (UserCreate, UserResponse, etc.)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):

    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):

    id: UUID
    email: str
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
