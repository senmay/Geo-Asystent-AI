"""
Unit tests for domain models and validation.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from tests.base import UnitTest
from tests.utils import generate_sample_geojson, generate_random_coordinates
from models.domain import (
    ParcelCriteria, 
    QueryResult, 
    GISOperationResult,
    LayerMetadata,
    SpatialQuery
)
from models.schemas import (
    ChatRequest,
    ChatResponse,
    LayerInfoResponse,
    ErrorResponse,
    GeoJSONResponse
)


class TestDomainModels(UnitTest):
    """Test domain model classes."""
    
    @pytest.mark.unit
    def test_parcel_criteria_creation(self):
        """Test ParcelCriteria model creation."""
        # Test with all parameters
        criteria = ParcelCriteria(
            min_area=100.0,
            max_area=1000.0,
            limit=10,
            order_by="area_sqm DESC"
        )
        
        assert criteria.min_area == 100.0
        assert criteria.max_area == 1000.0
        assert criteria.limit == 10
        assert criteria.order_by == "area_sqm DESC"
    
    @pytest.mark.unit
    def test_parcel_criteria_defaults(self):
        """Test ParcelCriteria with default values."""
        criteria = ParcelCriteria()
        
        assert criteria.min_area is None
        assert criteria.max_area is None
        assert criteria.limit is None
        assert criteria.order_by == "area_sqm DESC"
    
    @pytest.mark.unit
    def test_parcel_criteria_validation(self):
        """Test ParcelCriteria validation."""
        # Test invalid min_area
        with pytest.raises(ValueError):
            ParcelCriteria(min_area=-10.0)
        
        # Test invalid max_area
        with pytest.raises(ValueError):
            ParcelCriteria(max_area=-5.0)
        
        # Test invalid limit
        with pytest.raises(ValueError):
            ParcelCriteria(limit=0)
        
        # Test min_area > max_area
        with pytest.raises(ValueError):
            ParcelCriteria(min_area=1000.0, max_area=100.0)
    
    @pytest.mark.unit
    def test_query_result_creation(self):
        """Test QueryResult model creation."""
        sample_geojson = generate_sample_geojson(feature_count=3)
        
        result = QueryResult(
            data=sample_geojson,
            feature_count=3,
            execution_time=0.5,
            query_type="get_layer"
        )
        
        assert result.data == sample_geojson
        assert result.feature_count == 3
        assert result.execution_time == 0.5
        assert result.query_type == "get_layer"
        assert isinstance(result.timestamp, datetime)
    
    @pytest.mark.unit
    def test_query_result_validation(self):
        """Test QueryResult validation."""
        sample_geojson = generate_sample_geojson()
        
        # Test invalid feature_count
        with pytest.raises(ValueError):
            QueryResult(
                data=sample_geojson,
                feature_count=-1,
                execution_time=0.5,
                query_type="test"
            )
        
        # Test invalid execution_time
        with pytest.raises(ValueError):
            QueryResult(
                data=sample_geojson,
                feature_count=1,
                execution_time=-0.1,
                query_type="test"
            )
    
    @pytest.mark.unit
    def test_gis_operation_result_success(self):
        """Test GISOperationResult for successful operation."""
        sample_data = generate_sample_geojson()
        
        result = GISOperationResult(
            success=True,
            data=sample_data,
            operation="get_layer",
            layer_name="buildings"
        )
        
        assert result.success is True
        assert result.data == sample_data
        assert result.error is None
        assert result.operation == "get_layer"
        assert result.layer_name == "buildings"
    
    @pytest.mark.unit
    def test_gis_operation_result_failure(self):
        """Test GISOperationResult for failed operation."""
        result = GISOperationResult(
            success=False,
            error="Layer not found",
            operation="get_layer",
            layer_name="unknown_layer"
        )
        
        assert result.success is False
        assert result.data is None
        assert result.error == "Layer not found"
        assert result.operation == "get_layer"
        assert result.layer_name == "unknown_layer"
    
    @pytest.mark.unit
    def test_layer_metadata_creation(self):
        """Test LayerMetadata model creation."""
        metadata = LayerMetadata(
            name="buildings",
            display_name="Budynki",
            description="Building footprints",
            geometry_type="Polygon",
            feature_count=150,
            srid=4326,
            bbox=[20.0, 51.0, 22.0, 53.0]
        )
        
        assert metadata.name == "buildings"
        assert metadata.display_name == "Budynki"
        assert metadata.geometry_type == "Polygon"
        assert metadata.feature_count == 150
        assert metadata.srid == 4326
        assert len(metadata.bbox) == 4
    
    @pytest.mark.unit
    def test_layer_metadata_validation(self):
        """Test LayerMetadata validation."""
        # Test invalid geometry_type
        with pytest.raises(ValueError):
            LayerMetadata(
                name="test",
                geometry_type="InvalidType",
                feature_count=10,
                srid=4326
            )
        
        # Test invalid SRID
        with pytest.raises(ValueError):
            LayerMetadata(
                name="test",
                geometry_type="Point",
                feature_count=10,
                srid=-1
            )
        
        # Test invalid bbox
        with pytest.raises(ValueError):
            LayerMetadata(
                name="test",
                geometry_type="Point",
                feature_count=10,
                srid=4326,
                bbox=[20.0, 51.0, 22.0]  # Should have 4 values
            )
    
    @pytest.mark.unit
    def test_spatial_query_creation(self):
        """Test SpatialQuery model creation."""
        coords = generate_random_coordinates(1)[0]
        
        query = SpatialQuery(
            query_type="intersects",
            geometry={
                "type": "Point",
                "coordinates": list(coords)
            },
            layers=["buildings", "parcels"],
            buffer_distance=100.0
        )
        
        assert query.query_type == "intersects"
        assert query.geometry["type"] == "Point"
        assert query.layers == ["buildings", "parcels"]
        assert query.buffer_distance == 100.0
    
    @pytest.mark.unit
    def test_spatial_query_validation(self):
        """Test SpatialQuery validation."""
        # Test invalid query_type
        with pytest.raises(ValueError):
            SpatialQuery(
                query_type="invalid_type",
                geometry={"type": "Point", "coordinates": [0, 0]}
            )
        
        # Test invalid buffer_distance
        with pytest.raises(ValueError):
            SpatialQuery(
                query_type="intersects",
                geometry={"type": "Point", "coordinates": [0, 0]},
                buffer_distance=-10.0
            )


class TestAPISchemas(UnitTest):
    """Test API schema models."""
    
    @pytest.mark.unit
    def test_chat_request_creation(self):
        """Test ChatRequest schema creation."""
        request = ChatRequest(
            query="Pokaż budynki",
            context={"user_id": "123", "session_id": "abc"}
        )
        
        assert request.query == "Pokaż budynki"
        assert request.context["user_id"] == "123"
        assert request.context["session_id"] == "abc"
    
    @pytest.mark.unit
    def test_chat_request_validation(self):
        """Test ChatRequest validation."""
        # Test empty query
        with pytest.raises(ValidationError):
            ChatRequest(query="")
        
        # Test query too long
        with pytest.raises(ValidationError):
            ChatRequest(query="a" * 1001)
        
        # Test valid query without context
        request = ChatRequest(query="Test query")
        assert request.query == "Test query"
        assert request.context is None
    
    @pytest.mark.unit
    def test_chat_response_creation(self):
        """Test ChatResponse schema creation."""
        response = ChatResponse(
            type="text",
            data="Hello, how can I help you?",
            intent="chat",
            metadata={"confidence": 0.9}
        )
        
        assert response.type == "text"
        assert response.data == "Hello, how can I help you?"
        assert response.intent == "chat"
        assert response.metadata["confidence"] == 0.9
    
    @pytest.mark.unit
    def test_chat_response_geojson(self):
        """Test ChatResponse with GeoJSON data."""
        sample_geojson = generate_sample_geojson()
        
        response = ChatResponse(
            type="geojson",
            data=sample_geojson,
            intent="get_gis_data",
            metadata={"layer_name": "buildings"}
        )
        
        assert response.type == "geojson"
        assert response.data == sample_geojson
        assert response.intent == "get_gis_data"
        assert response.metadata["layer_name"] == "buildings"
    
    @pytest.mark.unit
    def test_chat_response_validation(self):
        """Test ChatResponse validation."""
        # Test invalid type
        with pytest.raises(ValidationError):
            ChatResponse(
                type="invalid_type",
                data="test",
                intent="chat"
            )
        
        # Test missing required fields
        with pytest.raises(ValidationError):
            ChatResponse(type="text")
    
    @pytest.mark.unit
    def test_layer_info_response_creation(self):
        """Test LayerInfoResponse schema creation."""
        response = LayerInfoResponse(
            name="buildings",
            table_name="buildings_low",
            geometry_type="Polygon",
            srid=4326,
            feature_count=150,
            bbox=[20.0, 51.0, 22.0, 53.0]
        )
        
        assert response.name == "buildings"
        assert response.table_name == "buildings_low"
        assert response.geometry_type == "Polygon"
        assert response.srid == 4326
        assert response.feature_count == 150
        assert len(response.bbox) == 4
    
    @pytest.mark.unit
    def test_error_response_creation(self):
        """Test ErrorResponse schema creation."""
        response = ErrorResponse(
            error={
                "type": "LayerNotFoundError",
                "message": "Layer 'unknown' not found",
                "code": "LAYER_NOT_FOUND",
                "details": {"layer_name": "unknown"}
            },
            timestamp=datetime.now(),
            request_id="req-123"
        )
        
        assert response.error["type"] == "LayerNotFoundError"
        assert response.error["message"] == "Layer 'unknown' not found"
        assert response.error["code"] == "LAYER_NOT_FOUND"
        assert response.error["details"]["layer_name"] == "unknown"
        assert isinstance(response.timestamp, datetime)
        assert response.request_id == "req-123"
    
    @pytest.mark.unit
    def test_geojson_response_creation(self):
        """Test GeoJSONResponse schema creation."""
        sample_geojson = generate_sample_geojson(feature_count=5)
        
        response = GeoJSONResponse(
            type="FeatureCollection",
            features=sample_geojson["features"],
            metadata={
                "layer_name": "buildings",
                "query_time": 0.5,
                "feature_count": 5
            }
        )
        
        assert response.type == "FeatureCollection"
        assert len(response.features) == 5
        assert response.metadata["layer_name"] == "buildings"
        assert response.metadata["feature_count"] == 5
    
    @pytest.mark.unit
    def test_geojson_response_validation(self):
        """Test GeoJSONResponse validation."""
        # Test invalid type
        with pytest.raises(ValidationError):
            GeoJSONResponse(
                type="InvalidCollection",
                features=[]
            )
        
        # Test invalid features
        with pytest.raises(ValidationError):
            GeoJSONResponse(
                type="FeatureCollection",
                features=[{"invalid": "feature"}]
            )


class TestModelSerialization(UnitTest):
    """Test model serialization and deserialization."""
    
    @pytest.mark.unit
    def test_parcel_criteria_serialization(self):
        """Test ParcelCriteria serialization."""
        criteria = ParcelCriteria(
            min_area=100.0,
            max_area=1000.0,
            limit=10
        )
        
        # Test to dict
        data = criteria.dict()
        assert data["min_area"] == 100.0
        assert data["max_area"] == 1000.0
        assert data["limit"] == 10
        
        # Test from dict
        new_criteria = ParcelCriteria(**data)
        assert new_criteria.min_area == criteria.min_area
        assert new_criteria.max_area == criteria.max_area
        assert new_criteria.limit == criteria.limit
    
    @pytest.mark.unit
    def test_query_result_serialization(self):
        """Test QueryResult serialization."""
        sample_geojson = generate_sample_geojson()
        
        result = QueryResult(
            data=sample_geojson,
            feature_count=1,
            execution_time=0.5,
            query_type="test"
        )
        
        # Test to dict
        data = result.dict()
        assert data["data"] == sample_geojson
        assert data["feature_count"] == 1
        assert data["execution_time"] == 0.5
        
        # Test JSON serialization
        json_str = result.json()
        assert isinstance(json_str, str)
        assert "FeatureCollection" in json_str
    
    @pytest.mark.unit
    def test_chat_request_serialization(self):
        """Test ChatRequest serialization."""
        request = ChatRequest(
            query="Test query",
            context={"key": "value"}
        )
        
        # Test to dict
        data = request.dict()
        assert data["query"] == "Test query"
        assert data["context"]["key"] == "value"
        
        # Test JSON serialization
        json_str = request.json()
        assert "Test query" in json_str
        assert "key" in json_str


class TestModelValidationEdgeCases(UnitTest):
    """Test model validation edge cases."""
    
    @pytest.mark.unit
    def test_parcel_criteria_edge_values(self):
        """Test ParcelCriteria with edge values."""
        # Test zero values
        criteria = ParcelCriteria(min_area=0.0, max_area=0.0)
        assert criteria.min_area == 0.0
        assert criteria.max_area == 0.0
        
        # Test very large values
        criteria = ParcelCriteria(min_area=1e10, max_area=1e12)
        assert criteria.min_area == 1e10
        assert criteria.max_area == 1e12
        
        # Test very small positive values
        criteria = ParcelCriteria(min_area=0.001, max_area=0.002)
        assert criteria.min_area == 0.001
        assert criteria.max_area == 0.002
    
    @pytest.mark.unit
    def test_layer_metadata_optional_fields(self):
        """Test LayerMetadata with optional fields."""
        # Test minimal required fields
        metadata = LayerMetadata(
            name="test",
            geometry_type="Point",
            feature_count=10,
            srid=4326
        )
        
        assert metadata.name == "test"
        assert metadata.display_name is None
        assert metadata.description is None
        assert metadata.bbox is None
        
        # Test with all optional fields
        metadata = LayerMetadata(
            name="test",
            display_name="Test Layer",
            description="A test layer",
            geometry_type="Point",
            feature_count=10,
            srid=4326,
            bbox=[0, 0, 1, 1],
            tags=["test", "sample"],
            created_at=datetime.now()
        )
        
        assert metadata.display_name == "Test Layer"
        assert metadata.description == "A test layer"
        assert metadata.bbox == [0, 0, 1, 1]
        assert metadata.tags == ["test", "sample"]
        assert isinstance(metadata.created_at, datetime)
    
    @pytest.mark.unit
    def test_spatial_query_geometry_types(self):
        """Test SpatialQuery with different geometry types."""
        # Test Point geometry
        point_query = SpatialQuery(
            query_type="intersects",
            geometry={
                "type": "Point",
                "coordinates": [21.0, 52.0]
            }
        )
        assert point_query.geometry["type"] == "Point"
        
        # Test Polygon geometry
        polygon_query = SpatialQuery(
            query_type="contains",
            geometry={
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]
            }
        )
        assert polygon_query.geometry["type"] == "Polygon"
        
        # Test LineString geometry
        line_query = SpatialQuery(
            query_type="crosses",
            geometry={
                "type": "LineString",
                "coordinates": [[0, 0], [1, 1]]
            }
        )
        assert line_query.geometry["type"] == "LineString"


@pytest.mark.parametrize("geometry_type,expected_valid", [
    ("Point", True),
    ("LineString", True),
    ("Polygon", True),
    ("MultiPoint", True),
    ("MultiLineString", True),
    ("MultiPolygon", True),
    ("GeometryCollection", True),
    ("InvalidType", False),
    ("point", False),  # Case sensitive
    ("", False)
])
class TestGeometryTypeValidation(UnitTest):
    """Parametrized tests for geometry type validation."""
    
    @pytest.mark.unit
    def test_geometry_type_validation(self, geometry_type, expected_valid):
        """Test geometry type validation."""
        if expected_valid:
            metadata = LayerMetadata(
                name="test",
                geometry_type=geometry_type,
                feature_count=10,
                srid=4326
            )
            assert metadata.geometry_type == geometry_type
        else:
            with pytest.raises(ValueError):
                LayerMetadata(
                    name="test",
                    geometry_type=geometry_type,
                    feature_count=10,
                    srid=4326
                )