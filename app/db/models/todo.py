import uuid

from db.session import Base
from sqlalchemy import Boolean, Column, Date, DateTime, Index, String, Text
from sqlalchemy import text as sql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func


class AdminTodo(Base):
    """
    A to-do on the admin's welcome page. `day` is the day it is for, in the
    owner's local time (the browser says which day it is). Until done it
    carries over to the days after; `done_on` is the day it was done.
    Daily items (`daily_key`) are added once per day; removing one only
    hides it, so it is not added again that day.
    """

    __tablename__ = "admin_todos"
    __table_args__ = (
        Index(
            "uq_admin_todos_daily_day",
            "daily_key",
            "day",
            unique=True,
            postgresql_where=sql("daily_key IS NOT NULL"),
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text = Column(Text, nullable=False)
    href = Column(Text, nullable=True)
    day = Column(Date, nullable=False, index=True)
    daily_key = Column(String(32), nullable=True)
    done_on = Column(Date, nullable=True)
    removed = Column(Boolean, nullable=False, default=False)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
