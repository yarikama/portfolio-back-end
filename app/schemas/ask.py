from pydantic import Field, field_validator
from schemas.base import BaseSchema
from services.ask import MAX_QUESTION_CHARS


class AskRequest(BaseSchema):
    question: str = Field(..., min_length=1, max_length=MAX_QUESTION_CHARS)

    @field_validator("question")
    @classmethod
    def not_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Ask a question.")
        return value
