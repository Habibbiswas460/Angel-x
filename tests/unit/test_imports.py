"""
Unit tests for __init__.py files
Ensures proper module initialization
"""

import pytest


@pytest.mark.unit
class TestModuleImports:
    """Test module imports"""
    
    def test_database_imports(self):
        """Test database module imports"""
        try:
            from src.database import Base, get_session, init_database
            assert Base is not None
            assert get_session is not None
            assert init_database is not None
        except ImportError as e:
            pytest.fail(f"Failed to import database modules: {e}")
    
    def test_model_imports(self):
        """Test model imports"""
        try:
            from src.database.models import Trade, Performance, MarketData, AccountHistory
            assert Trade is not None
            assert Performance is not None
            assert MarketData is not None
            assert AccountHistory is not None
        except ImportError as e:
            pytest.fail(f"Failed to import models: {e}")
    
    def test_enum_imports(self):
        """Test enum imports"""
        try:
            from src.database.models.trade import TradeStatus, TradeDirection, OptionType
            assert TradeStatus is not None
            assert TradeDirection is not None
            assert OptionType is not None
        except ImportError as e:
            pytest.fail(f"Failed to import enums: {e}")
