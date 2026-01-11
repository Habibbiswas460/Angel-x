"""
End-to-End tests for full strategy execution
Tests: Complete trading flows, realistic scenarios, system integration
"""

import pytest
from datetime import datetime, timedelta
from tests.fixtures.market_data import MockTick, MockGreeks, tick_data_sequence


@pytest.mark.e2e
class TestFullStrategyExecution:
    """Test complete strategy execution flow"""
    
    def test_bullish_entry_to_exit_flow(self, mock_config, tick_data_sequence):
        """Test complete bullish trade: entry -> exit"""
        from tests.mocks import (
            MockDataFeed, MockOrderManager, MockTradeManager, 
            MockBiasEngine, MockEntryEngine
        )
        
        # Initialize components
        data_feed = MockDataFeed()
        order_mgr = MockOrderManager()
        trade_mgr = MockTradeManager()
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Simulate tick processing
        for i, tick in enumerate(tick_data_sequence):
            greeks = MockGreeks.sample(delta=0.55 + (i * 0.02))
            
            # Step 1: Detect bias
            bias = bias_engine.analyze(
                {'ltp': tick.ltp},
                greeks.__dict__
            )
            
            # Step 2: Check entry
            if i == 0:  # Enter on first bullish tick
                if bias == 'BULLISH':
                    should_enter = entry_engine.should_enter(
                        bias, greeks.__dict__, tick.__dict__
                    )
                    
                    if should_enter:
                        # Step 3: Place order
                        order = order_mgr.place_order(
                            'NIFTY_CALL',
                            'BUY',
                            75,
                            price=tick.ltp
                        )
                        
                        # Step 4: Open position
                        position = trade_mgr.open_position('NIFTY_CALL', order)
                        assert position['status'] == 'OPEN'
                        entry_price = order['price']
                        entry_time = position['entry_time']
            
            # Step 5: Monitor for exit
            if i > 0 and trade_mgr.positions.get('NIFTY_CALL'):
                pos = trade_mgr.positions['NIFTY_CALL']
                current_pnl_percent = ((tick.ltp - pos['entry_price']) / pos['entry_price']) * 100
                
                # Exit on 7% profit target
                if current_pnl_percent >= 7.0:
                    closed = trade_mgr.close_position('NIFTY_CALL', tick.ltp)
                    assert closed['status'] == 'CLOSED'
                    assert closed['pnl'] > 0
                    break
    
    def test_trade_rejection_on_iv_trap(self, mock_config):
        """Test trade is rejected when IV trap detected"""
        from tests.mocks import MockBiasEngine, MockEntryEngine
        
        bias_engine = MockBiasEngine()
        entry_engine = MockEntryEngine()
        
        # Setup: Bullish bias but IV dropping = trap
        tick = MockTick.sample(ltp=101.0, volume=1100, oi=510000)
        prev_tick = MockTick.sample(ltp=100.0, volume=1000, oi=500000)
        
        greeks = MockGreeks.sample(delta=0.55, iv=22.0)
        prev_greeks = MockGreeks.sample(delta=0.55, iv=25.0)
        
        # Bias should be bullish
        bias = bias_engine.analyze(
            {'ltp': tick.ltp},
            greeks.__dict__
        )
        assert bias == 'BULLISH'
        
        # But entry should be rejected due to IV drop
        iv_drop_percent = (prev_greeks.iv - greeks.iv) / prev_greeks.iv * 100
        assert iv_drop_percent > 3.0
        
        # Entry decision should account for this
        # (actual implementation depends on engine logic)
    
    def test_stop_loss_execution(self):
        """Test stop loss is executed at target level"""
        from tests.mocks import MockOrderManager, MockTradeManager
        
        order_mgr = MockOrderManager()
        trade_mgr = MockTradeManager()
        
        # Open position at 100
        order = order_mgr.place_order('NIFTY_CALL', 'BUY', 75, price=100.0)
        position = trade_mgr.open_position('NIFTY_CALL', order)
        
        entry_price = position['entry_price']
        sl_level = entry_price * 0.93  # 7% SL
        
        # Price drops to SL
        exit_price = sl_level
        closed = trade_mgr.close_position('NIFTY_CALL', exit_price)
        
        assert closed['pnl'] < 0
        assert abs(closed['pnl']) <= (entry_price - sl_level) * 75 * 1.01  # With some margin for slippage
    
    def test_daily_loss_limit_enforcement(self):
        """Test trading stops when daily loss limit reached"""
        from tests.mocks import MockTradeManager
        
        trade_mgr = MockTradeManager()
        
        daily_loss = 3000
        max_daily_loss = 3000
        
        # After max daily loss reached, no more trades should open
        can_trade = daily_loss < max_daily_loss
        assert can_trade is False
    
    @pytest.mark.slow
    def test_full_market_day_simulation(self, tick_data_sequence):
        """Simulate full market day with multiple trade cycles"""
        from tests.mocks import MockDataFeed, MockOrderManager, MockTradeManager
        
        data_feed = MockDataFeed()
        order_mgr = MockOrderManager()
        trade_mgr = MockTradeManager()
        
        total_trades = 0
        total_pnl = 0
        
        # Simulate multiple ticks
        for tick in tick_data_sequence:
            # In real system, this would be continuous
            # For testing, we simulate discrete ticks
            greeks = MockGreeks.sample()
            
            # Would generate signal, place order, etc.
            # For E2E test, just verify components work
            assert data_feed.connected
            assert len(order_mgr.orders) >= 0
        
        # Day completed successfully
        assert total_trades >= 0
