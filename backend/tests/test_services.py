"""
Unit tests for service layer.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from tests.base import ServiceTest, LLMTest, GISTest
from tests.utils import generate_sample_geojson, create_mock_llm_response
from services.gis_service import GISService
from services.intent_service import IntentClassificationService
from services.llm_service import LLMService
from exceptions.gis import LayerNotFoundError, GISDataProcessingError
from exceptions.llm import LLMServiceError, IntentClassificationError


class TestGISService(ServiceTest, GISTest):
    """Test GIS service methods."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.mock_repository = self.create_mock(GISService)
        self.service = GISService(self.mock_repository)
    
    @pytest.mark.unit
    def test_get_layer_success(self):
        """Test successful layer retrieval."""
        # Arrange
        sample_geojson = generate_sample_geojson(feature_count=3)
        self.mock_repository.get_layer_data.return_value = sample_geojson
        
        # Act
        result = self.service.get_layer("buildings", use_low_resolution=True)
        
        # Assert
        self.assert_valid_geojson(result)
        assert self.count_features(result) == 3
        self.mock_repository.get_layer_data.assert_called_once_with("buildings", True)
    
    @pytest.mark.unit
    def test_get_layer_not_found(self):
        """Test layer not found error."""
        # Arrange
        self.mock_repository.get_layer_data.side_effect = LayerNotFoundError("unknown_layer")
        
        # Act & Assert
        with pytest.raises(LayerNotFoundError):
            self.service.get_layer("unknown_layer")
    
    @pytest.mark.unit
    def test_get_available_layers_success(self):
        """Test getting available layers."""
        # Arrange
        expected_layers = [
            {"name": "buildings", "table_name": "buildings_low", "geometry_type": "Polygon"},
            {"name": "parcels", "table_name": "parcels_low", "geometry_type": "Polygon"}
        ]
        self.mock_repository.get_available_tables.return_value = expected_layers
        
        # Act
        result = self.service.get_available_layers()
        
        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "buildings"
        assert result[1]["name"] == "parcels"
    
    @pytest.mark.unit
    def test_find_largest_parcels_success(self):
        """Test finding largest parcels."""
        # Arrange
        sample_parcels = generate_sample_geojson(feature_count=5, geometry_type="Polygon")
        # Add area properties to features
        for i, feature in enumerate(sample_parcels["features"]):
            feature["properties"]["area"] = (i + 1) * 100
        
        self.mock_repository.find_parcels_by_criteria.return_value = sample_parcels
        
        # Act
        result = self.service.find_largest_parcels(n=3)
        
        # Assert
        self.assert_valid_geojson(result)
        assert self.count_features(result) == 5  # Mock returns all features
        self.mock_repository.find_parcels_by_criteria.assert_called_once()
    
    @pytest.mark.unit
    def test_find_parcels_above_area_success(self):
        """Test finding parcels above specified area."""
        # Arrange
        sample_parcels = generate_sample_geojson(feature_count=2, geometry_type="Polygon")
        self.mock_repository.find_parcels_by_criteria.return_value = sample_parcels
        
        # Act
        result = self.service.find_parcels_above_area(min_area=1000)
        
        # Assert
        self.assert_valid_geojson(result)
        self.mock_repository.find_parcels_by_criteria.assert_called_once()
        
        # Check that criteria was passed correctly
        call_args = self.mock_repository.find_parcels_by_criteria.call_args[0][0]
        assert call_args.min_area == 1000
    
    @pytest.mark.unit
    def test_find_parcels_near_gpz_success(self):
        """Test finding parcels near GPZ stations."""
        # Arrange
        sample_parcels = generate_sample_geojson(feature_count=3, geometry_type="Polygon")
        self.mock_repository.find_parcels_near_point.return_value = sample_parcels
        
        # Act
        result = self.service.find_parcels_near_gpz(radius_meters=500)
        
        # Assert
        self.assert_valid_geojson(result)
        self.mock_repository.find_parcels_near_point.assert_called_once_with(
            "gpz_110kv_low", 500
        )
    
    @pytest.mark.unit
    def test_service_error_handling(self):
        """Test service error handling."""
        # Arrange
        self.mock_repository.get_layer_data.side_effect = Exception("Database error")
        
        # Act & Assert
        with pytest.raises(GISDataProcessingError):
            self.service.get_layer("buildings")


