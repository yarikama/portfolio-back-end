from db.session import Base
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.sql import func


class AdminSetting(Base):
    """A value the owner keeps for the admin pages, by name: for now the
    current goal on the welcome page ("goal")."""

    __tablename__ = "admin_settings"

    key = Column(String(64), primary_key=True)
    value = Column(Text, nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
