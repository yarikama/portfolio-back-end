import datetime
from typing import Optional
from uuid import UUID

from schemas.base import BaseSchema


class LabNoteBase(BaseSchema):
    title: str
    slug: str
    excerpt: str
    content: str
    tags: list[str]
    read_time: str
    date: datetime.date
    published: bool = False


class LabNoteCreate(LabNoteBase):
    pass


class LabNoteUpdate(BaseSchema):
    title: Optional[str] = None
    slug: Optional[str] = None
    excerpt: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[list[str]] = None
    read_time: Optional[str] = None
    date: Optional[datetime.date] = None
    published: Optional[bool] = None


class LabNoteResponse(LabNoteBase):
    id: UUID
    created_at: datetime.datetime
    updated_at: datetime.datetime


class LabNoteListResponse(BaseSchema):
    id: UUID
    title: str
    slug: str
    excerpt: str
    tags: list[str]
    read_time: Optional[str] = None
    date: datetime.date
    published: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
