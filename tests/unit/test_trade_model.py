"""
Unit tests for Trade model
Tests trade creation, validation, and business logic
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError

from src.database.models.trade import Trade, TradeStatus, TradeDirection, OptionType


@pytest.mark.unit
@pytest.mark.database
class TestTradeModel:
    """Test Trade model functionality"""
    
    def test_create_trade(self, db_session, sample_trade_data):
        """Test creating a new trade"""
        trade = Trade(**sample_trade_data)
        db_session.add(trade)
        db_session.commit()
        
        assert trade.id is not None
        assert trade.symbol == 'NIFTY'
        assert trade.strike_price == 22000.0
        assert trade.status == TradeStatus.OPEN
        assert trade.created_at is not None
    
    def test_trade_with_factory(self, create_trade):
        """Test creating trade using factory fixture"""
        trade = create_trade(symbol='BANKNIFTY', strike_price=48000.0)
        
        assert trade.id is not None
        assert trade.symbol == 'BANKNIFTY'
        assert trade.strike_price == 48000.0
    
    def test_trade_status_enum(self, create_trade):
        """Test trade status enumeration"""
        trade = create_trade(status=TradeStatus.OPEN)
        assert trade.status == TradeStatus.OPEN
        
        trade.status = TradeStatus.CLOSED
        assert trade.status == TradeStatus.CLOSED
    
    def test_trade_direction_enum(self, create_trade):
        """Test trade direction enumeration"""
        buy_trade = create_trade(direction=TradeDirection.BUY)
        assert buy_trade.direction == TradeDirection.BUY
        
        sell_trade = create_trade(direction=TradeDirection.SELL)
        assert sell_trade.direction == TradeDirection.SELL
    
    def test_option_type_enum(self, create_trade):
        """Test option type enumeration"""
        call_trade = create_trade(option_type=OptionType.CALL)
        assert call_trade.option_type == OptionType.CALL
        
        put_trade = create_trade(option_type=OptionType.PUT)
        assert put_trade.option_type == OptionType.PUT
    
    def test_trade_pnl_calculation(self, create_trade, closed_trade_data):
        """Test P&L calculations"""
        trade = create_trade(**closed_trade_data)
        
        # Gross P&L = (exit_price - entry_price) * quantity
        expected_gross = (165.0 - 150.0) * 50
        assert trade.gross_pnl == expected_gross
        
        # Net P&L = Gross P&L - Brokerage
        expected_net = expected_gross - 50.0
        assert trade.net_pnl == expected_net
    
    def test_trade_duration(self, create_trade, closed_trade_data):
        """Test trade duration calculation"""
        trade = create_trade(**closed_trade_data)
        
        duration = trade.exit_time - trade.entry_time
        assert duration.total_seconds() > 0
    
    def test_trade_greeks_entry(self, create_trade):
        """Test entry Greeks are stored"""
        trade = create_trade(
            entry_delta=0.55,
            entry_gamma=0.02,
            entry_theta=-0.5,
            entry_vega=0.3,
            entry_iv=15.5
        )
        
        assert trade.entry_delta == 0.55
        assert trade.entry_gamma == 0.02
        assert trade.entry_theta == -0.5
        assert trade.entry_vega == 0.3
        assert trade.entry_iv == 15.5
    
    def test_trade_greeks_exit(self, create_trade, closed_trade_data):
        """Test exit Greeks are stored"""
        trade = create_trade(**closed_trade_data)
        
        assert trade.exit_delta == 0.65
        assert trade.exit_iv == 14.8
    
    def test_trade_strategy_tracking(self, create_trade):
        """Test strategy tracking fields"""
        trade = create_trade(
            strategy='momentum',
            signal_strength=0.85,
            entry_reason='Strong bullish signal',
            exit_reason='Target reached'
        )
        
        assert trade.strategy == 'momentum'
        assert trade.signal_strength == 0.85
        assert trade.entry_reason == 'Strong bullish signal'
    
    def test_trade_to_dict(self, create_trade):
        """Test trade serialization to dict"""
        trade = create_trade()
        trade_dict = trade.to_dict()
        
        assert isinstance(trade_dict, dict)
        assert 'id' in trade_dict
        assert 'symbol' in trade_dict
        assert 'strike_price' in trade_dict
        assert trade_dict['symbol'] == 'NIFTY'
    
    def test_trade_repr(self, create_trade):
        """Test trade string representation"""
        trade = create_trade()
        repr_str = repr(trade)
        
        assert 'NIFTY' in repr_str
        assert '22000' in repr_str
        assert 'OPEN' in repr_str
    
    def test_trade_timestamps(self, create_trade):
        """Test automatic timestamp creation"""
        before = datetime.now()
        trade = create_trade()
        after = datetime.now()
        
        assert before <= trade.created_at <= after
        assert before <= trade.updated_at <= after
    
    def test_multiple_trades(self, create_trade):
        """Test creating multiple trades"""
        trade1 = create_trade(symbol='NIFTY', strike_price=22000.0)
        trade2 = create_trade(symbol='BANKNIFTY', strike_price=48000.0)
        trade3 = create_trade(symbol='NIFTY', strike_price=22100.0)
        
        assert trade1.id != trade2.id
        assert trade2.id != trade3.id
        assert trade1.symbol == trade3.symbol
        assert trade1.strike_price != trade3.strike_price
    
    def test_trade_update(self, create_trade, db_session):
        """Test updating trade fields"""
        trade = create_trade(status=TradeStatus.OPEN)
        original_updated_at = trade.updated_at
        
        # Update trade
        trade.status = TradeStatus.CLOSED
        trade.exit_time = datetime.now()
        trade.exit_price = 165.0
        db_session.commit()
        
        assert trade.status == TradeStatus.CLOSED
        assert trade.exit_price == 165.0
        # Updated timestamp should change
        assert trade.updated_at >= original_updated_at


@pytest.mark.unit
class TestTradeValidation:
    """Test trade validation logic"""
    
    def test_positive_strike_price(self, create_trade):
        """Test strike price must be positive"""
        with pytest.raises(Exception):
            create_trade(strike_price=-100.0)
    
    def test_positive_quantity(self, create_trade):
        """Test quantity must be positive"""
        with pytest.raises(Exception):
            create_trade(quantity=-50)
    
    def test_required_fields(self, db_session):
        """Test required fields cannot be null"""
        # Missing symbol should fail
        with pytest.raises(IntegrityError):
            trade = Trade(
                strike_price=22000.0,
                quantity=50,
                entry_price=150.0
            )
            db_session.add(trade)
            db_session.commit()


@pytest.mark.unit
@pytest.mark.parametrize('symbol,strike,expected_strike', [
    ('NIFTY', 22000.0, 22000.0),
    ('NIFTY', 22050.0, 22050.0),
    ('BANKNIFTY', 48000.0, 48000.0),
])
class TestTradeParametrized:
    """Parametrized trade tests"""
    
    def test_trade_creation_parametrized(self, create_trade, symbol, strike, expected_strike):
        """Test trade creation with different parameters"""
        trade = create_trade(symbol=symbol, strike_price=strike)
        assert trade.symbol == symbol
        assert trade.strike_price == expected_strike
