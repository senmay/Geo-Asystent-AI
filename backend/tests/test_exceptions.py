"""
Unit tests for exception handling.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from tests.base import UnitTest, ErrorHandlingMixin
from exceptions.base import GeoAsystentException, ErrorCode
from exceptions.gis import (
    LayerNotFoundError,
    InvalidLayerNameError,
    GISDataProcessingError,
    DatabaseConnectionError,
    SpatialQueryError
)
from exceptions.llm import (
    LLMServiceError,
    IntentClassificationError,
    LLMTimeoutError,
    LLMAPIKeyError
)


class TestBaseException(UnitTest):
    """Test base exception class."""
    
    @pytest.mark.unit
    def test_base_exception_creation(self):
        """Test basic exception creation."""
        exc = GeoAsystentException(
            message="Test error",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            details={"key": "value"},
            user_message="User friendly message"
        )
        
        assert str(exc) == "Test error"
        assert exc.code == ErrorCode.INTERNAL_SERVER_ERROR
        assert exc.details == {"key": "value"}
        assert exc.user_message == "User friendly message"
    
    @pytest.mark.unit
    def test_base_exception_defaults(self):
        """Test exception with default values."""
        exc = GeoAsystentException("Simple error", ErrorCode.INTERNAL_SERVER_ERROR)
        
        assert str(exc) == "Simple error"
        assert exc.code == ErrorCode.INTERNAL_SERVER_ERROR
        assert exc.details == {}
        assert "Wystąpił błąd wewnętrzny serwera" in exc.user_message
    
    @pytest.mark.unit
    def test_exception_serialization(self):
        """Test exception serialization to dict."""
        exc = GeoAsystentException(
            message="Test error",
            code=ErrorCode.VALIDATION_ERROR,
            details={"field": "test_field"},
            user_message="Validation failed"
        )
        
        data = exc.to_dict()
        
        assert data["error"]["message"] == "Validation failed"  # user_message
        assert data["error"]["code"] == ErrorCode.VALIDATION_ERROR
        assert data["error"]["details"] == {"field": "test_field"}
    
    @pytest.mark.unit
    def test_error_code_enum(self):
        """Test ErrorCode enum values."""
        # Test that all expected error codes exist
        expected_codes = [
            "INTERNAL_SERVER_ERROR",
            "VALIDATION_ERROR",
            "CONFIGURATION_ERROR",
            "LAYER_NOT_FOUND",
            "INVALID_LAYER_NAME",
            "GIS_DATA_PROCESSING_ERROR",
            "DATABASE_CONNECTION_ERROR",
            "SPATIAL_QUERY_ERROR",
            "LLM_SERVICE_ERROR",
            "INTENT_CLASSIFICATION_ERROR",
            "LLM_TIMEOUT_ERROR",
            "LLM_API_KEY_ERROR"
        ]
        
        for code_name in expected_codes:
            assert hasattr(ErrorCode, code_name)
            code = getattr(ErrorCode, code_name)
            assert isinstance(code.value, str)


class TestGISExceptions(UnitTest, ErrorHandlingMixin):
    """Test GIS-specific exceptions."""
    
    @pytest.mark.unit
    def test_layer_not_found_error(self):
        """Test LayerNotFoundError creation and properties."""
        exc = LayerNotFoundError(
            layer_name="unknown_layer",
            available_layers=["buildings", "parcels"]
        )
        
        assert "unknown_layer" in str(exc)
        assert exc.code == ErrorCode.LAYER_NOT_FOUND
        assert exc.details["layer_name"] == "unknown_layer"
        assert exc.details["available_layers"] == ["buildings", "parcels"]
        assert "nie została znaleziona" in exc.user_message
        assert "buildings, parcels" in exc.user_message
    
    @pytest.mark.unit
    def test_layer_not_found_error_without_available_layers(self):
        """Test LayerNotFoundError without available layers list."""
        exc = LayerNotFoundError(layer_name="unknown_layer")
        
        assert exc.details["layer_name"] == "unknown_layer"
        assert "available_layers" not in exc.details
        assert "Dostępne warstwy" not in exc.user_message
    
    @pytest.mark.unit
    def test_invalid_layer_name_error(self):
        """Test InvalidLayerNameError creation."""
        exc = InvalidLayerNameError(
            layer_name="invalid@layer",
            valid_patterns=["buildings", "parcels", "gpz"]
        )
        
        assert "invalid@layer" in str(exc)
        assert exc.code == ErrorCode.INVALID_LAYER_NAME
        assert exc.details["layer_name"] == "invalid@layer"
        assert exc.details["valid_patterns"] == ["buildings", "parcels", "gpz"]
        assert "Nieprawidłowa nazwa warstwy" in exc.user_message
    
    @pytest.mark.unit
    def test_invalid_layer_name_error_default_patterns(self):
        """Test InvalidLayerNameError with default patterns."""
        exc = InvalidLayerNameError(layer_name="invalid@layer")
        
        assert "działki" in exc.user_message
        assert "budynki" in exc.user_message
        assert "gpz" in exc.user_message
    
    @pytest.mark.unit
    def test_gis_data_processing_error(self):
        """Test GISDataProcessingError creation."""
        original_error = ValueError("Invalid geometry")
        
        exc = GISDataProcessingError(
            operation="geometry_validation",
            original_error=original_error
        )
        
        assert "geometry_validation" in str(exc)
        assert exc.code == ErrorCode.GIS_DATA_PROCESSING_ERROR
        assert exc.details["operation"] == "geometry_validation"
        assert exc.details["original_error"] == "Invalid geometry"
        assert exc.details["error_type"] == "ValueError"
        assert "Błąd podczas przetwarzania danych GIS" in exc.user_message
    
    @pytest.mark.unit
    def test_database_connection_error(self):
        """Test DatabaseConnectionError creation."""
        original_error = ConnectionError("Connection refused")
        
        exc = DatabaseConnectionError(
            operation="layer_query",
            original_error=original_error
        )
        
        assert "layer_query" in str(exc)
        assert exc.code == ErrorCode.DATABASE_CONNECTION_ERROR
        assert exc.details["operation"] == "layer_query"
        assert exc.details["original_error"] == "Connection refused"
        assert "Błąd połączenia z bazą danych" in exc.user_message
    
    @pytest.mark.unit
    def test_spatial_query_error(self):
        """Test SpatialQueryError creation."""
        parameters = {"layer": "buildings", "radius": 100}
        original_error = Exception("Invalid spatial query")
        
        exc = SpatialQueryError(
            query_type="proximity_search",
            parameters=parameters,
            original_error=original_error
        )
        
        assert "proximity_search" in str(exc)
        assert exc.code == ErrorCode.SPATIAL_QUERY_ERROR
        assert exc.details["query_type"] == "proximity_search"
        assert exc.details["parameters"] == parameters
        assert exc.details["original_error"] == "Invalid spatial query"
        assert "zapytania przestrzennego" in exc.user_message


class TestLLMExceptions(UnitTest, ErrorHandlingMixin):
    """Test LLM-specific exceptions."""
    
    @pytest.mark.unit
    def test_llm_service_error(self):
        """Test LLMServiceError creation."""
        original_error = Exception("API rate limit exceeded")
        
        exc = LLMServiceError(
            operation="chat_completion",
            original_error=original_error
        )
        
        assert "chat_completion" in str(exc)
        assert exc.code == ErrorCode.LLM_SERVICE_ERROR
        assert exc.details["operation"] == "chat_completion"
        assert exc.details["original_error"] == "API rate limit exceeded"
        assert "Błąd usługi AI" in exc.user_message
    
    @pytest.mark.unit
    def test_intent_classification_error(self):
        """Test IntentClassificationError creation."""
        query = "Pokaż budynki"
        original_error = ValueError("Invalid response format")
        
        exc = IntentClassificationError(
            query=query,
            original_error=original_error
        )
        
        assert query in str(exc)
        assert exc.code == ErrorCode.INTENT_CLASSIFICATION_ERROR
        assert exc.details["query"] == query
        assert exc.details["original_error"] == "Invalid response format"
        assert "Nie udało się zrozumieć zapytania" in exc.user_message
    
    @pytest.mark.unit
    def test_llm_timeout_error(self):
        """Test LLMTimeoutError creation."""
        exc = LLMTimeoutError(
            timeout_seconds=30,
            operation="intent_classification"
        )
        
        assert "30" in str(exc)
        assert "intent_classification" in str(exc)
        assert exc.code == ErrorCode.LLM_TIMEOUT_ERROR
        assert exc.details["timeout_seconds"] == 30
        assert exc.details["operation"] == "intent_classification"
        assert "przekroczyło limit czasu" in exc.user_message
    
    @pytest.mark.unit
    def test_llm_api_key_error(self):
        """Test LLMAPIKeyError creation."""
        exc = LLMAPIKeyError()
        
        assert "API key" in str(exc)
        assert exc.code == ErrorCode.LLM_API_KEY_ERROR
        assert "autoryzacji" in exc.user_message


class TestExceptionHandling(UnitTest, ErrorHandlingMixin):
    """Test exception handling patterns."""
    
    @pytest.mark.unit
    def test_exception_chaining(self):
        """Test exception chaining with original errors."""
        # Create a chain of exceptions
        original = ValueError("Original error")
        
        try:
            raise original
        except ValueError as e:
            processing_error = GISDataProcessingError(
                operation="test_operation",
                original_error=e
            )
        
        assert processing_error.details["original_error"] == "Original error"
        assert processing_error.details["error_type"] == "ValueError"
    
    @pytest.mark.unit
    def test_exception_context_preservation(self):
        """Test that exception context is preserved."""
        context = {
            "user_id": "123",
            "session_id": "abc",
            "layer_name": "buildings",
            "query": "show buildings"
        }
        
        exc = LayerNotFoundError(
            layer_name=context["layer_name"]
        )
        
        # Add context to exception
        exc.details.update(context)
        
        assert exc.details["user_id"] == "123"
        assert exc.details["session_id"] == "abc"
        assert exc.details["query"] == "show buildings"
    
    @pytest.mark.unit
    def test_exception_logging_integration(self):
        """Test exception integration with logging."""
        with patch('logging.getLogger') as mock_logger:
            mock_log = Mock()
            mock_logger.return_value = mock_log
            
            exc = GISDataProcessingError(
                operation="test_operation",
                original_error=Exception("Test error")
            )
            
            # Simulate logging the exception
            mock_log.error(
                f"GIS processing error: {exc}",
                extra=exc.to_dict()
            )
            
            mock_log.error.assert_called_once()
            call_args = mock_log.error.call_args
            assert "GIS processing error" in call_args[0][0]
            assert "extra" in call_args[1]
    
    @pytest.mark.unit
    def test_exception_user_message_localization(self):
        """Test user message localization."""
        # Test Polish messages
        exc = LayerNotFoundError("test_layer")
        assert "nie została znaleziona" in exc.user_message
        
        exc = GISDataProcessingError("test_operation")
        assert "Błąd podczas przetwarzania" in exc.user_message
        
        exc = LLMTimeoutError(30, "test_operation")
        assert "przekroczyło limit czasu" in exc.user_message


class TestExceptionEdgeCases(UnitTest):
    """Test exception edge cases."""
    
    @pytest.mark.unit
    def test_exception_with_none_values(self):
        """Test exception handling with None values."""
        exc = GeoAsystentException(
            message="Test error",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            details=None,
            user_message=None
        )
        
        assert exc.details == {}
        assert "Wystąpił błąd wewnętrzny serwera" in exc.user_message  # Uses default message
    
    @pytest.mark.unit
    def test_exception_with_empty_strings(self):
        """Test exception handling with empty strings."""
        exc = GeoAsystentException(
            message="",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            user_message=""
        )
        
        assert str(exc) == ""
        assert "Wystąpił błąd wewnętrzny serwera" in exc.user_message  # Empty string gets default message
    
    @pytest.mark.unit
    def test_exception_with_large_details(self):
        """Test exception with large details dictionary."""
        large_details = {f"key_{i}": f"value_{i}" for i in range(1000)}
        
        exc = GeoAsystentException(
            message="Test error",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            details=large_details
        )
        
        assert len(exc.details) == 1000
        assert exc.details["key_500"] == "value_500"
    
    @pytest.mark.unit
    def test_exception_serialization_with_complex_objects(self):
        """Test exception serialization with complex objects in details."""
        complex_details = {
            "datetime": datetime.now(),
            "list": [1, 2, 3],
            "dict": {"nested": "value"},
            "none": None
        }
        
        exc = GeoAsystentException(
            message="Test error",
            code=ErrorCode.INTERNAL_SERVER_ERROR,
            details=complex_details
        )
        
        # Should handle serialization gracefully
        data = exc.to_dict()
        assert "error" in data
        assert "details" in data["error"]
        assert isinstance(data["error"]["details"], dict)


@pytest.mark.parametrize("error_class,expected_code", [
    (LayerNotFoundError, ErrorCode.LAYER_NOT_FOUND),
    (InvalidLayerNameError, ErrorCode.INVALID_LAYER_NAME),
    (GISDataProcessingError, ErrorCode.GIS_DATA_PROCESSING_ERROR),
    (DatabaseConnectionError, ErrorCode.DATABASE_CONNECTION_ERROR),
    (SpatialQueryError, ErrorCode.SPATIAL_QUERY_ERROR),
    (LLMServiceError, ErrorCode.LLM_SERVICE_ERROR),
    (IntentClassificationError, ErrorCode.INTENT_CLASSIFICATION_ERROR),
    (LLMTimeoutError, ErrorCode.LLM_TIMEOUT_ERROR),
    (LLMAPIKeyError, ErrorCode.LLM_API_KEY_ERROR)
])
class TestExceptionCodes(UnitTest):
    """Parametrized tests for exception error codes."""
    
    @pytest.mark.unit
    def test_exception_error_codes(self, error_class, expected_code):
        """Test that exceptions have correct error codes."""
        # Create exception with minimal required parameters
        if error_class == LayerNotFoundError:
            exc = error_class("test_layer")
        elif error_class == InvalidLayerNameError:
            exc = error_class("test_layer")
        elif error_class == GISDataProcessingError:
            exc = error_class("test_operation")
        elif error_class == DatabaseConnectionError:
            exc = error_class("test_operation")
        elif error_class == SpatialQueryError:
            exc = error_class("test_query")
        elif error_class == LLMServiceError:
            exc = error_class("test_operation")
        elif error_class == IntentClassificationError:
            exc = error_class("test_query")
        elif error_class == LLMTimeoutError:
            exc = error_class(30, "test_operation")
        elif error_class == LLMAPIKeyError:
            exc = error_class()
        else:
            exc = error_class("test_message")
        
        assert exc.code == expected_code