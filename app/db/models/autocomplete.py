import uuid

from db.session import Base
from sqlalchemy import Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func


class AutocompleteSuggestion(Base):
    """One suggestion shown in the note editor, and what became of it.

    This is the training and evaluation data for the autocomplete model: the
    context it saw, what it proposed, and whether the author took it.
    """

    __tablename__ = "autocomplete_suggestions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    model_version = Column(String(200), nullable=False)
    # The lab note being edited; null while writing a note not saved yet.
    note_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    # The prompt text the model continued (title header plus the text before
    # the cursor, trimmed to the context limit).
    prompt = Column(Text, nullable=False)
    # What the model generated, and the part of it that was shown.
    completion = Column(Text, nullable=False)
    suggestion = Column(Text, nullable=False)
    # [[token, logprob], ...] for the completion, to revisit the cut-off.
    # Since generation stops at the first unsure token, this ends with that
    # token (or a sentence end), not after 16 tokens.
    tokens = Column(JSONB, nullable=True)
    # The confidence cut-off in force when it was shown, to compare settings.
    min_token_prob = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=False)
    # accepted | rejected | ignored; null until the editor reports back.
    outcome = Column(String(16), nullable=True, index=True)
    # How much of the suggestion ended up in the text (all of it on Tab,
    # a prefix when the author typed along with it).
    accepted_chars = Column(Integer, nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
