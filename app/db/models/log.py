from db.session import Base
from sqlalchemy import Column, Integer, Text


# Left over from the ML predictor, which is gone. The table stays (empty in
# production) until its owner decides to drop it; the model keeps Alembic
# from proposing that on its own.
class RequestLog(Base):
    __tablename__ = "request_logs"

    id = Column(Integer, primary_key=True, index=True)
    request = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
