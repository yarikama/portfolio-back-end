from db.session import Base
from sqlalchemy import Column, DateTime, String, Text


class AdminSeen(Base):
    """
    When each admin last opened a page that counts what is new since
    (Questions), so the nav can say how many came in meanwhile. Per account,
    in the database, so it holds across browsers and devices.
    """

    __tablename__ = "admin_seen"

    email = Column(Text, primary_key=True)
    page = Column(String(32), primary_key=True)
    seen_at = Column(DateTime(timezone=True), nullable=False)
