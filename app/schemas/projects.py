from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from schemas.base import BaseSchema


class ProjectCategory(str, Enum):
    ENGINEERING = "engineering"
    ML = "ml"


class ProjectBase(BaseSchema):
    slug: str
    title: str
    description: str
    tags: list[str]
    category: ProjectCategory
    year: str
    link: Optional[str] = None
    github: Optional[str] = None
    metrics: Optional[str] = None
    formula: Optional[str] = None
    featured: bool
    order: int
    published: bool


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseSchema):
    slug: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[list[str]] = None
    category: Optional[ProjectCategory] = None
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
    created_at: datetime
    updated_at: datetime
