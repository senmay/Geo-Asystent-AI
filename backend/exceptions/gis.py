"""GIS-specific exception classes."""

from typing import Dict, Any, Optional
from .base import GeoAsystentException, ErrorCode


class LayerNotFoundError(GeoAsystentException):
    """Raised when a requested GIS layer is not found."""
    
    def __init__(self, layer_name: str, available_layers: Optional[list] = None):
        details = {"layer_name": layer_name}
        if available_layers:
            details["available_layers"] = available_layers
            
        user_message = f"Warstwa '{layer_name}' nie została znaleziona."
        if available_layers:
            user_message += f" Dostępne warstwy: {', '.join(available_layers)}."
            
        super().__init__(
            message=f"Layer '{layer_name}' not found in database",
            code=ErrorCode.LAYER_NOT_FOUND,
            details=details,
            user_message=user_message
        )


class InvalidLayerNameError(GeoAsystentException):
    """Raised when an invalid layer name is provided."""
    
    def __init__(self, layer_name: str, valid_patterns: Optional[list] = None):
        details = {"layer_name": layer_name}
        if valid_patterns:
            details["valid_patterns"] = valid_patterns
            
        user_message = f"Nieprawidłowa nazwa warstwy: '{layer_name}'."
        if valid_patterns:
            user_message += f" Spróbuj: {', '.join(valid_patterns)}."
        else:
            user_message += " Spróbuj 'działki', 'budynki' lub 'gpz'."
            
        super().__init__(
            message=f"Invalid layer name: '{layer_name}'",
            code=ErrorCode.INVALID_LAYER_NAME,
            details=details,
            user_message=user_message
        )


class GISDataProcessingError(GeoAsystentException):
    """Raised when GIS data processing fails."""
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None):
        details = {"operation": operation}
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
            
        super().__init__(
            message=f"GIS data processing failed during operation: {operation}",
            code=ErrorCode.GIS_DATA_PROCESSING_ERROR,
            details=details,
            user_message=f"Błąd podczas przetwarzania danych GIS ({operation}). Spróbuj ponownie."
        )


class DatabaseConnectionError(GeoAsystentException):
    """Raised when database connection fails."""
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None):
        details = {"operation": operation}
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
            
        super().__init__(
            message=f"Database connection failed during operation: {operation}",
            code=ErrorCode.DATABASE_CONNECTION_ERROR,
            details=details,
            user_message="Błąd połączenia z bazą danych. Spróbuj ponownie za chwilę."
        )


class SpatialQueryError(GeoAsystentException):
    """Raised when spatial query execution fails."""
    
    def __init__(self, query_type: str, parameters: Optional[Dict[str, Any]] = None, original_error: Optional[Exception] = None):
        details = {
            "query_type": query_type,
            "parameters": parameters or {}
        }
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
            
        super().__init__(
            message=f"Spatial query failed: {query_type}",
            code=ErrorCode.SPATIAL_QUERY_ERROR,
            details=details,
            user_message=f"Błąd podczas wykonywania zapytania przestrzennego ({query_type}). Sprawdź parametry i spróbuj ponownie."
        )


class ValidationError(GeoAsystentException):
    """Raised when input validation fails."""
    
    def __init__(self, parameter: str, value: Any, reason: str):
        details = {
            "parameter": parameter,
            "value": str(value),
            "reason": reason
        }
        
        super().__init__(
            message=f"Validation failed for parameter '{parameter}': {reason}",
            code=ErrorCode.VALIDATION_ERROR,
            details=details,
            user_message=f"Nieprawidłowa wartość parametru '{parameter}': {reason}"
        )