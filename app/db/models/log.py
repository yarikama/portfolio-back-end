from db.session import Base
from sqlalchemy import Integer, Text
from sqlalchemy.orm import Mapped, mapped_column


# Left over from the ML predictor, which is gone. The table stays (empty in
# production) until its owner decides to drop it; the model keeps Alembic
# from proposing that on its own.
class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    request: Mapped[str] = mapped_column(Text)
    response: Mapped[str] = mapped_column(Text)
