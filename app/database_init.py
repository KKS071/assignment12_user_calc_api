# app/database_init.py

from app.database import engine
from app.models.user import Base


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_db():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


if __name__ == "__main__":
    init_db()  # pragma: no cover