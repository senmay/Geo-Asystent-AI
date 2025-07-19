"""Centralized configuration management using Pydantic BaseSettings."""

from functools import lru_cache
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseModel):
    """Database configuration settings."""
    
    host: str
    port: int
    name: str
    user: str
    password: str
    
    @property
    def url(self) -> str:
        """Generate database URL from components."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class LLMSettings(BaseModel):
    """LLM service configuration settings."""
    
    model: str
    temperature: float
    api_key: Optional[str]
    timeout: int
    max_retries: int


class APISettings(BaseModel):
    """API server configuration settings."""
    
    host: str
    port: int
    cors_origins: List[str]
    debug: bool


class LoggingSettings(BaseModel):
    """Logging configuration settings."""
    
    level: str
    format: str
    file_path: Optional[str]


class GISSettings(BaseModel):
    """GIS-specific configuration settings."""
    
    default_crs: str
    max_features: int
    buffer_default_radius: float


class Settings(BaseSettings):
    """Main application settings."""
    
    # Application info
    app_name: str = Field("Geo-Asystent AI", description="Application name")
    app_version: str = Field("1.0.0", description="Application version")
    app_description: str = Field("Backend for the GIS AI Assistant", description="Application description")
    
    # Database settings
    db_host: str = Field(..., env="DB_HOST", description="Database host")
    db_port: int = Field(5432, env="DB_PORT", description="Database port")
    db_name: str = Field(..., env="DB_NAME", description="Database name")
    db_user: str = Field(..., env="DB_USER", description="Database user")
    db_password: str = Field(..., env="DB_PASSWORD", description="Database password")
    
    # LLM settings
    llm_model: str = Field("llama3-8b-8192", env="LLM_MODEL", description="LLM model name")
    llm_temperature: float = Field(0.0, env="LLM_TEMPERATURE", description="LLM temperature")
    groq_api_key: Optional[str] = Field(None, env="GROQ_API_KEY", description="Groq API key")
    llm_timeout: int = Field(30, env="LLM_TIMEOUT", description="LLM request timeout in seconds")
    llm_max_retries: int = Field(3, env="LLM_MAX_RETRIES", description="Maximum retry attempts")
    
    # API settings
    api_host: str = Field("127.0.0.1", env="API_HOST", description="API server host")
    api_port: int = Field(8000, env="API_PORT", description="API server port")
    cors_origins: List[str] = Field(
        ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"],
        env="CORS_ORIGINS",
        description="Allowed CORS origins"
    )
    debug: bool = Field(False, env="DEBUG", description="Enable debug mode")
    
    # Logging settings
    log_level: str = Field("INFO", env="LOG_LEVEL", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT",
        description="Log message format"
    )
    log_file: Optional[str] = Field(None, env="LOG_FILE", description="Log file path")
    
    # GIS settings
    default_crs: str = Field("EPSG:4326", env="DEFAULT_CRS", description="Default coordinate reference system")
    max_features: int = Field(10000, env="MAX_FEATURES", description="Maximum features to return in queries")
    buffer_default_radius: float = Field(1000.0, env="BUFFER_DEFAULT_RADIUS", description="Default buffer radius in meters")
    
    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def database(self) -> DatabaseSettings:
        """Get database settings."""
        return DatabaseSettings(
            host=self.db_host,
            port=self.db_port,
            name=self.db_name,
            user=self.db_user,
            password=self.db_password
        )
    
    @property
    def llm(self) -> LLMSettings:
        """Get LLM settings."""
        return LLMSettings(
            model=self.llm_model,
            temperature=self.llm_temperature,
            api_key=self.groq_api_key,
            timeout=self.llm_timeout,
            max_retries=self.llm_max_retries
        )
    
    @property
    def api(self) -> APISettings:
        """Get API settings."""
        return APISettings(
            host=self.api_host,
            port=self.api_port,
            cors_origins=self.cors_origins,
            debug=self.debug
        )
    
    @property
    def logging(self) -> LoggingSettings:
        """Get logging settings."""
        return LoggingSettings(
            level=self.log_level,
            format=self.log_format,
            file_path=self.log_file
        )
    
    @property
    def gis(self) -> GISSettings:
        """Get GIS settings."""
        return GISSettings(
            default_crs=self.default_crs,
            max_features=self.max_features,
            buffer_default_radius=self.buffer_default_radius
        )
    
    model_config = {
        "env_file": Path(__file__).parent.parent.parent / ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields in .env file
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()