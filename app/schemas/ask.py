from typing import Annotated

from pydantic import StringConstraints
from schemas.base import BaseSchema
from services.ask import MAX_QUESTION_CHARS


class AskRequest(BaseSchema):
    # Stripped before the length checks: surrounding whitespace neither
    # counts toward the limit nor makes a blank question valid.
    question: Annotated[
        str,
        StringConstraints(
            strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_CHARS
        ),
    ]
