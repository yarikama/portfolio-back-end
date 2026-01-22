from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import EmailStr, Field
from schemas.base import BaseSchema


class ContactCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=5, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactUpdate(BaseSchema):
    read: Optional[bool] = Field(None)
    replied: Optional[bool] = Field(None)


class ContactResponse(BaseSchema):
    id: UUID
    name: str
    email: str
    subject: str
    message: str
    read: bool
    replied: bool
    created_at: datetime
