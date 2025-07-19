"""Models module for Geo-Asystent AI backend."""

from .schemas import ChatRequest
from .domain import LayerConfig, ParcelCriteria, QueryResult

__all__ = [
    # API schemas
    "ChatRequest",
    
    # Domain models
    "LayerConfig", 
    "ParcelCriteria",
    "QueryResult",
]