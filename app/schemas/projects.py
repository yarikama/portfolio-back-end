from datetime import datetime
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
    cover_image: str | None = None
    link: str | None = None
    github: str | None = None
    metrics: str | None = None
    formula: str | None = None
    featured: bool
    order: int
    published: bool


class ProjectCreate(ProjectBase):
    category_id: UUID = Field(..., description="Category UUID")


class ProjectUpdate(BaseSchema):
    slug: str | None = None
    title: str | None = None
    description: str | None = None
    tags: list[str] | None = None
    category_id: UUID | None = Field(None, description="Category UUID")
    year: str | None = None
    cover_image: str | None = None
    link: str | None = None
    github: str | None = None
    metrics: str | None = None
    formula: str | None = None
    featured: bool | None = None
    order: int | None = None
    published: bool | None = None


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
