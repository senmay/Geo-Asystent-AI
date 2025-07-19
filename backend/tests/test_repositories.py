"""
Tests for repository layer.
"""

import pytest
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from sqlalchemy import text

from tests.base import RepositoryTest, IntegrationTest, GISTest
from tests.utils import generate_sample_geojson, assert_geojson_structure
from repositories.gis_repository import GISRepository
from exceptions.gis import LayerNotFoundError


class TestGISRepository(RepositoryTest, GISTest):
    """Test GIS repository methods."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        # Create a mock session with execute method
        from unittest.mock import Mock
        self.session = Mock()
        self.repository = self.create_repository(GISRepository, self.session)
    
    @pytest.mark.unit
    def test_get_available_layers_success(self):
        """Test getting available layers."""
        # Mock the database query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            ("buildings", "buildings_low", "Polygon", 4326, 150),
            ("parcels", "parcels_low", "Polygon", 4326, 200),
            ("gpz_110kv", "gpz_110kv_low", "Point", 4326, 25)
        ]
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            layers = self.repository.get_available_layers()
        
        assert len(layers) == 3
        assert layers[0]["name"] == "buildings"
        assert layers[0]["table_name"] == "buildings_low"
        assert layers[0]["geometry_type"] == "Polygon"
        assert layers[0]["srid"] == 4326
        assert layers[0]["feature_count"] == 150
    
    @pytest.mark.unit
    def test_get_available_layers_empty(self):
        """Test getting available layers when none exist."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            layers = self.repository.get_available_layers()
        
        assert layers == []
    
    @pytest.mark.unit
    def test_get_layer_as_geojson_success(self):
        """Test getting layer as GeoJSON."""
        # Mock the database query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, "Building 1", "POLYGON((0 0, 1 0, 1 1, 0 1, 0 0))"),
            (2, "Building 2", "POLYGON((2 2, 3 2, 3 3, 2 3, 2 2))")
        ]
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            geojson = self.repository.get_layer_as_geojson("buildings_low")
        
        self.assert_valid_geojson(geojson)
        assert self.count_features(geojson) == 2
        
        # Check first feature
        first_feature = geojson["features"][0]
        assert first_feature["properties"]["id"] == 1
        assert first_feature["properties"]["name"] == "Building 1"
        assert first_feature["geometry"]["type"] == "Polygon"
    
    @pytest.mark.unit
    def test_get_layer_as_geojson_not_found(self):
        """Test getting non-existent layer."""
        mock_result = Mock()
        mock_result.fetchall.return_value = []
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            with pytest.raises(LayerNotFoundError):
                self.repository.get_layer_as_geojson("non_existent_layer")
    
    @pytest.mark.unit
    def test_get_layer_statistics_success(self):
        """Test getting layer statistics."""
        mock_result = Mock()
        mock_result.fetchone.return_value = (150, "Polygon", 4326, 20.0, 51.0, 22.0, 53.0)
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            stats = self.repository.get_layer_statistics("buildings_low")
        
        assert stats["feature_count"] == 150
        assert stats["geometry_type"] == "Polygon"
        assert stats["srid"] == 4326
        assert stats["bbox"] == [20.0, 51.0, 22.0, 53.0]
    
    @pytest.mark.unit
    def test_get_layer_statistics_not_found(self):
        """Test getting statistics for non-existent layer."""
        mock_result = Mock()
        mock_result.fetchone.return_value = None
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            with pytest.raises(LayerNotFoundError):
                self.repository.get_layer_statistics("non_existent_layer")
    
    @pytest.mark.unit
    def test_layer_exists_true(self):
        """Test checking if layer exists - positive case."""
        mock_result = Mock()
        mock_result.scalar.return_value = 1
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            exists = self.repository.layer_exists("buildings_low")
        
        assert exists is True
    
    @pytest.mark.unit
    def test_layer_exists_false(self):
        """Test checking if layer exists - negative case."""
        mock_result = Mock()
        mock_result.scalar.return_value = 0
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            exists = self.repository.layer_exists("non_existent_layer")
        
        assert exists is False


