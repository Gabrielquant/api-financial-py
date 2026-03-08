"""Schemas de categoria (CategoryCreate, CategoryResponse, etc.)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    """Payload para criar categoria."""

    name: str = Field(..., min_length=1, strip_whitespace=True)
    type: CategoryType


class CategoryUpdate(BaseModel):
    """Payload para atualizar categoria (PATCH)."""

    name: str | None = Field(None, min_length=1, strip_whitespace=True)
    type: CategoryType | None = None


class CategoryResponse(BaseModel):
    """Resposta de uma categoria."""

    id: UUID
    # user_id: UUID
    name: str
    type: CategoryType
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    """Resposta de listagem de categorias."""

    items: list[CategoryResponse]
    total: int
