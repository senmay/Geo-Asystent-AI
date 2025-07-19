"""
Utility functions for testing.
"""

import json
import tempfile
import os
from typing import Dict, Any, List, Optional
from unittest.mock import Mock, MagicMock
from datetime import datetime, timedelta
import random
import string

from shapely.geometry import Point, Polygon, LineString
from geopandas import GeoDataFrame
import pandas as pd


# ============================================================================
# Data Generation Utilities
# ============================================================================

def generate_random_string(length: int = 10) -> str:
    """Generate a random string of specified length."""
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))


def generate_random_coordinates(count: int = 1, bbox: tuple = (20.0, 51.0, 22.0, 53.0)) -> List[tuple]:
    """Generate random coordinates within a bounding box."""
    min_lon, min_lat, max_lon, max_lat = bbox
    coordinates = []
    for _ in range(count):
        lon = random.uniform(min_lon, max_lon)
        lat = random.uniform(min_lat, max_lat)
        coordinates.append((lon, lat))
    return coordinates


def generate_sample_points(count: int = 5, bbox: tuple = (20.0, 51.0, 22.0, 53.0)) -> List[Point]:
    """Generate sample Point geometries."""
    coords = generate_random_coordinates(count, bbox)
    return [Point(lon, lat) for lon, lat in coords]


def generate_sample_polygons(count: int = 3, bbox: tuple = (20.0, 51.0, 22.0, 53.0)) -> List[Polygon]:
    """Generate sample Polygon geometries."""
    polygons = []
    min_lon, min_lat, max_lon, max_lat = bbox
    
    for _ in range(count):
        # Generate a simple square polygon
        center_lon = random.uniform(min_lon + 0.1, max_lon - 0.1)
        center_lat = random.uniform(min_lat + 0.1, max_lat - 0.1)
        size = random.uniform(0.01, 0.05)
        
        coords = [
            (center_lon - size, center_lat - size),
            (center_lon + size, center_lat - size),
            (center_lon + size, center_lat + size),
            (center_lon - size, center_lat + size),
            (center_lon - size, center_lat - size)  # Close the polygon
        ]
        polygons.append(Polygon(coords))
    
    return polygons


def generate_sample_geojson(feature_count: int = 5, geometry_type: str = "Point") -> Dict[str, Any]:
    """Generate sample GeoJSON data."""
    features = []
    
    for i in range(feature_count):
        if geometry_type == "Point":
            coords = generate_random_coordinates(1)[0]
            geometry = {"type": "Point", "coordinates": list(coords)}
        elif geometry_type == "Polygon":
            polygons = generate_sample_polygons(1)
            coords = list(polygons[0].exterior.coords)
            geometry = {"type": "Polygon", "coordinates": [coords]}
        else:
            raise ValueError(f"Unsupported geometry type: {geometry_type}")
        
        feature = {
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "id": i + 1,
                "name": f"Feature {i + 1}",
                "description": f"Test {geometry_type} feature",
                "created_at": datetime.now().isoformat()
            }
        }
        features.append(feature)
    
    return {
        "type": "FeatureCollection",
        "features": features
    }


def generate_sample_geodataframe(feature_count: int = 5, geometry_type: str = "Point") -> GeoDataFrame:
    """Generate sample GeoDataFrame."""
    if geometry_type == "Point":
        geometries = generate_sample_points(feature_count)
    elif geometry_type == "Polygon":
        geometries = generate_sample_polygons(feature_count)
    else:
        raise ValueError(f"Unsupported geometry type: {geometry_type}")
    
    data = {
        'id': range(1, feature_count + 1),
        'name': [f'Feature {i}' for i in range(1, feature_count + 1)],
        'geometry': geometries
    }
    
    if geometry_type == "Polygon":
        data['area'] = [geom.area for geom in geometries]
    
    return GeoDataFrame(data, crs='EPSG:4326')


# ============================================================================
# Mock Utilities
# ============================================================================

def create_mock_llm_response(content: str, intent: str = None, confidence: float = 0.9) -> Mock:
    """Create a mock LLM response."""
    mock_response = Mock()
    mock_response.content = content
    if intent:
        mock_response.intent = intent
        mock_response.confidence = confidence
    return mock_response


def create_mock_database_result(data: List[Dict[str, Any]]) -> Mock:
    """Create a mock database query result."""
    mock_result = Mock()
    mock_result.fetchall.return_value = data
    mock_result.rowcount = len(data)
    return mock_result


def create_mock_gis_repository(layer_data: Dict[str, Any] = None) -> Mock:
    """Create a mock GIS repository with sample data."""
    from repositories.gis_repository import GISRepository
    
    mock_repo = Mock(spec=GISRepository)
    
    # Default sample data
    if layer_data is None:
        layer_data = generate_sample_geojson()
    
    mock_repo.get_layer_as_geojson.return_value = layer_data
    mock_repo.get_available_layers.return_value = [
        {"name": "buildings", "table_name": "buildings_low", "geometry_type": "Polygon"},
        {"name": "parcels", "table_name": "parcels_low", "geometry_type": "Polygon"},
        {"name": "gpz_110kv", "table_name": "gpz_110kv_low", "geometry_type": "Point"}
    ]
    mock_repo.get_layer_statistics.return_value = {
        "feature_count": len(layer_data.get("features", [])),
        "geometry_type": "Point",
        "bbox": [20.0, 51.0, 22.0, 53.0]
    }
    
    return mock_repo


