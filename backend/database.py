"""
DEPRECATED: This file is kept for backward compatibility.
Use config.database module for new code.
"""

from config.database import engine, SessionLocal, get_db, get_db_engine

# Re-export for backward compatibility
__all__ = ["engine", "SessionLocal", "get_db", "get_db_engine"]
