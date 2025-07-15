import pytest
from sqlalchemy import create_engine
from tools.gis_tools import get_layer_as_geojson
import json
import os

# This mark tells pytest that this test needs a database connection to run.
# We can use it to run only unit tests or only integration tests.
@pytest.mark.integration
def test_get_layer_from_postgis():
    """
    Tests the get_layer_as_geojson tool by connecting to a real database.
    Requires the database to be running and data to be loaded.
    """
    # Arrange: Create a real database engine.
    # This assumes the same environment variables are available during testing.
    DB_USER = os.getenv("DB_USER")
    DB_PASS = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST")
    DB_PORT = os.getenv("DB_PORT")
    DB_NAME = os.getenv("DB_NAME")

    if not all([DB_USER, DB_PASS, DB_HOST, DB_PORT, DB_NAME]):
        pytest.fail("Database environment variables are not set. Cannot run integration test.")

    engine = create_engine(f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

    # Act: Call the tool with the real engine
    tool_input = {"layer_name": "buildings", "db_engine": engine}
    result_json = get_layer_as_geojson.invoke(tool_input)

    # Assert: Check if the output is a valid GeoJSON string
    assert isinstance(result_json, str)
    assert "Error" not in result_json
    
    data = json.loads(result_json)
    assert data["type"] == "FeatureCollection"
    assert len(data["features"]) > 0
    assert data["features"][0]["properties"]["loaded_layer"] == "buildings_low"
