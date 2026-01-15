"""
Root conftest.py - Shared fixtures and configuration for all tests
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Generator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Environment setup
os.environ['TESTING'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'
os.environ['ENVIRONMENT'] = 'testing'
os.environ['DB_TYPE'] = 'sqlite'


# ============================================================================
# Session Configuration
# ============================================================================

def pytest_configure(config):
    """Configure pytest environment"""
    os.environ['ENVIRONMENT'] = 'testing'


@pytest.fixture(scope="session")
def test_config():
    """Load test configuration"""
    from config import config
    return config


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory"""
    return PROJECT_ROOT


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope='session')
def test_db_engine():
    """Create test database engine (session-scoped)"""
    from src.database.base import Base
    
    # Use in-memory SQLite for fast tests
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture(scope='function')
def db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create database session for each test (function-scoped)"""
    SessionLocal = sessionmaker(bind=test_db_engine)
    session = SessionLocal()
    
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@pytest.fixture(scope='function')
def clean_db(test_db_engine):
    """Clean database before each test"""
    from src.database.base import Base
    
    # Drop and recreate all tables
    Base.metadata.drop_all(test_db_engine)
    Base.metadata.create_all(test_db_engine)
    yield
    Base.metadata.drop_all(test_db_engine)


# ============================================================================
# Model Fixtures - Trade
# ============================================================================

@pytest.fixture
def sample_trade_data():
    """Sample trade data for testing"""
    from src.database.models.trade import OptionType, TradeDirection, TradeStatus
    
    return {
        'symbol': 'NIFTY',
        'option_type': OptionType.CALL,
        'strike_price': 22000.0,
        'expiry_date': datetime.now().date() + timedelta(days=7),
        'entry_time': datetime.now(),
        'entry_price': 150.0,
        'quantity': 50,
        'direction': TradeDirection.BUY,
        'status': TradeStatus.OPEN,
        'underlying_price_entry': 21950.0,
        'entry_iv': 15.5,
        'entry_delta': 0.55,
        'entry_gamma': 0.02,
        'entry_theta': -0.5,
        'entry_vega': 0.3,
        'strategy': 'momentum',
        'signal_strength': 0.85,
        'entry_reason': 'Strong bullish signal',
    }


@pytest.fixture
def create_trade(db_session, sample_trade_data):
    """Factory fixture to create trades"""
    from src.database.models.trade import Trade
    
    def _create_trade(**kwargs):
        trade_data = {**sample_trade_data, **kwargs}
        trade = Trade(**trade_data)
        db_session.add(trade)
        db_session.commit()
        db_session.refresh(trade)
        return trade
    return _create_trade


@pytest.fixture
def closed_trade_data(sample_trade_data):
    """Sample closed trade data"""
    from src.database.models.trade import TradeStatus
    
    return {
        **sample_trade_data,
        'status': TradeStatus.CLOSED,
        'exit_time': datetime.now() + timedelta(hours=2),
        'exit_price': 165.0,
        'exit_reason': 'Target reached',
        'underlying_price_exit': 22050.0,
        'exit_iv': 14.8,
        'exit_delta': 0.65,
        'gross_pnl': 750.0,
        'brokerage': 50.0,
        'net_pnl': 700.0,
    }


# ============================================================================
# Model Fixtures - Performance
# ============================================================================

@pytest.fixture
def sample_performance_data():
    """Sample performance data for testing"""
    return {
        'period': 'daily',
        'period_date': datetime.now().date(),
        'total_trades': 10,
        'winning_trades': 7,
        'losing_trades': 3,
        'win_rate': 70.0,
        'gross_pnl': 5000.0,
        'brokerage': 500.0,
        'net_pnl': 4500.0,
        'avg_win': 900.0,
        'avg_loss': -200.0,
        'largest_win': 1500.0,
        'largest_loss': -350.0,
        'profit_factor': 3.15,
        'sharpe_ratio': 1.8,
        'max_drawdown': -500.0,
        'capital_start': 100000.0,
        'capital_end': 104500.0,
    }


@pytest.fixture
def create_performance(db_session, sample_performance_data):
    """Factory fixture to create performance records"""
    from src.database.models.performance import Performance
    
    def _create_performance(**kwargs):
        perf_data = {**sample_performance_data, **kwargs}
        performance = Performance(**perf_data)
        db_session.add(performance)
        db_session.commit()
        db_session.refresh(performance)
        return performance
    return _create_performance


# ============================================================================
# Model Fixtures - Market Data
# ============================================================================

@pytest.fixture
def sample_market_data():
    """Sample market data for testing"""
    from src.database.models.trade import OptionType
    
    return {
        'symbol': 'NIFTY',
        'timestamp': datetime.now(),
        'interval': '1min',
        'open': 22000.0,
        'high': 22050.0,
        'low': 21980.0,
        'close': 22030.0,
        'volume': 1000000,
        'option_type': OptionType.CALL,
        'strike_price': 22000.0,
        'expiry_date': datetime.now().date() + timedelta(days=7),
        'iv': 15.5,
        'delta': 0.55,
        'gamma': 0.02,
        'theta': -0.5,
        'vega': 0.3,
        'bid': 149.5,
        'ask': 150.5,
        'underlying_price': 22030.0,
    }


@pytest.fixture
def create_market_data(db_session, sample_market_data):
    """Factory fixture to create market data records"""
    from src.database.models.market_data import MarketData
    
    def _create_market_data(**kwargs):
        data = {**sample_market_data, **kwargs}
        market_data = MarketData(**data)
        db_session.add(market_data)
        db_session.commit()
        db_session.refresh(market_data)
        return market_data
    return _create_market_data


# ============================================================================
# Model Fixtures - Account History
# ============================================================================

@pytest.fixture
def sample_account_data():
    """Sample account history data for testing"""
    from src.database.models.account import TransactionType
    
    return {
        'transaction_type': TransactionType.TRADE_PROFIT,
        'amount': 700.0,
        'balance_before': 100000.0,
        'balance_after': 100700.0,
        'description': 'Profit from NIFTY 22000 CE trade',
        'margin_used': 50000.0,
        'margin_available': 50700.0,
    }


@pytest.fixture
def create_account_history(db_session, sample_account_data):
    """Factory fixture to create account history records"""
    from src.database.models.account import AccountHistory
    
    def _create_account_history(**kwargs):
        data = {**sample_account_data, **kwargs}
        account = AccountHistory(**data)
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        return account
    return _create_account_history


# ============================================================================
# Configuration Fixtures
# ============================================================================

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables"""
    test_env = {
        'ANGELONE_CLIENT_CODE': 'TEST123',
        'ANGELONE_API_KEY': 'test_api_key',
        'DATABASE_NAME': ':memory:',
        'TRADING_ENABLED': 'False',
        'PAPER_TRADING': 'True',
        'LOG_LEVEL': 'DEBUG',
    }
    
    for key, value in test_env.items():
        monkeypatch.setenv(key, str(value))
    
    return test_env


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