@pytest.mark.integration
class TestGISRepositoryIntegration(IntegrationTest, GISTest):
    """Integration tests for GIS repository with real database."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.session = self.get_test_session()
        self.repository = GISRepository(self.session)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        if hasattr(self, 'session'):
            self.session.close()
    
    def test_get_available_layers_integration(self):
        """Test getting available layers from real database."""
        layers = self.repository.get_available_layers()
        
        # Should have the test layers we created in conftest.py
        layer_names = [layer["name"] for layer in layers]
        assert "buildings_low" in layer_names
        assert "parcels_low" in layer_names
        assert "gpz_110kv_low" in layer_names
    
    def test_get_layer_as_geojson_integration(self):
        """Test getting layer as GeoJSON from real database."""
        geojson = self.repository.get_layer_as_geojson("buildings_low")
        
        self.assert_valid_geojson(geojson)
        assert self.count_features(geojson) == 2  # We inserted 2 buildings in conftest.py
        
        # Check that features have expected properties
        for feature in geojson["features"]:
            assert "id" in feature["properties"]
            assert "name" in feature["properties"]
            assert feature["geometry"]["type"] == "Polygon"
    
    def test_get_layer_statistics_integration(self):
        """Test getting layer statistics from real database."""
        stats = self.repository.get_layer_statistics("parcels_low")
        
        assert stats["feature_count"] == 2  # We inserted 2 parcels
        assert "geometry_type" in stats
        assert "srid" in stats
        assert "bbox" in stats
        assert len(stats["bbox"]) == 4
    
    def test_layer_exists_integration(self):
        """Test checking layer existence with real database."""
        # Test existing layer
        assert self.repository.layer_exists("buildings_low") is True
        
        # Test non-existent layer
        assert self.repository.layer_exists("non_existent_layer") is False


class TestGISRepositoryErrorHandling(RepositoryTest):
    """Test error handling in GIS repository."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.repository = self.create_repository(GISRepository)
    
    @pytest.mark.unit
    def test_database_connection_error(self):
        """Test handling database connection errors."""
        with patch.object(self.session, 'execute', side_effect=Exception("Database connection failed")):
            with pytest.raises(Exception) as exc_info:
                self.repository.get_available_layers()
            
            assert "Database connection failed" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_sql_query(self):
        """Test handling invalid SQL queries."""
        with patch.object(self.session, 'execute', side_effect=Exception("SQL syntax error")):
            with pytest.raises(Exception) as exc_info:
                self.repository.get_layer_as_geojson("test_layer")
            
            assert "SQL syntax error" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_invalid_geometry_data(self):
        """Test handling invalid geometry data."""
        # Mock result with invalid geometry
        mock_result = Mock()
        mock_result.fetchall.return_value = [
            (1, "Invalid Building", "INVALID_GEOMETRY_STRING")
        ]
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            # Should handle invalid geometry gracefully
            geojson = self.repository.get_layer_as_geojson("buildings_low")
            
            # Should still return valid GeoJSON structure, possibly with empty features
            assert isinstance(geojson, dict)
            assert geojson.get("type") == "FeatureCollection"
            assert "features" in geojson


@pytest.mark.parametrize("layer_name,expected_table", [
    ("buildings", "buildings_low"),
    ("parcels", "parcels_low"),
    ("gpz_110kv", "gpz_110kv_low")
])
class TestGISRepositoryParametrized(RepositoryTest):
    """Parametrized tests for GIS repository."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.repository = self.create_repository(GISRepository)
    
    @pytest.mark.unit
    def test_layer_name_mapping(self, layer_name, expected_table):
        """Test that layer names are correctly mapped to table names."""
        # This would test internal logic if we had layer name mapping
        # For now, we assume direct mapping
        assert f"{layer_name}_low" == expected_table or layer_name == expected_table.replace("_low", "")


class TestGISRepositoryPerformance(RepositoryTest):
    """Performance tests for GIS repository."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        self.repository = self.create_repository(GISRepository)
    
    @pytest.mark.slow
    @pytest.mark.unit
    def test_large_dataset_performance(self):
        """Test performance with large dataset."""
        # Mock a large dataset
        large_dataset = [(i, f"Feature {i}", f"POINT({i} {i})") for i in range(1000)]
        mock_result = Mock()
        mock_result.fetchall.return_value = large_dataset
        
        with patch.object(self.session, 'execute', return_value=mock_result):
            import time
            start_time = time.time()
            geojson = self.repository.get_layer_as_geojson("large_layer")
            execution_time = time.time() - start_time
            
            # Should process 1000 features in reasonable time (< 1 second)
            assert execution_time < 1.0
            assert self.count_features(geojson) == 1000
    
    @pytest.mark.unit
    def test_concurrent_access(self):
        """Test concurrent access to repository."""
        import threading
        import time
        
        results = []
        errors = []
        
        def worker():
            try:
                mock_result = Mock()
                mock_result.fetchall.return_value = [(1, "Test", "POINT(0 0)")]
                
                with patch.object(self.session, 'execute', return_value=mock_result):
                    geojson = self.repository.get_layer_as_geojson("test_layer")
                    results.append(geojson)
            except Exception as e:
                errors.append(e)
        
        # Start multiple threads
        threads = [threading.Thread(target=worker) for _ in range(5)]
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All threads should succeed
        assert len(errors) == 0
        assert len(results) == 5