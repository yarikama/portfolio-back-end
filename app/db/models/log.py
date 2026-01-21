from db.session import Base
from sqlalchemy import Column, Integer, Text


class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
