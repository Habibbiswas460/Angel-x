"""
Root conftest.py - Shared fixtures and configuration for all tests
"""

import os
import sys
from pathlib import Path

import pytest

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment setup
os.environ['TESTING'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration"""
    from config import config
    return config


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory"""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def test_data_dir():
    """Get test data directory"""
    data_dir = PROJECT_ROOT / "tests" / "fixtures" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def mock_logger():
    """Create mock logger"""
    import logging
    return logging.getLogger("test")


@pytest.fixture
def mock_config():
    """Create mock config with defaults"""
    class MockConfig:
        CAPITAL = 100000
        RISK_PER_TRADE_MAX = 0.05
        MAX_CONCURRENT_POSITIONS = 1
        HARD_SL_PERCENT_MAX = 0.08
        IDEAL_DELTA_CALL = (0.45, 0.65)
        IDEAL_DELTA_PUT = (-0.65, -0.45)
        IDEAL_GAMMA_MIN = 0.002
        PRIMARY_UNDERLYING = "NIFTY"
        OPTION_EXPIRY = "weekly"
        
    return MockConfig()


# Markers configuration
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "smoke: mark test as smoke test"
    )


# Test collection hooks
def pytest_collection_modifyitems(config, items):
    """Modify collected tests based on markers"""
    for item in items:
        # Mark all tests in unit/ as unit tests
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        # Mark all tests in integration/ as integration tests
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        # Mark all tests in e2e/ as e2e tests
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
