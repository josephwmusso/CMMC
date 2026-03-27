"""
Database engine and session factory.

Path: D:\\cmmc-platform\\src\\db\\session.py

Usage:
    from src.db.session import get_session, engine

    with get_session() as session:
        controls = session.query(Control).all()
"""

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Import from your existing config
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from configs.settings import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,       # reconnect on stale connections
    echo=False,               # set True to see SQL in console during debugging
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


@contextmanager
def get_session():
    """
    Context manager that yields a SQLAlchemy session and handles
    commit/rollback automatically.

    Usage:
        with get_session() as db:
            db.add(some_object)
            # auto-committed on exit, rolled back on exception
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_session_dependency():
    """FastAPI dependency injector for request-scoped sessions."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
get_db = get_session_dependency
