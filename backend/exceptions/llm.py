"""LLM-specific exception classes."""

from typing import Dict, Any, Optional
from .base import GeoAsystentException, ErrorCode


class LLMServiceError(GeoAsystentException):
    """Raised when LLM service encounters an error."""
    
    def __init__(self, operation: str, original_error: Optional[Exception] = None):
        details = {"operation": operation}
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
            
        super().__init__(
            message=f"LLM service error during operation: {operation}",
            code=ErrorCode.LLM_SERVICE_ERROR,
            details=details,
            user_message="Błąd usługi AI. Spróbuj ponownie za chwilę."
        )


class IntentClassificationError(GeoAsystentException):
    """Raised when intent classification fails."""
    
    def __init__(self, query: str, original_error: Optional[Exception] = None):
        details = {"query": query}
        if original_error:
            details["original_error"] = str(original_error)
            details["error_type"] = type(original_error).__name__
            
        super().__init__(
            message=f"Intent classification failed for query: {query}",
            code=ErrorCode.INTENT_CLASSIFICATION_ERROR,
            details=details,
            user_message="Nie udało się zrozumieć zapytania. Spróbuj przeformułować lub użyj prostszych słów."
        )


class LLMTimeoutError(GeoAsystentException):
    """Raised when LLM request times out."""
    
    def __init__(self, timeout_seconds: int, operation: str):
        details = {
            "timeout_seconds": timeout_seconds,
            "operation": operation
        }
        
        super().__init__(
            message=f"LLM request timed out after {timeout_seconds} seconds during operation: {operation}",
            code=ErrorCode.LLM_TIMEOUT_ERROR,
            details=details,
            user_message=f"Zapytanie do AI przekroczyło limit czasu ({timeout_seconds}s). Spróbuj ponownie."
        )


class LLMAPIKeyError(GeoAsystentException):
    """Raised when LLM API key is missing or invalid."""
    
    def __init__(self, service_name: str = "Groq"):
        details = {"service_name": service_name}
        
        super().__init__(
            message=f"LLM API key is missing or invalid for service: {service_name}",
            code=ErrorCode.LLM_API_KEY_ERROR,
            details=details,
            user_message="Błąd autoryzacji usługi AI. Skontaktuj się z administratorem systemu."
        )