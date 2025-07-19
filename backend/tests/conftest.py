"""
Test configuration and fixtures for the backend application.
"""

import os
import pytest
import tempfile
from typing import Generator, Dict, Any
from unittest.mock import Mock, MagicMock
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient
from geopandas import GeoDataFrame
import pandas as pd
from shapely.geometry import Point, Polygon

# Import application modules
from main import app
from config.settings import get_settings
from repositories.base import BaseRepository
from repositories.gis_repository import GISRepository
from services.gis_service import GISService
from services.intent_service import IntentClassificationService
from services.llm_service import LLMService


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def test_db_url() -> str:
    """Create a test database URL."""
    return "sqlite:///./test.db"


@pytest.fixture(scope="session")
def test_engine(test_db_url: str) -> Generator[Engine, None, None]:
    """Create a test database engine."""
    engine = create_engine(
        test_db_url,
        connect_args={"check_same_thread": False}  # For SQLite
    )
    yield engine
    engine.dispose()


@pytest.fixture(scope="function")
def test_session(test_engine: Engine) -> Generator[Session, None, None]:
    """Create a test database session."""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def test_db_with_sample_data(test_engine: Engine) -> Generator[Engine, None, None]:
    """Create a test database with sample GIS data."""
    # Create sample tables and data
    with test_engine.connect() as conn:
        # Create sample buildings table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS buildings_low (
                id INTEGER PRIMARY KEY,
                name TEXT,
                geometry TEXT
            )
        """))
        
        # Create sample parcels table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS parcels_low (
                id INTEGER PRIMARY KEY,
                area REAL,
                geometry TEXT
            )
        """))
        
        # Create sample GPZ table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS gpz_110kv_low (
                id INTEGER PRIMARY KEY,
                name TEXT,
                voltage INTEGER,
                geometry TEXT
            )
        """))
        
        # Insert sample data
        conn.execute(text("""
            INSERT INTO buildings_low (id, name, geometry) VALUES
            (1, 'Building 1', 'POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))'),
            (2, 'Building 2', 'POLYGON((2 2, 3 2, 3 3, 2 3, 2 2))')
        """))
        
        conn.execute(text("""
            INSERT INTO parcels_low (id, area, geometry) VALUES
            (1, 100.5, 'POLYGON((0 0, 2 0, 2 2, 0 2, 0 0))'),
            (2, 200.0, 'POLYGON((3 3, 5 3, 5 5, 3 5, 3 3))')
        """))
        
        conn.execute(text("""
            INSERT INTO gpz_110kv_low (id, name, voltage, geometry) VALUES
            (1, 'GPZ Station 1', 110, 'POINT(1 1)'),
            (2, 'GPZ Station 2', 110, 'POINT(4 4)')
        """))
        
        conn.commit()
    
    yield test_engine
    
    # Cleanup
    with test_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS buildings_low"))
        conn.execute(text("DROP TABLE IF EXISTS parcels_low"))
        conn.execute(text("DROP TABLE IF EXISTS gpz_110kv_low"))
        conn.commit()


# ============================================================================
# Repository Fixtures
# ============================================================================

@pytest.fixture
def mock_gis_repository() -> Mock:
    """Create a mock GIS repository."""
    mock_repo = Mock(spec=GISRepository)
    
    # Mock sample data
    sample_geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [1.0, 1.0]},
                "properties": {"id": 1, "name": "Test Feature"}
            }
        ]
    }
    
    mock_repo.get_layer_as_geojson.return_value = sample_geojson
    mock_repo.get_available_layers.return_value = [
        {"name": "buildings", "table_name": "buildings_low", "geometry_type": "Polygon"},
        {"name": "parcels", "table_name": "parcels_low", "geometry_type": "Polygon"}
    ]
    
    return mock_repo


@pytest.fixture
def gis_repository(test_session: Session) -> GISRepository:
    """Create a real GIS repository with test session."""
    return GISRepository(test_session)


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def mock_llm_service() -> Mock:
    """Create a mock LLM service."""
    mock_service = Mock(spec=LLMService)
    mock_service.classify_intent.return_value = {
        "intent": "get_gis_data",
        "layer_name": "buildings",
        "confidence": 0.9
    }
    mock_service.generate_response.return_value = "Test response from LLM"
    return mock_service


@pytest.fixture
def mock_intent_service() -> Mock:
    """Create a mock intent service."""
    mock_service = Mock(spec=IntentClassificationService)
    mock_service.classify_query.return_value = {
        "intent": "get_gis_data",
        "parameters": {"layer_name": "buildings"},
        "confidence": 0.9
    }
    return mock_service


@pytest.fixture
def gis_service(mock_gis_repository: Mock) -> GISService:
    """Create a GIS service with mocked repository."""
    return GISService(mock_gis_repository)


# ============================================================================
# API Fixtures
# ============================================================================

@pytest.fixture
def test_client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(test_client: TestClient) -> TestClient:
    """Create an authenticated test client (if authentication is implemented)."""
    # For now, return the same client since we don't have authentication
    return test_client


# ============================================================================
# Sample Data Fixtures
# ============================================================================

@pytest.fixture
def sample_geojson() -> Dict[str, Any]:
    """Create sample GeoJSON data."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [21.0, 52.0]
                },
                "properties": {
                    "id": 1,
                    "name": "Test Point",
                    "description": "A test point in Warsaw"
                }
            },
            {
                "type": "Feature",
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [20.9, 51.9],
                        [21.1, 51.9],
                        [21.1, 52.1],
                        [20.9, 52.1],
                        [20.9, 51.9]
                    ]]
                },
                "properties": {
                    "id": 2,
                    "name": "Test Polygon",
                    "area": 100.5
                }
            }
        ]
    }


