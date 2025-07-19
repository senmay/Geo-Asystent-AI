"""
Base test classes for different types of tests.
"""

import pytest
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine

from repositories.gis_repository import GISRepository
from services.gis_service import GISService
from services.intent_service import IntentClassificationService
from services.llm_service import LLMService


class BaseTest(ABC):
    """Base class for all tests."""
    
    def setup_method(self):
        """Setup method called before each test method."""
        pass
    
    def teardown_method(self):
        """Teardown method called after each test method."""
        pass


class UnitTest(BaseTest):
    """Base class for unit tests.
    
    Unit tests should be fast and not depend on external resources.
    They should use mocks for all dependencies.
    """
    
    @pytest.fixture(autouse=True)
    def setup_unit_test(self):
        """Setup for unit tests."""
        self.mocks = {}
    
    def create_mock(self, spec_class: type, name: str = None) -> Mock:
        """Create and store a mock object."""
        mock_name = name or spec_class.__name__.lower()
        mock_obj = Mock(spec=spec_class)
        self.mocks[mock_name] = mock_obj
        return mock_obj
    
    def get_mock(self, name: str) -> Mock:
        """Get a stored mock object."""
        return self.mocks.get(name)


class IntegrationTest(BaseTest):
    """Base class for integration tests.
    
    Integration tests can use real database connections and external services.
    They should be marked with @pytest.mark.integration.
    """
    
    @pytest.fixture(autouse=True)
    def setup_integration_test(self, test_db_with_sample_data: Engine):
        """Setup for integration tests."""
        self.test_engine = test_db_with_sample_data
    
    def get_test_session(self) -> Session:
        """Get a test database session."""
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.test_engine)
        return SessionLocal()


class APITest(BaseTest):
    """Base class for API endpoint tests.
    
    API tests use TestClient to test FastAPI endpoints.
    """
    
    @pytest.fixture(autouse=True)
    def setup_api_test(self, test_client: TestClient):
        """Setup for API tests."""
        self.client = test_client
    
    def get(self, url: str, **kwargs) -> Any:
        """Make a GET request."""
        return self.client.get(url, **kwargs)
    
    def post(self, url: str, **kwargs) -> Any:
        """Make a POST request."""
        return self.client.post(url, **kwargs)
    
    def put(self, url: str, **kwargs) -> Any:
        """Make a PUT request."""
        return self.client.put(url, **kwargs)
    
    def delete(self, url: str, **kwargs) -> Any:
        """Make a DELETE request."""
        return self.client.delete(url, **kwargs)
    
    def assert_status_code(self, response: Any, expected_code: int):
        """Assert response status code."""
        assert response.status_code == expected_code, f"Expected {expected_code}, got {response.status_code}: {response.text}"
    
    def assert_json_response(self, response: Any, expected_keys: list = None):
        """Assert response is valid JSON with expected keys."""
        assert response.headers.get("content-type") == "application/json"
        json_data = response.json()
        if expected_keys:
            for key in expected_keys:
                assert key in json_data, f"Key '{key}' not found in response"
        return json_data


class RepositoryTest(UnitTest):
    """Base class for repository tests."""
    
    def setup_method(self):
        """Setup method for repository tests."""
        super().setup_method()
        # Session will be injected by pytest fixture
        self.session = None
    
    def create_repository(self, repository_class: type, session: Session = None) -> Any:
        """Create a repository instance with test session."""
        test_session = session or self.session
        if test_session is None:
            # Create a mock session for unit tests
            from unittest.mock import Mock
            test_session = Mock()
        return repository_class(test_session)


class ServiceTest(UnitTest):
    """Base class for service tests."""
    
    def setup_method(self):
        """Setup method for service tests."""
        super().setup_method()
        self.mock_repository = None
        self.service = None
    
    def create_service_with_mocks(self, service_class: type, **mock_dependencies) -> Any:
        """Create a service instance with mocked dependencies."""
        return service_class(**mock_dependencies)


