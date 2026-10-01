import datetime
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
    title: str | None = None
    slug: str | None = None
    excerpt: str | None = None
    content: str | None = None
    tags: list[str] | None = None
    read_time: str | None = None
    date: datetime.date | None = None
    published: bool | None = None


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
    read_time: str | None = None
    date: datetime.date
    published: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime
