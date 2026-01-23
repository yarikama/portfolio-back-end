from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import Field
from schemas.base import BaseSchema
from schemas.category import CategoryResponse


class ProjectBase(BaseSchema):
    slug: str
    title: str
    description: str
    tags: list[str]
    year: str
    link: Optional[str] = None
    github: Optional[str] = None
    metrics: Optional[str] = None
    formula: Optional[str] = None
    featured: bool
    order: int
    published: bool


class ProjectCreate(ProjectBase):
    category_id: UUID = Field(..., description="Category UUID")


class ProjectUpdate(BaseSchema):
    slug: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category_id: Optional[UUID] = Field(None, description="Category UUID")
    year: Optional[str] = None
    link: Optional[str] = None
    github: Optional[str] = None
    metrics: Optional[str] = None
    formula: Optional[str] = None
    featured: Optional[bool] = None
    order: Optional[int] = None
    published: Optional[bool] = None


class ProjectResponse(ProjectBase):
    id: UUID
    category: CategoryResponse = Field(..., description="Full category object")
    created_at: datetime
    updated_at: datetime

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Custom validation to handle category relationship."""
        if hasattr(obj, "category_rel"):
            # Create a dict with category_rel mapped to category
            data = {
                **{k: v for k, v in obj.__dict__.items() if not k.startswith("_")},
                "category": obj.category_rel,
            }
            return super().model_validate(data, **kwargs)
        return super().model_validate(obj, **kwargs)


class ProjectReorderItem(BaseSchema):
    id: UUID
    order: int


class ProjectReorderRequest(BaseSchema):
    orders: list[ProjectReorderItem]
