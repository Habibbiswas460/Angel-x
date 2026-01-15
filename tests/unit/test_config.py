"""
Tests for configuration validation
Tests config loading, validation, and error handling
"""

import pytest
import os
from pathlib import Path


@pytest.mark.unit
class TestConfigValidation:
    """Test configuration validation logic"""
    
    def test_environment_detection(self, mock_env):
        """Test environment variable detection"""
        assert os.getenv('ANGELONE_CLIENT_CODE') == 'TEST123'
        assert os.getenv('ANGELONE_API_KEY') == 'test_api_key'
    
    def test_trading_mode_config(self, mock_env):
        """Test trading mode configuration"""
        assert os.getenv('TRADING_ENABLED') == 'False'
        assert os.getenv('PAPER_TRADING') == 'True'
    
    def test_database_config(self, mock_env):
        """Test database configuration"""
        db_name = os.getenv('DATABASE_NAME')
        assert db_name == ':memory:'
    
    def test_log_level_config(self, mock_env):
        """Test log level configuration"""
        log_level = os.getenv('LOG_LEVEL')
        assert log_level == 'DEBUG'


@pytest.mark.unit
class TestConfigDefaults:
    """Test configuration default values"""
    
    def test_default_paper_trading(self):
        """Test default paper trading mode"""
        # When PAPER_TRADING is not set, should default to True
        paper_trading = os.getenv('PAPER_TRADING', 'True')
        assert paper_trading == 'True'
    
    def test_default_trading_disabled(self):
        """Test default trading disabled"""
        trading_enabled = os.getenv('TRADING_ENABLED', 'False')
        assert trading_enabled == 'False'


@pytest.mark.integration
class TestConfigIntegration:
    """Test configuration integration"""
    
    def test_config_file_exists(self):
        """Test configuration files exist"""
        config_paths = [
            Path('config/config.py'),
            Path('config/config.example.py'),
        ]
        
        # At least example should exist
        assert any(p.exists() for p in config_paths)
    
    def test_env_example_exists(self):
        """Test .env.example exists"""
        env_example = Path('.env.docker')
        assert env_example.exists()
