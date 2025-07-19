"""API dependencies for FastAPI."""

from fastapi import Depends
from sqlalchemy.engine import Engine

from config.database import get_db_engine
from services import IntentClassificationService, LLMService, GISService


def get_intent_service() -> IntentClassificationService:
    """Dependency for intent classification service."""
    return IntentClassificationService()


def get_llm_service() -> LLMService:
    """Dependency for LLM service."""
    return LLMService()


def get_gis_service(db_engine: Engine = Depends(get_db_engine)) -> GISService:
    """Dependency for GIS service."""
    return GISService(db_engine)