class GISTest(BaseTest):
    """Base class for GIS-related tests."""
    
    def assert_valid_geojson(self, geojson: Dict[str, Any]):
        """Assert that the given data is valid GeoJSON."""
        assert isinstance(geojson, dict), "GeoJSON must be a dictionary"
        assert geojson.get("type") == "FeatureCollection", "GeoJSON must be a FeatureCollection"
        assert "features" in geojson, "GeoJSON must have features"
        assert isinstance(geojson["features"], list), "Features must be a list"
        
        for feature in geojson["features"]:
            self.assert_valid_feature(feature)
    
    def assert_valid_feature(self, feature: Dict[str, Any]):
        """Assert that the given data is a valid GeoJSON feature."""
        assert isinstance(feature, dict), "Feature must be a dictionary"
        assert feature.get("type") == "Feature", "Feature type must be 'Feature'"
        assert "geometry" in feature, "Feature must have geometry"
        assert "properties" in feature, "Feature must have properties"
        
        geometry = feature["geometry"]
        assert isinstance(geometry, dict), "Geometry must be a dictionary"
        assert "type" in geometry, "Geometry must have type"
        assert "coordinates" in geometry, "Geometry must have coordinates"
    
    def assert_geometry_type(self, geojson: Dict[str, Any], expected_type: str):
        """Assert that all geometries in GeoJSON are of expected type."""
        for feature in geojson["features"]:
            geometry_type = feature["geometry"]["type"]
            assert geometry_type == expected_type, f"Expected geometry type {expected_type}, got {geometry_type}"
    
    def count_features(self, geojson: Dict[str, Any]) -> int:
        """Count the number of features in GeoJSON."""
        return len(geojson.get("features", []))


class LLMTest(UnitTest):
    """Base class for LLM service tests."""
    
    def setup_method(self):
        """Setup method for LLM tests."""
        super().setup_method()
        self.mock_llm_client = Mock()
    
    def mock_llm_response(self, response_text: str, intent: str = None, confidence: float = 0.9):
        """Mock LLM response."""
        mock_response = Mock()
        mock_response.content = response_text
        if intent:
            mock_response.intent = intent
            mock_response.confidence = confidence
        return mock_response
    
    def assert_intent_classification(self, result: Dict[str, Any], expected_intent: str, min_confidence: float = 0.5):
        """Assert intent classification result."""
        assert "intent" in result, "Result must contain intent"
        assert "confidence" in result, "Result must contain confidence"
        assert result["intent"] == expected_intent, f"Expected intent {expected_intent}, got {result['intent']}"
        assert result["confidence"] >= min_confidence, f"Confidence {result['confidence']} below minimum {min_confidence}"


class DatabaseTest(IntegrationTest):
    """Base class for database tests."""
    
    def execute_sql(self, sql: str, params: Dict[str, Any] = None) -> Any:
        """Execute SQL query on test database."""
        with self.test_engine.connect() as conn:
            return conn.execute(sql, params or {})
    
    def count_table_rows(self, table_name: str) -> int:
        """Count rows in a table."""
        result = self.execute_sql(f"SELECT COUNT(*) FROM {table_name}")
        return result.scalar()
    
    def table_exists(self, table_name: str) -> bool:
        """Check if table exists."""
        try:
            self.count_table_rows(table_name)
            return True
        except Exception:
            return False


# ============================================================================
# Test Mixins
# ============================================================================

class ErrorHandlingMixin:
    """Mixin for testing error handling."""
    
    def assert_raises_with_message(self, exception_class: type, message_pattern: str, callable_obj, *args, **kwargs):
        """Assert that exception is raised with specific message pattern."""
        with pytest.raises(exception_class) as exc_info:
            callable_obj(*args, **kwargs)
        assert message_pattern in str(exc_info.value)
    
    def assert_error_response(self, response: Any, expected_status: int, expected_error_type: str = None):
        """Assert API error response format."""
        assert response.status_code == expected_status
        error_data = response.json()
        assert "error" in error_data
        if expected_error_type:
            assert error_data["error"].get("type") == expected_error_type


class ValidationMixin:
    """Mixin for testing validation."""
    
    def assert_validation_error(self, response: Any, field_name: str = None):
        """Assert validation error response."""
        assert response.status_code == 422
        error_data = response.json()
        assert "detail" in error_data
        if field_name:
            # Check if field is mentioned in validation errors
            detail_str = str(error_data["detail"])
            assert field_name in detail_str


class PerformanceMixin:
    """Mixin for testing performance."""
    
    def assert_execution_time(self, callable_obj, max_seconds: float, *args, **kwargs):
        """Assert that function executes within time limit."""
        import time
        start_time = time.time()
        result = callable_obj(*args, **kwargs)
        execution_time = time.time() - start_time
        assert execution_time <= max_seconds, f"Execution took {execution_time:.2f}s, expected <= {max_seconds}s"
        return result