"""
Unit tests for Position Sizing Engine
Tests: Capital allocation, risk calculation, position sizing logic
"""

import pytest
from src.core.position_sizing import PositionSizing
from tests.fixtures.market_data import MockTick, MockGreeks


@pytest.mark.unit
class TestPositionSizing:
    """Test position sizing calculations"""
    
    def test_calculate_position_size_basic(self, mock_config):
        """Test basic position size calculation"""
        ps = PositionSizing(mock_config)
        
        # Entry at 100, SL at 92 = 8% risk
        entry_price = 100.0
        sl_price = 92.0
        capital = 100000
        risk_percent = 0.02  # 2% of capital
        
        position_size = ps.calculate_position_size(
            entry_price=entry_price,
            sl_price=sl_price,
            capital=capital,
            risk_percent=risk_percent
        )
        
        assert position_size > 0
        # Risk amount = 100000 * 0.02 = 2000
        # Per unit loss = 100 - 92 = 8
        # Position size = 2000 / 8 = 250 units
        expected = 250
        assert position_size == expected
    
    def test_position_size_respects_max_limit(self, mock_config):
        """Test position size doesn't exceed max"""
        ps = PositionSizing(mock_config)
        mock_config.MAX_POSITION_SIZE = 100
        
        entry_price = 100.0
        sl_price = 95.0
        capital = 100000
        risk_percent = 0.05  # High risk
        
        position_size = ps.calculate_position_size(
            entry_price=entry_price,
            sl_price=sl_price,
            capital=capital,
            risk_percent=risk_percent,
            max_size=100
        )
        
        assert position_size <= 100
    
    def test_position_size_with_extreme_sl(self, mock_config):
        """Test rejection when SL is too far"""
        ps = PositionSizing(mock_config)
        
        entry_price = 100.0
        sl_price = 80.0  # 20% SL - too much
        capital = 100000
        risk_percent = 0.02
        max_sl_percent = 0.08  # 8% max
        
        position_size = ps.calculate_position_size(
            entry_price=entry_price,
            sl_price=sl_price,
            capital=capital,
            risk_percent=risk_percent,
            max_sl_percent=max_sl_percent
        )
        
        # Should return 0 or None for invalid SL
        assert position_size == 0 or position_size is None
    
    def test_daily_loss_protection(self, mock_config):
        """Test daily loss limit enforcement"""
        ps = PositionSizing(mock_config)
        
        daily_loss = 2000
        max_daily_loss = 3000
        capital = 100000
        risk_percent = 0.02
        
        available_risk = ps.get_available_risk(
            daily_loss=daily_loss,
            max_daily_loss=max_daily_loss
        )
        
        assert available_risk > 0
        assert available_risk <= (max_daily_loss - daily_loss)
    
    def test_consecutive_loss_cooldown(self, mock_config):
        """Test cooldown after consecutive losses"""
        ps = PositionSizing(mock_config)
        ps.consecutive_losses = 2
        ps.max_consecutive_losses = 2
        ps.cooldown_minutes = 15
        
        can_trade = ps.can_trade_after_losses()
        assert can_trade is False
    
    def test_lot_size_alignment(self, mock_config):
        """Test position size aligns with minimum lot size"""
        ps = PositionSizing(mock_config)
        mock_config.MINIMUM_LOT_SIZE = 75
        
        calculated_size = 250  # Not multiple of 75
        aligned_size = ps.align_to_lot_size(calculated_size)
        
        assert aligned_size % 75 == 0
        assert aligned_size <= calculated_size  # Should round down to safety
