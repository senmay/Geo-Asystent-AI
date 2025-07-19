"""
Unit tests for configuration management.
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any

from tests.base import UnitTest
from config.settings import get_settings, Settings
from config.database import get_database_url, create_engine_with_settings
from config.validation import validate_environment, validate_database_connection
from exceptions.base import ConfigurationError


class TestSettings(UnitTest):
    """Test application settings."""
    
    def setup_method(self):
        """Setup for each test method."""
        super().setup_method()
        # Store original environment variables
        self.original_env = dict(os.environ)
    
    def teardown_method(self):
        """Cleanup after each test method."""
        # Restore original environment variables
        os.environ.clear()
        os.environ.update(self.original_env)
    
    @pytest.mark.unit
    def test_settings_default_values(self):
        """Test settings with default values."""
        # Clear environment variables
        for key in list(os.environ.keys()):
            if key.startswith(('DB_', 'LLM_', 'API_')):
                del os.environ[key]
        
        # Act
        settings = Settings()
        
        # Assert
        assert settings.debug is False
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.cors_origins == ["*"]
    
    @pytest.mark.unit
    def test_settings_from_environment(self):
        """Test settings loaded from environment variables."""
        # Arrange
        os.environ.update({
            'DEBUG': 'true',
            'API_HOST': '127.0.0.1',
            'API_PORT': '9000',
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'test_db',
            'DB_USER': 'test_user',
            'DB_PASSWORD': 'test_pass',
            'LLM_API_KEY': 'test-api-key',
            'LLM_MODEL': 'test-model',
            'LLM_TEMPERATURE': '0.5'
        })
        
        # Act
        settings = Settings()
        
        # Assert
        assert settings.debug is True
        assert settings.api_host == "127.0.0.1"
        assert settings.api_port == 9000
        assert settings.database.host == "localhost"
        assert settings.database.port == 5432
        assert settings.database.name == "test_db"
        assert settings.database.user == "test_user"
        assert settings.database.password == "test_pass"
        assert settings.llm.api_key == "test-api-key"
        assert settings.llm.model == "test-model"
        assert settings.llm.temperature == 0.5
    
    @pytest.mark.unit
    def test_settings_validation_missing_required(self):
        """Test settings validation with missing required fields."""
        # Arrange - clear required environment variables
        for key in ['DB_HOST', 'DB_NAME', 'DB_USER', 'DB_PASSWORD', 'LLM_API_KEY']:
            os.environ.pop(key, None)
        
        # Act & Assert
        with pytest.raises(ValueError):
            Settings()
    
    @pytest.mark.unit
    def test_settings_validation_invalid_types(self):
        """Test settings validation with invalid types."""
        # Arrange
        os.environ.update({
            'API_PORT': 'not_a_number',
            'DB_PORT': 'invalid_port',
            'LLM_TEMPERATURE': 'not_a_float'
        })
        
        # Act & Assert
        with pytest.raises(ValueError):
            Settings()
    
    @pytest.mark.unit
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        # Act
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Assert
        assert settings1 is settings2
    
    @pytest.mark.unit
    def test_settings_database_url_construction(self):
        """Test database URL construction."""
        # Arrange
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_PORT': '5432',
            'DB_NAME': 'testdb',
            'DB_USER': 'testuser',
            'DB_PASSWORD': 'testpass'
        })
        
        # Act
        settings = Settings()
        db_url = get_database_url(settings.database)
        
        # Assert
        expected_url = "postgresql://testuser:testpass@localhost:5432/testdb"
        assert db_url == expected_url
    
    @pytest.mark.unit
    def test_settings_cors_origins_parsing(self):
        """Test CORS origins parsing from environment."""
        # Arrange
        os.environ['CORS_ORIGINS'] = 'http://localhost:3000,https://example.com'
        
        # Act
        settings = Settings()
        
        # Assert
        assert settings.cors_origins == ['http://localhost:3000', 'https://example.com']


class TestDatabaseConfiguration(UnitTest):
    """Test database configuration."""
    
    @pytest.mark.unit
    def test_get_database_url_with_all_params(self):
        """Test database URL generation with all parameters."""
        # Arrange
        from config.database import DatabaseSettings
        db_config = DatabaseSettings(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password="testpass"
        )
        
        # Act
        url = get_database_url(db_config)
        
        # Assert
        assert url == "postgresql://testuser:testpass@localhost:5432/testdb"
    
    @pytest.mark.unit
    def test_get_database_url_with_special_characters(self):
        """Test database URL generation with special characters in password."""
        # Arrange
        from config.database import DatabaseSettings
        db_config = DatabaseSettings(
            host="localhost",
            port=5432,
            name="testdb",
            user="testuser",
            password="test@pass#123"
        )
        
        # Act
        url = get_database_url(db_config)
        
        # Assert
        # Password should be URL encoded
        assert "test%40pass%23123" in url
    
    @pytest.mark.unit
    @patch('config.database.create_engine')
    def test_create_engine_with_settings(self, mock_create_engine):
        """Test engine creation with settings."""
        # Arrange
        mock_engine = Mock()
        mock_create_engine.return_value = mock_engine
        
        settings = get_settings()
        
        # Act
        engine = create_engine_with_settings(settings)
        
        # Assert
        assert engine == mock_engine
        mock_create_engine.assert_called_once()
        
        # Check that the call included proper connection parameters
        call_args = mock_create_engine.call_args
        assert 'pool_size' in call_args[1]
        assert 'max_overflow' in call_args[1]


class TestConfigurationValidation(UnitTest):
    """Test configuration validation."""
    
    @pytest.mark.unit
    def test_validate_environment_success(self):
        """Test successful environment validation."""
        # Arrange
        required_vars = ['DB_HOST', 'DB_NAME', 'LLM_API_KEY']
        os.environ.update({
            'DB_HOST': 'localhost',
            'DB_NAME': 'testdb',
            'LLM_API_KEY': 'test-key'
        })
        
        # Act
        result = validate_environment(required_vars)
        
        # Assert
        assert result is True
    
    @pytest.mark.unit
    def test_validate_environment_missing_vars(self):
        """Test environment validation with missing variables."""
        # Arrange
        required_vars = ['MISSING_VAR', 'ANOTHER_MISSING_VAR']
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            validate_environment(required_vars)
        
        assert "Missing required environment variables" in str(exc_info.value)
        assert "MISSING_VAR" in str(exc_info.value)
    
    @pytest.mark.unit
    @patch('config.validation.create_engine')
    def test_validate_database_connection_success(self, mock_create_engine):
        """Test successful database connection validation."""
        # Arrange
        mock_engine = Mock()
        mock_connection = Mock()
        mock_engine.connect.return_value.__enter__.return_value = mock_connection
        mock_create_engine.return_value = mock_engine
        
        # Act
        result = validate_database_connection("postgresql://user:pass@localhost/db")
        
        # Assert
        assert result is True
        mock_engine.connect.assert_called_once()
    
    @pytest.mark.unit
    @patch('config.validation.create_engine')
    def test_validate_database_connection_failure(self, mock_create_engine):
        """Test database connection validation failure."""
        # Arrange
        mock_create_engine.side_effect = Exception("Connection failed")
        
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            validate_database_connection("invalid://connection/string")
        
        assert "Database connection failed" in str(exc_info.value)


class TestConfigurationEdgeCases(UnitTest):
    """Test configuration edge cases."""
    
    @pytest.mark.unit
    def test_settings_with_empty_strings(self):
        """Test settings behavior with empty string values."""
        # Arrange
        os.environ.update({
            'DB_HOST': '',
            'API_HOST': '',
            'LLM_MODEL': ''
        })
        
        # Act & Assert
        with pytest.raises(ValueError):
            Settings()
    
    @pytest.mark.unit
    def test_settings_with_whitespace_values(self):
        """Test settings behavior with whitespace values."""
        # Arrange
        os.environ.update({
            'DB_HOST': '  localhost  ',
            'DB_NAME': '\ttestdb\n',
            'LLM_MODEL': ' test-model '
        })
        
        # Act
        settings = Settings()
        
        # Assert - values should be stripped
        assert settings.database.host == "localhost"
        assert settings.database.name == "testdb"
        assert settings.llm.model == "test-model"
    
    @pytest.mark.unit
    def test_settings_boolean_parsing(self):
        """Test boolean value parsing from environment."""
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('1', True),
            ('yes', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('0', False),
            ('no', False),
            ('', False)
        ]
        
        for env_value, expected in test_cases:
            # Arrange
            os.environ['DEBUG'] = env_value
            
            # Act
            settings = Settings()
            
            # Assert
            assert settings.debug == expected, f"Failed for value: {env_value}"
    
    @pytest.mark.unit
    def test_settings_numeric_bounds(self):
        """Test numeric value bounds validation."""
        # Test port bounds
        invalid_ports = ['-1', '0', '65536', '100000']
        for port in invalid_ports:
            os.environ['API_PORT'] = port
            with pytest.raises(ValueError):
                Settings()
        
        # Test valid ports
        valid_ports = ['1', '8000', '65535']
        for port in valid_ports:
            os.environ['API_PORT'] = port
            settings = Settings()
            assert 1 <= settings.api_port <= 65535
    
    @pytest.mark.unit
    def test_settings_temperature_bounds(self):
        """Test LLM temperature bounds validation."""
        # Test invalid temperatures
        invalid_temps = ['-0.1', '2.1', '-1', '3']
        for temp in invalid_temps:
            os.environ['LLM_TEMPERATURE'] = temp
            with pytest.raises(ValueError):
                Settings()
        
        # Test valid temperatures
        valid_temps = ['0.0', '0.5', '1.0', '2.0']
        for temp in valid_temps:
            os.environ['LLM_TEMPERATURE'] = temp
            settings = Settings()
            assert 0.0 <= settings.llm.temperature <= 2.0


@pytest.mark.parametrize("env_var,setting_path,test_value", [
    ('DEBUG', 'debug', 'true'),
    ('API_HOST', 'api_host', '192.168.1.1'),
    ('API_PORT', 'api_port', '9000'),
    ('DB_HOST', 'database.host', 'db.example.com'),
    ('DB_PORT', 'database.port', '3306'),
    ('LLM_MODEL', 'llm.model', 'gpt-4'),
    ('LLM_TEMPERATURE', 'llm.temperature', '0.7')
])
class TestSettingsParametrized(UnitTest):
    """Parametrized tests for settings."""
    
    @pytest.mark.unit
    def test_environment_variable_mapping(self, env_var, setting_path, test_value):
        """Test that environment variables map correctly to settings."""
        # Arrange
        os.environ[env_var] = test_value
        
        # Act
        settings = Settings()
        
        # Assert
        # Navigate to nested setting using dot notation
        current = settings
        for part in setting_path.split('.'):
            current = getattr(current, part)
        
        # Convert expected value to appropriate type
        if env_var in ['DEBUG']:
            expected = test_value.lower() == 'true'
        elif env_var in ['API_PORT', 'DB_PORT']:
            expected = int(test_value)
        elif env_var in ['LLM_TEMPERATURE']:
            expected = float(test_value)
        else:
            expected = test_value
        
        assert current == expected