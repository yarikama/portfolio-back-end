import uuid

from db.session import Base
from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class ContactMessage(Base):
    __tablename__ = "contact_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(Text, nullable=False)
    email = Column(String(255), nullable=False)
    subject = Column(Text, nullable=False)
    message = Column(Text, nullable=False)
    read = Column(Boolean, default=False)
    replied = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
