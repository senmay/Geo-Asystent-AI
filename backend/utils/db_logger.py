"""Database operation logging utilities."""

import logging
import time
from typing import Optional, Dict, Any
from functools import wraps
from contextlib import contextmanager

logger = logging.getLogger(__name__)


@contextmanager
def log_database_operation(operation: str, table: Optional[str] = None, **kwargs):
    """
    Context manager for logging database operations.
    
    Args:
        operation: Description of the database operation
        table: Table name being accessed (optional)
        **kwargs: Additional context information
    """
    start_time = time.time()
    
    # Log operation start
    logger.debug(
        f"Starting database operation: {operation}",
        extra={
            "db_operation": operation,
            "table": table,
            "operation_context": kwargs
        }
    )
    
    try:
        yield
        
        # Log successful completion
        duration = time.time() - start_time
        logger.info(
            f"Database operation completed: {operation} - {duration:.3f}s",
            extra={
                "db_operation": operation,
                "table": table,
                "duration": duration,
                "success": True,
                "operation_context": kwargs
            }
        )
        
        # Log slow database operations
        if duration > 2.0:  # Log operations taking more than 2 seconds
            logger.warning(
                f"Slow database operation: {operation} - {duration:.3f}s",
                extra={
                    "slow_db_operation": True,
                    "db_operation": operation,
                    "table": table,
                    "duration": duration,
                    "operation_context": kwargs
                }
            )
            
    except Exception as e:
        # Log operation failure
        duration = time.time() - start_time
        logger.error(
            f"Database operation failed: {operation} - {duration:.3f}s - {type(e).__name__}: {str(e)}",
            extra={
                "db_operation": operation,
                "table": table,
                "duration": duration,
                "success": False,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "operation_context": kwargs
            },
            exc_info=True
        )
        raise


def log_gis_operation(operation_type: str):
    """
    Decorator for logging GIS operations.
    
    Args:
        operation_type: Type of GIS operation (e.g., 'layer_retrieval', 'spatial_query')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            # Extract relevant parameters for logging
            log_context = {
                "function": func.__name__,
                "operation_type": operation_type
            }
            
            # Try to extract common parameters
            if 'layer_name' in kwargs:
                log_context['layer_name'] = kwargs['layer_name']
            if 'n' in kwargs:
                log_context['limit'] = kwargs['n']
            if 'min_area' in kwargs:
                log_context['min_area'] = kwargs['min_area']
            if 'radius_meters' in kwargs:
                log_context['radius_meters'] = kwargs['radius_meters']
            
            logger.info(
                f"Starting GIS operation: {operation_type}",
                extra=log_context
            )
            
            try:
                result = func(*args, **kwargs)
                
                # Log successful completion
                duration = time.time() - start_time
                logger.info(
                    f"GIS operation completed: {operation_type} - {duration:.3f}s",
                    extra={
                        **log_context,
                        "duration": duration,
                        "success": True
                    }
                )
                
                return result
                
            except Exception as e:
                # Log operation failure
                duration = time.time() - start_time
                logger.error(
                    f"GIS operation failed: {operation_type} - {duration:.3f}s - {type(e).__name__}: {str(e)}",
                    extra={
                        **log_context,
                        "duration": duration,
                        "success": False,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    },
                    exc_info=True
                )
                raise
                
        return wrapper
    return decorator


class LLMOperationLogger:
    """Logger for LLM operations with fallback mechanisms."""
    
    @staticmethod
    def log_intent_classification(query: str, intent: str, confidence: Optional[float] = None, duration: Optional[float] = None):
        """Log intent classification results."""
        logger.info(
            f"Intent classified: '{query}' -> {intent}",
            extra={
                "llm_operation": "intent_classification",
                "query": query,
                "classified_intent": intent,
                "confidence": confidence,
                "duration": duration
            }
        )
    
    @staticmethod
    def log_chat_response(query: str, response_length: int, duration: Optional[float] = None):
        """Log chat response generation."""
        logger.info(
            f"Chat response generated: {response_length} characters",
            extra={
                "llm_operation": "chat_response",
                "query": query,
                "response_length": response_length,
                "duration": duration
            }
        )
    
    @staticmethod
    def log_llm_fallback(operation: str, error: Exception, fallback_used: str):
        """Log when LLM fallback mechanisms are used."""
        logger.warning(
            f"LLM fallback triggered for {operation}: {fallback_used}",
            extra={
                "llm_operation": operation,
                "fallback_mechanism": fallback_used,
                "original_error": str(error),
                "error_type": type(error).__name__
            }
        )