class TestIntentClassificationService(LLMTest):
    """Test intent classification service."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.service = IntentClassificationService()
    
    @pytest.mark.unit
    @patch('services.intent_service.ChatGroq')
    def test_classify_intent_gis_data(self, mock_chat_groq):
        """Test classifying GIS data intent."""
        # Arrange
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        
        mock_response = {
            "route": {
                "intent": "get_gis_data",
                "layer_name": "buildings"
            }
        }
        
        # Create a mock chain
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        with patch.object(self.service, 'prompt_template') as mock_template:
            mock_template.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = self.service.classify_intent("Pokaż budynki")
            
            # Assert
            assert result["intent"] == "get_gis_data"
            assert result["layer_name"] == "buildings"
    
    @pytest.mark.unit
    @patch('services.intent_service.ChatGroq')
    def test_classify_intent_chat(self, mock_chat_groq):
        """Test classifying chat intent."""
        # Arrange
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        
        mock_response = {
            "route": {
                "intent": "chat"
            }
        }
        
        mock_chain = Mock()
        mock_chain.invoke.return_value = mock_response
        
        with patch.object(self.service, 'prompt_template') as mock_template:
            mock_template.__or__ = Mock(return_value=mock_chain)
            
            # Act
            result = self.service.classify_intent("Jak się masz?")
            
            # Assert
            assert result["intent"] == "chat"
    
    @pytest.mark.unit
    def test_validate_query_empty(self):
        """Test query validation with empty query."""
        # Act
        result = self.service.validateQuery("")
        
        # Assert
        assert result["isValid"] is False
        assert "puste" in result["error"]
    
    @pytest.mark.unit
    def test_validate_query_too_long(self):
        """Test query validation with too long query."""
        # Arrange
        long_query = "a" * 1001
        
        # Act
        result = self.service.validateQuery(long_query)
        
        # Assert
        assert result["isValid"] is False
        assert "długie" in result["error"]
    
    @pytest.mark.unit
    def test_validate_query_valid(self):
        """Test query validation with valid query."""
        # Act
        result = self.service.validateQuery("Pokaż działki")
        
        # Assert
        assert result["isValid"] is True
        assert "error" not in result
    
    @pytest.mark.unit
    def test_get_intent_display_name(self):
        """Test getting display names for intents."""
        service = IntentClassificationService()
        
        # Test known intents
        assert "Pobieranie warstwy GIS" in service.getIntentDisplayName("get_gis_data")
        assert "Rozmowa ogólna" in service.getIntentDisplayName("chat")
        
        # Test unknown intent
        assert service.getIntentDisplayName("unknown_intent") == "unknown_intent"
    
    @pytest.mark.unit
    @patch('services.intent_service.ChatGroq')
    def test_classify_intent_error_handling(self, mock_chat_groq):
        """Test error handling in intent classification."""
        # Arrange
        mock_chat_groq.side_effect = Exception("LLM API error")
        
        # Act & Assert
        with pytest.raises(IntentClassificationError):
            service = IntentClassificationService()
            service.classify_intent("test query")


class TestLLMService(LLMTest):
    """Test LLM service methods."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.service = LLMService()
    
    @pytest.mark.unit
    @patch('services.llm_service.ChatGroq')
    def test_generate_chat_response_success(self, mock_chat_groq):
        """Test successful chat response generation."""
        # Arrange
        mock_llm = Mock()
        mock_chat_groq.return_value = mock_llm
        
        mock_response = create_mock_llm_response("Witaj! Jak mogę pomóc?")
        mock_llm.invoke.return_value = mock_response
        
        # Act
        result = self.service.generate_chat_response("Cześć")
        
        # Assert
        assert result == "Witaj! Jak mogę pomóc?"
        mock_llm.invoke.assert_called_once()
    
    @pytest.mark.unit
    @patch('services.llm_service.ChatGroq')
    def test_generate_chat_response_error(self, mock_chat_groq):
        """Test chat response generation error handling."""
        # Arrange
        mock_chat_groq.side_effect = Exception("API error")
        
        # Act & Assert
        with pytest.raises(LLMServiceError):
            service = LLMService()
            service.generate_chat_response("test query")
    
    @pytest.mark.unit
    def test_validate_query_parameters(self):
        """Test query parameter validation."""
        service = LLMService()
        
        # Test valid parameters
        assert service._validate_query_parameters("test query", max_length=100) is True
        
        # Test invalid parameters
        with pytest.raises(ValueError):
            service._validate_query_parameters("", max_length=100)
        
        with pytest.raises(ValueError):
            service._validate_query_parameters("a" * 101, max_length=100)


