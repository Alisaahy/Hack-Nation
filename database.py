"""
Database Connection Management
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from contextlib import contextmanager
import os

# Database URL - using SQLite for MVP
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./research_discovery.db')

# Create engine
# For SQLite, we need check_same_thread=False to allow usage across threads in Flask
engine = create_engine(
    DATABASE_URL,
    connect_args={'check_same_thread': False} if DATABASE_URL.startswith('sqlite') else {},
    echo=False  # Set to True for SQL debugging
)

# Session factory
SessionLocal = scoped_session(sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
))


def get_db():
    """
    Get database session

    Usage in Flask routes:
        db = get_db()
        try:
            # Use db session
            db.add(obj)
            db.commit()
        except Exception as e:
            db.rollback()
            raise
        finally:
            db.close()
    """
    return SessionLocal()


@contextmanager
def db_session():
    """
    Context manager for database sessions

    Usage:
        with db_session() as db:
            db.add(obj)
            db.commit()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables

    This should be called once when setting up the database
    """
    from models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")


def drop_db():
    """
    Drop all tables - USE WITH CAUTION

    Only for development/testing
    """
    from models import Base
    Base.metadata.drop_all(bind=engine)
    print("All tables dropped!")


if __name__ == '__main__':
    # Initialize database when run directly
    init_db()
