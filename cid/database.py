"""Basic database setup for SQLAlchemy ORM."""
# Via FastAPI tutorial: https://fastapi.tiangolo.com/tutorial/sql-databases/

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from cid.config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
