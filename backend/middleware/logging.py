"""Logging middleware for FastAPI."""

import logging
import time
import uuid
from typing import Callable
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from config import get_settings

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    def __init__(self, app, settings=None):
        super().__init__(app)
        self.settings = settings or get_settings()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())[:8]
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "url": str(request.url),
                "client_ip": request.client.host if request.client else "unknown",
                "user_agent": request.headers.get("user-agent", "unknown")
            }
        )
        
        # Add request ID to request state for use in other parts of the application
        request.state.request_id = request_id
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"[{request_id}] {response.status_code} - {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                    "response_size": response.headers.get("content-length", "unknown")
                }
            )
            
            # Add request ID to response headers for debugging
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                f"[{request_id}] Request failed - {process_time:.3f}s - {type(e).__name__}: {str(e)}",
                extra={
                    "request_id": request_id,
                    "process_time": process_time,
                    "exception_type": type(e).__name__,
                    "exception_message": str(e)
                },
                exc_info=True
            )
            
            # Re-raise the exception to be handled by error handlers
            raise


def setup_logging_middleware(app: FastAPI) -> None:
    """Set up logging middleware for the FastAPI application."""
    settings = get_settings()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, settings.logging.level.upper()),
        format=settings.logging.format,
        handlers=[
            logging.StreamHandler(),
            *([logging.FileHandler(settings.logging.file_path)] if settings.logging.file_path else [])
        ]
    )
    
    # Add request/response logging middleware
    app.add_middleware(LoggingMiddleware, settings=settings)
    
    # Log application startup
    logger.info(
        f"Starting {settings.app_name} v{settings.app_version}",
        extra={
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug_mode": settings.api.debug,
            "log_level": settings.logging.level
        }
    )