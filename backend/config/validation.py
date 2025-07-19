"""Configuration validation utilities."""

import sys
from typing import List, Tuple
from .settings import get_settings


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
        
        print("=== Geo-Asystent AI Configuration Summary ===")
        print(f"App Name: {settings.app_name}")
        print(f"App Version: {settings.app_version}")
        print(f"Debug Mode: {settings.api.debug}")
        print()
        
        print("Database Configuration:")
        print(f"  Host: {settings.database.host}:{settings.database.port}")
        print(f"  Database: {settings.database.name}")
        print(f"  User: {settings.database.user}")
        print()
        
        print("LLM Configuration:")
        print(f"  Model: {settings.llm.model}")
        print(f"  Temperature: {settings.llm.temperature}")
        print(f"  API Key: {'Set' if settings.llm.api_key else 'Not set'}")
        print()
        
        print("API Configuration:")
        print(f"  Host: {settings.api.host}:{settings.api.port}")
        print(f"  CORS Origins: {', '.join(settings.api.cors_origins)}")
        print()
        
        print("GIS Configuration:")
        print(f"  Default CRS: {settings.gis.default_crs}")
        print(f"  Max Features: {settings.gis.max_features}")
        print()
        
        is_valid, errors = validate_configuration()
        if is_valid:
            print("✅ Configuration is valid!")
        else:
            print("❌ Configuration issues found:")
            for error in errors:
                print(f"  - {error}")
                
    except Exception as e:
        print(f"Error loading configuration: {e}")


if __name__ == "__main__":
    print_configuration_summary()