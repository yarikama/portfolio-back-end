"""Category model for project categorization."""

from datetime import datetime
from uuid import uuid4

from db.session import Base
from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship


class Category(Base):
    """Category model."""

    __tablename__ = "categories"
    # The table was created with both a unique constraint and a unique index on
    # name (4b2c8d0e1f23). The index alone would do; declaring the constraint
    # too keeps the model matching the database, so autogenerate does not
    # propose dropping it.
    __table_args__ = (UniqueConstraint("name", name="categories_name_key"),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(50), unique=True, nullable=False, index=True)
    label = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    order = Column(Integer, default=0, nullable=False)

    created_at = Column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationship
    projects = relationship("Project", back_populates="category_rel")
