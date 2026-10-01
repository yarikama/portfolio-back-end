import uuid

from db.session import Base
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func


class AskQuestion(Base):
    """One question asked in the "ask about my work" chat, and its answer.

    What visitors want to know, which answers cite nothing or get cut off,
    and, with a rating, the evaluation set of real questions. Kept for
    ASK_QUESTION_RETENTION_DAYS; the visitor's address is never stored.
    """

    __tablename__ = "ask_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
    question = Column(Text, nullable=False)
    # A passage the visitor highlighted, and the page it is on.
    quote = Column(Text, nullable=True)
    page = Column(String(200), nullable=True)
    # As streamed, so a broken-off answer keeps what was sent before it broke.
    answer = Column(Text, nullable=False)
    # [{"id", "kind", "title", "url"}] as sent in the done event. Ids like P3
    # change when content does; the title and url say what was meant.
    citations = Column(JSONB, nullable=False)
    # answered | error (the answer broke off).
    status = Column(String(16), nullable=False)
    # The answer hit ASK_MAX_TOKENS and ends mid-sentence.
    truncated = Column(Boolean, nullable=False, default=False)
    output_tokens = Column(Integer, nullable=True)
    # From the model accepting the question to the end of the answer.
    duration_ms = Column(Integer, nullable=False)
    # The owner, logged in, trying the chat; not a visitor.
    admin = Column(Boolean, nullable=False, default=False)
    # good | bad, set by the owner in the admin area; null until then.
    rating = Column(String(8), nullable=True, index=True)
