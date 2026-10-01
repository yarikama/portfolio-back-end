"""Pydantic schemas for Category."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class CategoryBase(BaseModel):
    """Base category schema."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique category identifier (e.g., 'ml', 'engineering')",
    )
    label: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Display label (e.g., 'ML/AI', 'Engineering')",
    )
    description: str | None = Field(
        None, description="Optional description of the category"
    )
    order: int = Field(0, description="Display order (lower number = higher priority)")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""

    pass


class CategoryUpdate(BaseModel):
    """Schema for updating a category."""

    name: str | None = Field(None, min_length=1, max_length=50)
    label: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    order: int | None = Field(None, ge=0)


class CategoryResponse(CategoryBase):
    """Schema for category response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CategoryWithCount(CategoryResponse):
    """Category with project count."""

    count: int = Field(..., description="Number of projects in this category")


class CategoryReorderItem(BaseModel):
    """Schema for reordering a single category."""

    id: UUID
    order: int = Field(..., ge=0)


class CategoryReorderRequest(BaseModel):
    """Schema for reordering categories."""

    orders: list[CategoryReorderItem] = Field(..., min_items=1)
