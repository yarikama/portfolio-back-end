from core.config import DATABASE_URL
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Neon suspends its compute after a few idle minutes and drops every open
# connection, so a pooled connection can be dead by the time a request checks
# it out. pre_ping tests it with SELECT 1 and reconnects instead of failing the
# request; recycle retires connections before they get that old.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
