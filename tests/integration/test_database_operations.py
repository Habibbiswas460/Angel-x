"""
Integration tests for database operations
Tests complex queries and database interactions
"""

import pytest
from datetime import datetime, timedelta, date
from sqlalchemy import func

from src.database.models.trade import Trade, TradeStatus, TradeDirection
from src.database.models.performance import Performance
from src.database.models.market_data import MarketData
from src.database.models.account import AccountHistory, TransactionType


@pytest.mark.integration
@pytest.mark.database
class TestTradeQueries:
    """Test complex trade queries"""
    
    def test_query_open_trades(self, create_trade, db_session):
        """Test querying open trades"""
        # Create mix of open and closed trades
        create_trade(status=TradeStatus.OPEN, symbol='NIFTY')
        create_trade(status=TradeStatus.OPEN, symbol='BANKNIFTY')
        create_trade(status=TradeStatus.CLOSED, symbol='NIFTY')
        
        open_trades = db_session.query(Trade).filter(
            Trade.status == TradeStatus.OPEN
        ).all()
        
        assert len(open_trades) == 2
        assert all(t.status == TradeStatus.OPEN for t in open_trades)
    
    def test_query_trades_by_symbol(self, create_trade, db_session):
        """Test querying trades by symbol"""
        create_trade(symbol='NIFTY')
        create_trade(symbol='NIFTY')
        create_trade(symbol='BANKNIFTY')
        
        nifty_trades = db_session.query(Trade).filter(
            Trade.symbol == 'NIFTY'
        ).all()
        
        assert len(nifty_trades) == 2
    
    def test_query_trades_by_date_range(self, create_trade, db_session):
        """Test querying trades within date range"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        
        create_trade(entry_time=today)
        create_trade(entry_time=yesterday)
        
        recent_trades = db_session.query(Trade).filter(
            Trade.entry_time >= yesterday
        ).all()
        
        assert len(recent_trades) == 2
    
    def test_calculate_total_pnl(self, create_trade, db_session, closed_trade_data):
        """Test calculating total P&L from trades"""
        create_trade(**closed_trade_data, net_pnl=700.0)
        create_trade(**closed_trade_data, net_pnl=500.0)
        create_trade(**closed_trade_data, net_pnl=-200.0)
        
        total_pnl = db_session.query(func.sum(Trade.net_pnl)).scalar()
        
        assert total_pnl == 1000.0  # 700 + 500 - 200
    
    def test_count_winning_trades(self, create_trade, db_session, closed_trade_data):
        """Test counting winning trades"""
        create_trade(**closed_trade_data, net_pnl=700.0)
        create_trade(**closed_trade_data, net_pnl=500.0)
        create_trade(**closed_trade_data, net_pnl=-200.0)
        
        winning_count = db_session.query(Trade).filter(
            Trade.net_pnl > 0
        ).count()
        
        assert winning_count == 2
    
    def test_average_trade_pnl(self, create_trade, db_session, closed_trade_data):
        """Test calculating average trade P&L"""
        create_trade(**closed_trade_data, net_pnl=700.0)
        create_trade(**closed_trade_data, net_pnl=500.0)
        create_trade(**closed_trade_data, net_pnl=-200.0)
        
        avg_pnl = db_session.query(func.avg(Trade.net_pnl)).scalar()
        
        expected_avg = (700.0 + 500.0 - 200.0) / 3
        assert abs(avg_pnl - expected_avg) < 0.01


@pytest.mark.integration
@pytest.mark.database
class TestPerformanceQueries:
    """Test performance data queries"""
    
    def test_query_daily_performance(self, create_performance, db_session):
        """Test querying daily performance"""
        create_performance(period='daily', period_date=date.today())
        create_performance(period='weekly', period_date=date.today())
        
        daily_perf = db_session.query(Performance).filter(
            Performance.period == 'daily'
        ).all()
        
        assert len(daily_perf) == 1
        assert daily_perf[0].period == 'daily'
    
    def test_query_performance_by_date(self, create_performance, db_session):
        """Test querying performance by specific date"""
        today = date.today()
        yesterday = today - timedelta(days=1)
        
        create_performance(period='daily', period_date=today, net_pnl=1000.0)
        create_performance(period='daily', period_date=yesterday, net_pnl=500.0)
        
        today_perf = db_session.query(Performance).filter(
            Performance.period_date == today
        ).first()
        
        assert today_perf.net_pnl == 1000.0
    
    def test_total_performance_over_period(self, create_performance, db_session):
        """Test calculating total performance over period"""
        for i in range(5):
            create_performance(
                period='daily',
                period_date=date.today() - timedelta(days=i),
                net_pnl=1000.0 * (i + 1)
            )
        
        total_pnl = db_session.query(func.sum(Performance.net_pnl)).scalar()
        
        # 1000 + 2000 + 3000 + 4000 + 5000 = 15000
        assert total_pnl == 15000.0


@pytest.mark.integration
@pytest.mark.database
class TestMarketDataQueries:
    """Test market data queries"""
    
    def test_query_latest_price(self, create_market_data, db_session):
        """Test querying latest market data"""
        now = datetime.now()
        
        create_market_data(symbol='NIFTY', timestamp=now - timedelta(minutes=2))
        create_market_data(symbol='NIFTY', timestamp=now - timedelta(minutes=1))
        latest = create_market_data(symbol='NIFTY', timestamp=now, close=22100.0)
        
        latest_data = db_session.query(MarketData).filter(
            MarketData.symbol == 'NIFTY'
        ).order_by(MarketData.timestamp.desc()).first()
        
        assert latest_data.close == 22100.0
    
    def test_query_ohlc_data(self, create_market_data, db_session):
        """Test querying OHLC data"""
        create_market_data(
            symbol='NIFTY',
            open=22000.0,
            high=22100.0,
            low=21950.0,
            close=22050.0
        )
        
        data = db_session.query(MarketData).filter(
            MarketData.symbol == 'NIFTY'
        ).first()
        
        assert data.open == 22000.0
        assert data.high == 22100.0
        assert data.low == 21950.0
        assert data.close == 22050.0


@pytest.mark.integration
@pytest.mark.database
class TestAccountQueries:
    """Test account history queries"""
    
    def test_query_by_transaction_type(self, create_account_history, db_session):
        """Test querying by transaction type"""
        create_account_history(transaction_type=TransactionType.TRADE_PROFIT)
        create_account_history(transaction_type=TransactionType.TRADE_LOSS)
        create_account_history(transaction_type=TransactionType.BROKERAGE)
        
        profit_txns = db_session.query(AccountHistory).filter(
            AccountHistory.transaction_type == TransactionType.TRADE_PROFIT
        ).all()
        
        assert len(profit_txns) == 1
    
    def test_calculate_total_brokerage(self, create_account_history, db_session):
        """Test calculating total brokerage"""
        create_account_history(
            transaction_type=TransactionType.BROKERAGE,
            amount=-50.0
        )
        create_account_history(
            transaction_type=TransactionType.BROKERAGE,
            amount=-75.0
        )
        
        total_brokerage = db_session.query(func.sum(AccountHistory.amount)).filter(
            AccountHistory.transaction_type == TransactionType.BROKERAGE
        ).scalar()
        
        assert total_brokerage == -125.0
    
    def test_balance_tracking(self, create_account_history, db_session):
        """Test balance tracking over time"""
        create_account_history(
            balance_before=100000.0,
            balance_after=100700.0,
            amount=700.0
        )
        
        latest_balance = db_session.query(AccountHistory).order_by(
            AccountHistory.created_at.desc()
        ).first()
        
        assert latest_balance.balance_after == 100700.0


@pytest.mark.integration
@pytest.mark.database
class TestCrossModelQueries:
    """Test queries across multiple models"""
    
    def test_trade_and_account_relationship(self, create_trade, create_account_history, db_session, closed_trade_data):
        """Test relationship between trades and account history"""
        trade = create_trade(**closed_trade_data)
        
        # Create account history linked to trade
        create_account_history(
            related_trade_id=trade.id,
            transaction_type=TransactionType.TRADE_PROFIT,
            amount=trade.net_pnl
        )
        
        account_txn = db_session.query(AccountHistory).filter(
            AccountHistory.related_trade_id == trade.id
        ).first()
        
        assert account_txn is not None
        assert account_txn.amount == trade.net_pnl
    
    def test_performance_aggregation_from_trades(self, create_trade, db_session, closed_trade_data):
        """Test aggregating performance from trades"""
        # Create multiple closed trades
        trades_data = [
            {**closed_trade_data, 'net_pnl': 700.0},
            {**closed_trade_data, 'net_pnl': 500.0},
            {**closed_trade_data, 'net_pnl': -200.0},
        ]
        
        for data in trades_data:
            create_trade(**data)
        
        # Aggregate statistics
        stats = db_session.query(
            func.count(Trade.id).label('total_trades'),
            func.sum(Trade.net_pnl).label('total_pnl'),
            func.avg(Trade.net_pnl).label('avg_pnl')
        ).filter(Trade.status == TradeStatus.CLOSED).first()
        
        assert stats.total_trades == 3
        assert stats.total_pnl == 1000.0
        assert abs(stats.avg_pnl - 333.33) < 0.01
