"""Error handling middleware for FastAPI."""

import logging
from typing import Union
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from pydantic import ValidationError

from exceptions import GeoAsystentException, ErrorCode
from config import get_settings

logger = logging.getLogger(__name__)


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up all exception handlers for the FastAPI application."""
    
    settings = get_settings()
    
    @app.exception_handler(GeoAsystentException)
    async def handle_geoasystent_exception(request: Request, exc: GeoAsystentException) -> JSONResponse:
        """Handle custom GeoAsystent exceptions."""
        logger.error(
            f"GeoAsystent exception: {exc.code} - {exc.message}",
            extra={
                "error_code": exc.code,
                "error_details": exc.details,
                "request_url": str(request.url),
                "request_method": request.method
            }
        )
        
        # Return debug info in development mode
        response_data = exc.to_dict_debug() if settings.api.debug else exc.to_dict()
        
        # Determine HTTP status code based on error type
        status_code = _get_http_status_code(exc.code)
        
        return JSONResponse(
            status_code=status_code,
            content=response_data
        )
    
    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle Pydantic validation errors."""
        logger.warning(
            f"Validation error: {exc}",
            extra={
                "validation_errors": exc.errors(),
                "request_url": str(request.url),
                "request_method": request.method
            }
        )
        
        # Create user-friendly error message
        error_details = []
        for error in exc.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            error_details.append(f"{field}: {error['msg']}")
        
        response_data = {
            "error": {
                "code": ErrorCode.VALIDATION_ERROR,
                "message": "Dane wejściowe są nieprawidłowe.",
                "details": {
                    "validation_errors": error_details if settings.api.debug else ["Sprawdź format danych wejściowych."]
                }
            }
        }
        
        return JSONResponse(
            status_code=422,
            content=response_data
        )
    
    @app.exception_handler(HTTPException)
    async def handle_http_exception(request: Request, exc: HTTPException) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        logger.warning(
            f"HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "request_url": str(request.url),
                "request_method": request.method
            }
        )
        
        response_data = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": _get_user_friendly_http_message(exc.status_code, exc.detail),
                "details": {"http_detail": exc.detail} if settings.api.debug else {}
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def handle_starlette_http_exception(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle Starlette HTTP exceptions."""
        logger.warning(
            f"Starlette HTTP exception: {exc.status_code} - {exc.detail}",
            extra={
                "status_code": exc.status_code,
                "request_url": str(request.url),
                "request_method": request.method
            }
        )
        
        response_data = {
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": _get_user_friendly_http_message(exc.status_code, exc.detail),
                "details": {"http_detail": exc.detail} if settings.api.debug else {}
            }
        }
        
        return JSONResponse(
            status_code=exc.status_code,
            content=response_data
        )
    
    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception) -> JSONResponse:
        """Handle all other unhandled exceptions."""
        logger.error(
            f"Unhandled exception: {type(exc).__name__} - {str(exc)}",
            extra={
                "exception_type": type(exc).__name__,
                "request_url": str(request.url),
                "request_method": request.method
            },
            exc_info=True
        )
        
        response_data = {
            "error": {
                "code": ErrorCode.INTERNAL_SERVER_ERROR,
                "message": "Wystąpił nieoczekiwany błąd serwera. Spróbuj ponownie później.",
                "details": {
                    "exception_type": type(exc).__name__,
                    "exception_message": str(exc)
                } if settings.api.debug else {}
            }
        }
        
        return JSONResponse(
            status_code=500,
            content=response_data
        )


def _get_http_status_code(error_code: ErrorCode) -> int:
    """Map error codes to HTTP status codes."""
    status_mapping = {
        ErrorCode.VALIDATION_ERROR: 400,
        ErrorCode.LAYER_NOT_FOUND: 404,
        ErrorCode.INVALID_LAYER_NAME: 400,
        ErrorCode.DATABASE_CONNECTION_ERROR: 503,
        ErrorCode.LLM_API_KEY_ERROR: 503,
        ErrorCode.LLM_TIMEOUT_ERROR: 504,
        ErrorCode.CONFIGURATION_ERROR: 500,
        ErrorCode.GIS_DATA_PROCESSING_ERROR: 500,
        ErrorCode.SPATIAL_QUERY_ERROR: 500,
        ErrorCode.LLM_SERVICE_ERROR: 500,
        ErrorCode.INTENT_CLASSIFICATION_ERROR: 400,
        ErrorCode.INTERNAL_SERVER_ERROR: 500,
    }
    return status_mapping.get(error_code, 500)


def _get_user_friendly_http_message(status_code: int, detail: Union[str, None]) -> str:
    """Get user-friendly message for HTTP status codes."""
    messages = {
        400: "Nieprawidłowe żądanie.",
        401: "Brak autoryzacji.",
        403: "Brak uprawnień.",
        404: "Nie znaleziono zasobu.",
        405: "Metoda nie jest dozwolona.",
        422: "Dane wejściowe są nieprawidłowe.",
        429: "Zbyt wiele żądań. Spróbuj ponownie później.",
        500: "Błąd wewnętrzny serwera.",
        502: "Błąd bramy.",
        503: "Usługa niedostępna.",
        504: "Przekroczono limit czasu.",
    }
    
    user_message = messages.get(status_code, "Wystąpił błąd.")
    
    # Add detail if it's user-friendly
    if detail and isinstance(detail, str) and len(detail) < 100:
        user_message += f" {detail}"
    
    return user_message