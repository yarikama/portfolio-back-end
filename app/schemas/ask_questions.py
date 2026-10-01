from datetime import datetime
from typing import Literal
from uuid import UUID

from schemas.base import BaseSchema


class Citation(BaseSchema):
    id: str
    kind: str
    title: str
    url: str | None = None


class AskQuestionResponse(BaseSchema):
    id: UUID
    created_at: datetime
    question: str
    quote: str | None
    page: str | None
    answer: str
    citations: list[Citation]
    status: str
    truncated: bool
    output_tokens: int | None
    duration_ms: int
    admin: bool
    rating: str | None


class AskQuestionRating(BaseSchema):
    # null clears it.
    rating: Literal["good", "bad"] | None
