import uuid

from db.session import Base
from sqlalchemy import Boolean, Column, Date, DateTime, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.sql import func


class LabNote(Base):
    __tablename__ = "lab_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    excerpt = Column(Text, nullable=False)
    content = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=False)
    read_time = Column(String(50), nullable=False)
    date = Column(Date, nullable=False)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