@pytest.fixture
def sample_geodataframe() -> GeoDataFrame:
    """Create sample GeoDataFrame."""
    data = {
        'id': [1, 2, 3],
        'name': ['Feature 1', 'Feature 2', 'Feature 3'],
        'geometry': [
            Point(21.0, 52.0),
            Point(21.1, 52.1),
            Polygon([(20.9, 51.9), (21.1, 51.9), (21.1, 52.1), (20.9, 52.1)])
        ]
    }
    return GeoDataFrame(data, crs='EPSG:4326')


@pytest.fixture
def sample_chat_queries() -> Dict[str, Dict[str, Any]]:
    """Create sample chat queries for testing."""
    return {
        "gis_query": {
            "query": "Pokaż budynki",
            "expected_intent": "get_gis_data",
            "expected_layer": "buildings"
        },
        "chat_query": {
            "query": "Jak się masz?",
            "expected_intent": "chat",
            "expected_response_type": "text"
        },
        "analysis_query": {
            "query": "Znajdź największą działkę",
            "expected_intent": "find_largest_parcel",
            "expected_response_type": "geojson"
        }
    }


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def test_settings():
    """Create test settings."""
    settings = get_settings()
    # Override settings for testing
    settings.database_url = "sqlite:///./test.db"
    settings.llm_api_key = "test-api-key"
    settings.debug = True
    return settings


# ============================================================================
# Utility Fixtures
# ============================================================================

@pytest.fixture
def temp_file() -> Generator[str, None, None]:
    """Create a temporary file for testing."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def mock_logger() -> Mock:
    """Create a mock logger."""
    return Mock()


# ============================================================================
# Cleanup Fixtures
# ============================================================================

@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Automatically cleanup test files after each test."""
    yield
    # Cleanup any test files that might have been created
    test_files = ["test.db", "test.log"]
    for file in test_files:
        if os.path.exists(file):
            os.unlink(file)


# ============================================================================
# Parametrized Fixtures
# ============================================================================

@pytest.fixture(params=["buildings", "parcels", "gpz_110kv"])
def layer_name(request) -> str:
    """Parametrized fixture for different layer names."""
    return request.param


@pytest.fixture(params=[
    {"intent": "get_gis_data", "layer": "buildings"},
    {"intent": "chat", "layer": None},
    {"intent": "find_largest_parcel", "layer": "parcels"}
])
def intent_data(request) -> Dict[str, Any]:
    """Parametrized fixture for different intent scenarios."""
    return request.param