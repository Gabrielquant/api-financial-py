"""Schemas de categoria (CategoryCreate, CategoryResponse, etc.)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.category import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(..., min_length=1)
    type: CategoryType

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip()
        return v


class CategoryUpdate(BaseModel):
    name: str | None = Field(None, min_length=1)
    type: CategoryType | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v: str | None) -> str | None:
        if v is None:
            return None
        if isinstance(v, str):
            return v.strip()
        return v


class CategoryResponse(BaseModel):
    id: UUID
    # user_id: UUID
    name: str
    type: CategoryType
    created_at: datetime

    model_config = {"from_attributes": True}


class CategoryListResponse(BaseModel):
    items: list[CategoryResponse]
    total: int
