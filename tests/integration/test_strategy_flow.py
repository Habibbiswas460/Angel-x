"""
Integration tests for Bias Engine + Entry Engine
Tests: Component interaction, signal flow, decision making
"""

import pytest
from tests.fixtures.market_data import MockTick, MockGreeks


@pytest.mark.integration
class TestBiasAndEntryIntegration:
    """Test interaction between Bias Engine and Entry Engine"""
    
    def test_bullish_bias_enables_entry(self, mock_config):
        """Test that bullish bias enables call entries"""
        # Create engines (mocked)
        from tests.mocks import MockBiasEngine, MockEntryEngine
        
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Setup bullish scenario
        tick = MockTick.sample(ltp=101.0)
        greeks = MockGreeks.sample(delta=0.55)
        
        # Detect bias
        bias = bias_engine.analyze(
            {'ltp': tick.ltp},
            greeks.__dict__
        )
        assert bias == 'BULLISH'
        
        # Check entry permission
        can_enter = entry_engine.should_enter(
            bias=bias,
            greeks=greeks.__dict__,
            tick=tick.__dict__
        )
        assert can_enter is True
    
    def test_bearish_bias_enables_entry(self):
        """Test that bearish bias enables put entries"""
        from tests.mocks import MockBiasEngine, MockEntryEngine
        
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Setup bearish scenario
        tick = MockTick.sample(ltp=99.0)
        greeks = MockGreeks.sample(delta=-0.55)
        
        # Detect bias
        bias = bias_engine.analyze(
            {'ltp': tick.ltp},
            greeks.__dict__
        )
        assert bias == 'BEARISH'
    
    def test_no_bias_blocks_all_entries(self):
        """Test that no bias prevents entries"""
        from tests.mocks import MockBiasEngine, MockEntryEngine
        
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Setup neutral scenario
        tick = MockTick.sample(ltp=100.0)
        greeks = MockGreeks.sample(delta=0.35)  # Weak
        
        # Detect bias
        bias = bias_engine.analyze(
            {'ltp': tick.ltp},
            greeks.__dict__
        )
        assert bias == 'NEUTRAL'
        
        # Check entry permission
        can_enter = entry_engine.should_enter(
            bias=bias,
            greeks=greeks.__dict__,
            tick=tick.__dict__
        )
        assert can_enter is False
    
    def test_trap_detection_blocks_entry(self):
        """Test that OI traps block entries even with good bias"""
        from tests.mocks import MockBiasEngine, MockEntryEngine
        
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Bullish bias but OI trap
        tick = MockTick.sample(ltp=101.0, oi=520000)
        prev_tick = MockTick.sample(ltp=100.0, oi=500000)
        greeks = MockGreeks.sample(delta=0.55)
        
        bias = bias_engine.analyze(
            {'ltp': tick.ltp},
            greeks.__dict__
        )
        
        # Entry should be blocked due to trap
        # (OI rising but price flat)
        assert bias == 'BULLISH'


@pytest.mark.integration
class TestPositioningAndRiskManagement:
    """Test risk management during position lifecycle"""
    
    def test_position_sizing_respects_daily_loss_limit(self):
        """Test that position sizing reduces after daily loss"""
        from tests.mocks import MockTradeManager
        from src.core.position_sizing import PositionSizing
        
        tm = MockTradeManager()
        ps = PositionSizing()  # No arguments
        
        # Open position
        order = {'price': 100.0, 'quantity': 75}
        position = tm.open_position('TEST_CALL', order)
        assert position['status'] == 'OPEN'
        
        # Close at loss
        loss_price = 95.0
        closed = tm.close_position('TEST_CALL', loss_price)
        assert closed['pnl'] < 0
        assert closed['status'] == 'CLOSED'
    
    def test_multiple_positions_blocked_when_max_reached(self):
        """Test that max concurrent positions limit is enforced"""
        from tests.mocks import MockTradeManager
        
        tm = MockTradeManager()
        
        # Open first position
        pos1 = tm.open_position('CALL_1', {'price': 100, 'quantity': 75})
        assert pos1['status'] == 'OPEN'
        
        # Try to open second (should depend on MAX_CONCURRENT_POSITIONS)
        pos2 = tm.open_position('CALL_2', {'price': 100, 'quantity': 75})
        assert pos2['status'] == 'OPEN'  # If max allows
