import uuid

from db.session import Base
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(255), unique=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    tags = Column(ARRAY(String), nullable=False)

    # Foreign key to categories table
    category_id = Column(
        UUID(as_uuid=True), ForeignKey("categories.id"), nullable=False
    )

    # Legacy field - kept for backward compatibility during migration
    # Can be removed after migration is complete
    category = Column(String(50), nullable=True)

    year = Column(String(20), nullable=False)
    link = Column(String(500), nullable=True)
    github = Column(String(500), nullable=True)
    metrics = Column(Text, nullable=True)
    formula = Column(Text, nullable=True)
    featured = Column(Boolean, default=False)
    order = Column(Integer, default=0)
    published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationship
    category_rel = relationship("Category", back_populates="projects")
