from core.config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# A pooled connection can be dead by the time a request checks it out (the
# database pod restarted or failed over; originally Neon, which suspends
# after a few idle minutes). pre_ping tests it with SELECT 1 and reconnects
# instead of failing the request; recycle retires connections before they get
# that old.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """The models' base: typed columns (Mapped[...]), so an attribute reads as
    its value's type (str, datetime) rather than Column[...]."""