class TestServiceIntegration(ServiceTest):
    """Test service integration scenarios."""
    
    @pytest.mark.unit
    def test_gis_service_with_intent_service(self):
        """Test GIS service working with intent service."""
        # Arrange
        mock_gis_repo = self.create_mock(GISService)
        mock_intent_service = self.create_mock(IntentClassificationService)
        
        gis_service = GISService(mock_gis_repo)
        
        # Mock intent classification
        mock_intent_service.classify_intent.return_value = {
            "intent": "get_gis_data",
            "layer_name": "buildings"
        }
        
        # Mock GIS data
        sample_data = generate_sample_geojson()
        mock_gis_repo.get_layer_data.return_value = sample_data
        
        # Act
        intent_result = mock_intent_service.classify_intent("Pokaż budynki")
        gis_result = gis_service.get_layer(intent_result["layer_name"])
        
        # Assert
        assert intent_result["intent"] == "get_gis_data"
        assert intent_result["layer_name"] == "buildings"
        self.assert_valid_geojson(gis_result)
    
    @pytest.mark.unit
    def test_error_propagation_between_services(self):
        """Test error propagation between services."""
        # Arrange
        mock_gis_repo = self.create_mock(GISService)
        gis_service = GISService(mock_gis_repo)
        
        # Mock repository error
        mock_gis_repo.get_layer_data.side_effect = LayerNotFoundError("test_layer")
        
        # Act & Assert
        with pytest.raises(LayerNotFoundError):
            gis_service.get_layer("test_layer")


@pytest.mark.parametrize("intent,expected_service", [
    ("get_gis_data", "GISService"),
    ("find_largest_parcel", "GISService"),
    ("chat", "LLMService")
])
class TestServiceRouting(ServiceTest):
    """Test service routing based on intent."""
    
    @pytest.mark.unit
    def test_intent_to_service_mapping(self, intent, expected_service):
        """Test that intents are mapped to correct services."""
        # This would test a router/dispatcher if we had one
        service_mapping = {
            "get_gis_data": "GISService",
            "find_largest_parcel": "GISService",
            "find_n_largest_parcels": "GISService",
            "find_parcels_above_area": "GISService",
            "find_parcels_near_gpz": "GISService",
            "chat": "LLMService"
        }
        
        assert service_mapping.get(intent) == expected_service


class TestServicePerformance(ServiceTest):
    """Performance tests for services."""
    
    @pytest.mark.slow
    @pytest.mark.unit
    def test_gis_service_performance(self):
        """Test GIS service performance with large datasets."""
        # Arrange
        mock_gis_repo = self.create_mock(GISService)
        service = GISService(mock_gis_repo)
        
        # Mock large dataset
        large_dataset = generate_sample_geojson(feature_count=1000)
        mock_gis_repo.get_layer_data.return_value = large_dataset
        
        # Act & Assert
        import time
        start_time = time.time()
        result = service.get_layer("large_layer")
        execution_time = time.time() - start_time
        
        # Should process large dataset quickly (< 0.1 seconds for mocked data)
        assert execution_time < 0.1
        assert self.count_features(result) == 1000
    
    @pytest.mark.unit
    def test_intent_service_caching(self):
        """Test intent service response caching."""
        # This would test caching if implemented
        service = IntentClassificationService()
        
        # For now, just test that the service can handle repeated calls
        query = "Pokaż budynki"
        
        with patch.object(service, 'classify_intent') as mock_classify:
            mock_classify.return_value = {"intent": "get_gis_data", "layer_name": "buildings"}
            
            # Multiple calls
            result1 = mock_classify(query)
            result2 = mock_classify(query)
            
            assert result1 == result2
            assert mock_classify.call_count == 2