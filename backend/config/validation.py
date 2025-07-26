"""Configuration validation utilities."""

import sys
import logging
from typing import List, Tuple
from .settings import get_settings

logger = logging.getLogger(__name__)


def validate_configuration() -> Tuple[bool, List[str]]:
    """
    Validate application configuration.
    
    Returns:
        Tuple of (is_valid, error_messages)
    """
    errors = []
    
    try:
        settings = get_settings()
        
        # Validate database settings
        if not settings.database.user:
            errors.append("Database user (DB_USER) is required")
        if not settings.database.password:
            errors.append("Database password (DB_PASSWORD) is required")
        if not settings.database.host:
            errors.append("Database host (DB_HOST) is required")
        if not settings.database.name:
            errors.append("Database name (DB_NAME) is required")
            
        # Validate LLM settings
        if settings.llm.api_key is None:
            errors.append("LLM API key (GROQ_API_KEY) is recommended for production")
            
        # Validate API settings
        if not settings.api.cors_origins:
            errors.append("CORS origins should be configured for security")
            
        # Test database URL generation
        try:
            db_url = settings.database.url
            if not db_url.startswith("postgresql://"):
                errors.append("Invalid database URL format")
        except Exception as e:
            errors.append(f"Error generating database URL: {e}")
            
    except Exception as e:
        errors.append(f"Configuration loading error: {e}")
    
    return len(errors) == 0, errors


def print_configuration_summary():
    """Print a summary of current configuration."""
    try:
        settings = get_settings()
        
        logger.info("=== Geo-Asystent AI Configuration Summary ===", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"App Name: {settings.app_name}", extra={
            'operation': 'configuration_summary',
            'app_name': settings.app_name,
            'app_version': settings.app_version
        })
        logger.info(f"App Version: {settings.app_version}", extra={
            'operation': 'configuration_summary',
            'app_version': settings.app_version
        })
        logger.info(f"Debug Mode: {settings.api.debug}", extra={
            'operation': 'configuration_summary',
            'debug_mode': settings.api.debug
        })
        
        logger.info("Database Configuration:", extra={
            'operation': 'configuration_summary',
            'db_host': settings.database.host,
            'db_port': settings.database.port,
            'db_name': settings.database.name,
            'db_user': settings.database.user
        })
        logger.info(f"  Host: {settings.database.host}:{settings.database.port}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  Database: {settings.database.name}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  User: {settings.database.user}", extra={
            'operation': 'configuration_summary'
        })
        
        logger.info("LLM Configuration:", extra={
            'operation': 'configuration_summary',
            'llm_model': settings.llm.model,
            'llm_temperature': settings.llm.temperature,
            'llm_api_key_set': bool(settings.llm.api_key)
        })
        logger.info(f"  Model: {settings.llm.model}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  Temperature: {settings.llm.temperature}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  API Key: {'Set' if settings.llm.api_key else 'Not set'}", extra={
            'operation': 'configuration_summary'
        })
        
        logger.info("API Configuration:", extra={
            'operation': 'configuration_summary',
            'api_host': settings.api.host,
            'api_port': settings.api.port,
            'cors_origins_count': len(settings.api.cors_origins)
        })
        logger.info(f"  Host: {settings.api.host}:{settings.api.port}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  CORS Origins: {', '.join(settings.api.cors_origins)}", extra={
            'operation': 'configuration_summary'
        })
        
        logger.info("GIS Configuration:", extra={
            'operation': 'configuration_summary',
            'gis_default_crs': settings.gis.default_crs,
            'gis_max_features': settings.gis.max_features
        })
        logger.info(f"  Default CRS: {settings.gis.default_crs}", extra={
            'operation': 'configuration_summary'
        })
        logger.info(f"  Max Features: {settings.gis.max_features}", extra={
            'operation': 'configuration_summary'
        })
        
        is_valid, errors = validate_configuration()
        if is_valid:
            logger.info("✅ Configuration is valid!", extra={
                'operation': 'configuration_validation',
                'is_valid': True
            })
        else:
            logger.warning("❌ Configuration issues found:", extra={
                'operation': 'configuration_validation',
                'is_valid': False,
                'error_count': len(errors)
            })
            for error in errors:
                logger.warning(f"  - {error}", extra={
                    'operation': 'configuration_validation',
                    'validation_error': error
                })
                
    except Exception as e:
        logger.error(f"Error loading configuration: {e}", extra={
            'operation': 'configuration_summary',
            'error_type': type(e).__name__
        })


if __name__ == "__main__":
    print_configuration_summary()