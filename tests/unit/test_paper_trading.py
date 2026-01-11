"""
Unit tests for Professional Paper Trading Engine
"""

import pytest
from datetime import datetime
from src.core.paper_trading import PaperTradingEngine, OrderStatus, PositionStatus


@pytest.mark.unit
class TestPaperTradingEngine:
    """Test paper trading engine"""
    
    @pytest.fixture
    def engine(self, mock_config):
        """Create paper trading engine"""
        return PaperTradingEngine()
    
    def test_engine_initialization(self, engine):
        """Test engine initializes with correct capital"""
        assert engine.initial_capital == 100000
        assert engine.current_capital == 100000
        assert engine.total_trades == 0
        assert len(engine.positions) == 0
    
    def test_buy_order_placement(self, engine):
        """Test placing a buy order"""
        success, order, message = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert success is True
        assert order.status == OrderStatus.FILLED
        assert order.filled_quantity == 75
        assert 'NIFTY' in order.symbol
    
    def test_order_rejection_low_capital(self, engine):
        """Test order rejection when insufficient capital"""
        engine.current_capital = 100  # Set very low capital
        engine.available_margin = 100  # Also update available margin
        
        success, order, message = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert success is False
        assert order.status == OrderStatus.REJECTED
        assert 'Insufficient margin' in order.rejected_reason
    
    def test_position_open_after_buy(self, engine):
        """Test position opens after buy order"""
        success, order, _ = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert success is True
        assert 'NIFTY_25JAN26_19000CE' in engine.positions
        position = engine.positions['NIFTY_25JAN26_19000CE']
        assert position.quantity == 75
        assert position.entry_price == order.average_price
    
    def test_position_close_on_sell(self, engine):
        """Test position closes when sell order placed"""
        # Buy first
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert len(engine.positions) == 1
        
        # Sell to close
        success, order, _ = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='SELL',
            quantity=75,
            price=107.0  # 7% profit
        )
        
        assert success is True
        assert len(engine.positions) == 0
        assert len(engine.closed_trades) == 1
        assert engine.total_trades == 1
    
    def test_slippage_calculation(self, engine):
        """Test slippage is calculated on orders"""
        success, order, _ = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert success is True
        assert order.slippage != 0
        assert abs(order.slippage) < 1.0  # Should be small
    
    def test_pnl_calculation(self, engine):
        """Test P&L calculation on closed trade"""
        # Buy
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        # Sell at profit
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='SELL',
            quantity=75,
            price=107.0
        )
        
        assert engine.gross_pnl > 0
        assert engine.winning_trades == 1
        assert engine.total_trades == 1
    
    def test_win_rate_calculation(self, engine):
        """Test win rate calculation"""
        # Place 2 winning trades
        for _ in range(2):
            engine.place_order(
                symbol='NIFTY_25JAN26_19000CE',
                action='BUY',
                quantity=75,
                price=100.0
            )
            engine.place_order(
                symbol='NIFTY_25JAN26_19000CE',
                action='SELL',
                quantity=75,
                price=107.0
            )
        
        stats = engine.get_statistics()
        assert stats['total_trades'] == 2
        assert stats['winning_trades'] == 2
        assert stats['win_rate'] == 100.0
    
    def test_max_drawdown_tracking(self, engine):
        """Test max drawdown is tracked"""
        # Take a loss
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='SELL',
            quantity=75,
            price=93.0  # 7% loss
        )
        
        stats = engine.get_statistics()
        assert stats['max_drawdown'] > 0
    
    def test_margin_tracking(self, engine):
        """Test margin utilization is tracked"""
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        stats = engine.get_statistics()
        assert stats['utilized_margin'] > 0
        assert stats['available_margin'] > 0
        assert stats['utilized_margin'] + stats['available_margin'] == engine.initial_capital
    
    def test_position_price_update(self, engine):
        """Test updating position price for real-time P&L"""
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        # Update price
        engine.update_position_price('NIFTY_25JAN26_19000CE', 105.0)
        
        position = engine.positions['NIFTY_25JAN26_19000CE']
        pnl_rupees, pnl_percent = position.calculate_pnl()
        assert pnl_rupees > 0
        assert pnl_percent > 0
    
    def test_invalid_order_rejection(self, engine):
        """Test invalid orders are rejected"""
        success, order, message = engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=0,  # Invalid quantity
            price=100.0
        )
        
        assert success is False
        assert 'Invalid quantity' in message
    
    def test_position_export(self, engine):
        """Test exporting positions"""
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        positions = engine.get_positions()
        assert len(positions) == 1
        assert positions[0]['symbol'] == 'NIFTY_25JAN26_19000CE'
    
    def test_engine_reset(self, engine):
        """Test resetting engine"""
        # Add some trades
        engine.place_order(
            symbol='NIFTY_25JAN26_19000CE',
            action='BUY',
            quantity=75,
            price=100.0
        )
        
        assert len(engine.orders) > 0
        
        # Reset
        engine.reset()
        
        assert engine.current_capital == engine.initial_capital
        assert len(engine.positions) == 0
        assert engine.total_trades == 0
