"""Schemas de categoria (CategoryCreate, CategoryResponse, etc.)."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.models.category import CategoryType


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1)
    type: CategoryType

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        if v is None:
            return v

        if isinstance(v, str):
            v = v.strip()

            if not v:
                raise ValueError("name cannot be empty or blank")

        return v


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    """Update schema: all fields optional."""

    name: Optional[str] = Field(None, min_length=1)
    type: Optional[CategoryType] = Field(None, description="The type of the category")

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, v):
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("name cannot be empty or blank")
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
