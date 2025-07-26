"""Exception handling module for Geo-Asystent AI backend."""

from .base import GeoAsystentException, ErrorCode
from .gis import (
    LayerNotFoundError,
    InvalidLayerNameError,
    GISDataProcessingError,
    DatabaseConnectionError,
    SpatialQueryError,
    ValidationError
)
from .llm import (
    LLMServiceError,
    IntentClassificationError,
    LLMTimeoutError,
    LLMAPIKeyError
)

__all__ = [
    # Base exceptions
    "GeoAsystentException",
    "ErrorCode",
    
    # GIS exceptions
    "LayerNotFoundError",
    "InvalidLayerNameError", 
    "GISDataProcessingError",
    "DatabaseConnectionError",
    "SpatialQueryError",
    "ValidationError",
    
    # LLM exceptions
    "LLMServiceError",
    "IntentClassificationError",
    "LLMTimeoutError",
    "LLMAPIKeyError",
]