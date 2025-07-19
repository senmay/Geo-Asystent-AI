"""Database configuration and connection management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine
from typing import Generator

from .settings import get_settings


def create_database_engine() -> Engine:
    """Create and configure database engine."""
    settings = get_settings()
    
    engine = create_engine(
        settings.database.url,
        echo=settings.api.debug,  # Log SQL queries in debug mode
        pool_pre_ping=True,  # Verify connections before use
        pool_recycle=3600,  # Recycle connections after 1 hour
    )
    
    return engine


# Global engine instance
engine = create_database_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator:
    """
    Dependency to get a database session.
    Ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_engine() -> Engine:
    """
    Dependency to get the database engine directly.
    """
    return engine