def create_mock_intent_service(default_intent: str = "get_gis_data") -> Mock:
    """Create a mock intent service."""
    from services.intent_service import IntentService
    
    mock_service = Mock(spec=IntentService)
    mock_service.classify_query.return_value = {
        "intent": default_intent,
        "parameters": {"layer_name": "buildings"},
        "confidence": 0.9
    }
    
    return mock_service


# ============================================================================
# File Utilities
# ============================================================================

def create_temp_geojson_file(geojson_data: Dict[str, Any]) -> str:
    """Create a temporary GeoJSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as f:
        json.dump(geojson_data, f)
        return f.name


def create_temp_config_file(config_data: Dict[str, Any]) -> str:
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(config_data, f)
        return f.name


def cleanup_temp_files(file_paths: List[str]):
    """Clean up temporary files."""
    for file_path in file_paths:
        if os.path.exists(file_path):
            os.unlink(file_path)


# ============================================================================
# Assertion Utilities
# ============================================================================

def assert_geojson_structure(geojson: Dict[str, Any], expected_feature_count: int = None):
    """Assert GeoJSON has correct structure."""
    assert isinstance(geojson, dict), "GeoJSON must be a dictionary"
    assert geojson.get("type") == "FeatureCollection", "Must be a FeatureCollection"
    assert "features" in geojson, "Must have features"
    assert isinstance(geojson["features"], list), "Features must be a list"
    
    if expected_feature_count is not None:
        assert len(geojson["features"]) == expected_feature_count, \
            f"Expected {expected_feature_count} features, got {len(geojson['features'])}"
    
    for feature in geojson["features"]:
        assert_feature_structure(feature)


def assert_feature_structure(feature: Dict[str, Any]):
    """Assert GeoJSON feature has correct structure."""
    assert isinstance(feature, dict), "Feature must be a dictionary"
    assert feature.get("type") == "Feature", "Feature type must be 'Feature'"
    assert "geometry" in feature, "Feature must have geometry"
    assert "properties" in feature, "Feature must have properties"
    
    geometry = feature["geometry"]
    assert isinstance(geometry, dict), "Geometry must be a dictionary"
    assert "type" in geometry, "Geometry must have type"
    assert "coordinates" in geometry, "Geometry must have coordinates"


def assert_api_error_response(response_data: Dict[str, Any], expected_status: int = None):
    """Assert API error response structure."""
    assert "error" in response_data, "Response must contain error"
    error = response_data["error"]
    assert "message" in error, "Error must have message"
    
    if expected_status:
        assert "status" in error, "Error must have status"
        assert error["status"] == expected_status


def assert_coordinates_in_bbox(coordinates: List[float], bbox: tuple):
    """Assert coordinates are within bounding box."""
    lon, lat = coordinates
    min_lon, min_lat, max_lon, max_lat = bbox
    assert min_lon <= lon <= max_lon, f"Longitude {lon} not in range [{min_lon}, {max_lon}]"
    assert min_lat <= lat <= max_lat, f"Latitude {lat} not in range [{min_lat}, {max_lat}]"


# ============================================================================
# Performance Utilities
# ============================================================================

def measure_execution_time(func, *args, **kwargs) -> tuple:
    """Measure function execution time."""
    import time
    start_time = time.time()
    result = func(*args, **kwargs)
    execution_time = time.time() - start_time
    return result, execution_time


def assert_execution_time_under(func, max_seconds: float, *args, **kwargs):
    """Assert function executes within time limit."""
    result, execution_time = measure_execution_time(func, *args, **kwargs)
    assert execution_time <= max_seconds, \
        f"Execution took {execution_time:.2f}s, expected <= {max_seconds}s"
    return result


# ============================================================================
# Database Utilities
# ============================================================================

def create_test_tables(engine):
    """Create test tables in database."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        # Create test tables with sample data
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_buildings (
                id INTEGER PRIMARY KEY,
                name TEXT,
                height REAL,
                geometry TEXT
            )
        """))
        
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS test_parcels (
                id INTEGER PRIMARY KEY,
                area REAL,
                owner TEXT,
                geometry TEXT
            )
        """))
        
        conn.commit()


def insert_test_data(engine, table_name: str, data: List[Dict[str, Any]]):
    """Insert test data into table."""
    from sqlalchemy import text
    
    if not data:
        return
    
    # Build INSERT statement
    columns = list(data[0].keys())
    placeholders = ', '.join([f':{col}' for col in columns])
    sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({placeholders})"
    
    with engine.connect() as conn:
        for row in data:
            conn.execute(text(sql), row)
        conn.commit()


def cleanup_test_tables(engine, table_names: List[str]):
    """Clean up test tables."""
    from sqlalchemy import text
    
    with engine.connect() as conn:
        for table_name in table_names:
            conn.execute(text(f"DROP TABLE IF EXISTS {table_name}"))
        conn.commit()


# ============================================================================
# Environment Utilities
# ============================================================================

def set_test_env_vars(env_vars: Dict[str, str]):
    """Set environment variables for testing."""
    for key, value in env_vars.items():
        os.environ[key] = value


def restore_env_vars(original_vars: Dict[str, Optional[str]]):
    """Restore original environment variables."""
    for key, value in original_vars.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


def get_test_database_url() -> str:
    """Get test database URL."""
    return os.getenv("TEST_DATABASE_URL", "sqlite:///./test.db")