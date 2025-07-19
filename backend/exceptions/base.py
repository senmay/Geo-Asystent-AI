"""Base exception classes for Geo-Asystent AI."""

from enum import Enum
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorCode(str, Enum):
    """Standardized error codes for the application."""
    
    # General errors
    INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    
    # GIS errors
    LAYER_NOT_FOUND = "LAYER_NOT_FOUND"
    INVALID_LAYER_NAME = "INVALID_LAYER_NAME"
    GIS_DATA_PROCESSING_ERROR = "GIS_DATA_PROCESSING_ERROR"
    DATABASE_CONNECTION_ERROR = "DATABASE_CONNECTION_ERROR"
    SPATIAL_QUERY_ERROR = "SPATIAL_QUERY_ERROR"
    
    # LLM errors
    LLM_SERVICE_ERROR = "LLM_SERVICE_ERROR"
    INTENT_CLASSIFICATION_ERROR = "INTENT_CLASSIFICATION_ERROR"
    LLM_TIMEOUT_ERROR = "LLM_TIMEOUT_ERROR"
    LLM_API_KEY_ERROR = "LLM_API_KEY_ERROR"


class GeoAsystentException(Exception):
    """Base exception class for all Geo-Asystent AI errors."""
    
    def __init__(
        self,
        message: str,
        code: ErrorCode,
        details: Optional[Dict[str, Any]] = None,
        user_message: Optional[str] = None,
        log_level: int = logging.ERROR
    ):
        """
        Initialize the exception.
        
        Args:
            message: Technical error message for developers
            code: Standardized error code
            details: Additional error details and context
            user_message: User-friendly error message (optional)
            log_level: Logging level for this error
        """
        super().__init__(message)
        self.message = message
        self.code = code
        self.details = details or {}
        self.user_message = user_message or self._get_default_user_message()
        self.log_level = log_level
        
        # Log the error when it's created
        logger.log(
            self.log_level,
            f"[{self.code}] {self.message}",
            extra={"error_details": self.details}
        )
    
    def _get_default_user_message(self) -> str:
        """Get default user-friendly message based on error code."""
        user_messages = {
            ErrorCode.INTERNAL_SERVER_ERROR: "Wystąpił błąd wewnętrzny serwera. Spróbuj ponownie później.",
            ErrorCode.VALIDATION_ERROR: "Dane wejściowe są nieprawidłowe. Sprawdź format zapytania.",
            ErrorCode.CONFIGURATION_ERROR: "Błąd konfiguracji aplikacji. Skontaktuj się z administratorem.",
            ErrorCode.LAYER_NOT_FOUND: "Nie znaleziono żądanej warstwy danych.",
            ErrorCode.INVALID_LAYER_NAME: "Nieprawidłowa nazwa warstwy. Spróbuj 'działki' lub 'budynki'.",
            ErrorCode.GIS_DATA_PROCESSING_ERROR: "Błąd podczas przetwarzania danych GIS.",
            ErrorCode.DATABASE_CONNECTION_ERROR: "Błąd połączenia z bazą danych. Spróbuj ponownie później.",
            ErrorCode.SPATIAL_QUERY_ERROR: "Błąd podczas wykonywania zapytania przestrzennego.",
            ErrorCode.LLM_SERVICE_ERROR: "Błąd usługi AI. Spróbuj ponownie później.",
            ErrorCode.INTENT_CLASSIFICATION_ERROR: "Nie udało się zrozumieć zapytania. Spróbuj przeformułować.",
            ErrorCode.LLM_TIMEOUT_ERROR: "Zapytanie do AI przekroczyło limit czasu. Spróbuj ponownie.",
            ErrorCode.LLM_API_KEY_ERROR: "Błąd autoryzacji usługi AI. Skontaktuj się z administratorem.",
        }
        return user_messages.get(self.code, "Wystąpił nieoczekiwany błąd.")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API responses."""
        return {
            "error": {
                "code": self.code,
                "message": self.user_message,
                "details": self.details
            }
        }
    
    def to_dict_debug(self) -> Dict[str, Any]:
        """Convert exception to dictionary with debug information."""
        return {
            "error": {
                "code": self.code,
                "message": self.user_message,
                "technical_message": self.message,
                "details": self.details
            }
        }