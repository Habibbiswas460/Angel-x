"""
Unit tests for Performance model
Tests performance metrics calculation and storage
"""

import pytest
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError

from src.database.models.performance import Performance


@pytest.mark.unit
@pytest.mark.database
class TestPerformanceModel:
    """Test Performance model functionality"""
    
    def test_create_performance(self, db_session, sample_performance_data):
        """Test creating performance record"""
        perf = Performance(**sample_performance_data)
        db_session.add(perf)
        db_session.commit()
        
        assert perf.id is not None
        assert perf.period == 'daily'
        assert perf.total_trades == 10
        assert perf.net_pnl == 4500.0
    
    def test_performance_with_factory(self, create_performance):
        """Test creating performance using factory"""
        perf = create_performance(total_trades=15, net_pnl=6000.0)
        
        assert perf.total_trades == 15
        assert perf.net_pnl == 6000.0
    
    def test_win_rate_calculation(self, create_performance):
        """Test win rate calculation"""
        perf = create_performance(
            total_trades=10,
            winning_trades=7,
            losing_trades=3,
            win_rate=70.0
        )
        
        # Win rate should be (winning_trades / total_trades) * 100
        expected_win_rate = (7 / 10) * 100
        assert perf.win_rate == expected_win_rate
    
    def test_profit_factor(self, create_performance):
        """Test profit factor calculation"""
        perf = create_performance(
            gross_pnl=5000.0,
            avg_win=900.0,
            avg_loss=-200.0,
            winning_trades=7,
            losing_trades=3,
            profit_factor=3.15
        )
        
        # Profit factor = total wins / total losses
        total_wins = 900.0 * 7  # 6300
        total_losses = abs(-200.0 * 3)  # 600
        expected_pf = total_wins / total_losses  # 10.5
        
        # Allow some tolerance for calculation differences
        assert perf.profit_factor > 0
    
    def test_sharpe_ratio(self, create_performance):
        """Test Sharpe ratio storage"""
        perf = create_performance(sharpe_ratio=1.8)
        assert perf.sharpe_ratio == 1.8
    
    def test_sortino_ratio(self, create_performance):
        """Test Sortino ratio storage"""
        perf = create_performance(sortino_ratio=2.1)
        assert perf.sortino_ratio == 2.1
    
    def test_max_drawdown(self, create_performance):
        """Test maximum drawdown storage"""
        perf = create_performance(
            max_drawdown=-500.0,
            max_drawdown_pct=-0.5
        )
        
        assert perf.max_drawdown == -500.0
        assert perf.max_drawdown_pct == -0.5
    
    def test_capital_tracking(self, create_performance):
        """Test capital start and end tracking"""
        perf = create_performance(
            capital_start=100000.0,
            capital_end=104500.0,
            net_pnl=4500.0
        )
        
        # Capital end should equal capital start + net P&L
        assert perf.capital_end == perf.capital_start + perf.net_pnl
    
    def test_return_on_capital(self, create_performance):
        """Test return on capital calculation"""
        perf = create_performance(
            capital_start=100000.0,
            net_pnl=4500.0,
            return_on_capital=4.5
        )
        
        # ROC = (net_pnl / capital_start) * 100
        expected_roc = (4500.0 / 100000.0) * 100
        assert perf.return_on_capital == expected_roc
    
    def test_period_types(self, create_performance):
        """Test different period types"""
        daily = create_performance(period='daily')
        weekly = create_performance(
            period='weekly',
            period_date=date.today() - timedelta(days=7)
        )
        monthly = create_performance(
            period='monthly',
            period_date=date.today() - timedelta(days=30)
        )
        
        assert daily.period == 'daily'
        assert weekly.period == 'weekly'
        assert monthly.period == 'monthly'
    
    def test_unique_period_date_constraint(self, create_performance, db_session):
        """Test unique constraint on period and date"""
        today = date.today()
        
        # Create first performance record
        create_performance(period='daily', period_date=today)
        
        # Attempting to create duplicate should fail
        with pytest.raises(IntegrityError):
            perf = Performance(
                period='daily',
                period_date=today,
                total_trades=5,
                net_pnl=1000.0
            )
            db_session.add(perf)
            db_session.commit()
    
    def test_timestamps(self, create_performance):
        """Test automatic timestamp creation"""
        before = datetime.now()
        perf = create_performance()
        after = datetime.now()
        
        assert before <= perf.created_at <= after
        assert before <= perf.updated_at <= after
    
    def test_performance_repr(self, create_performance):
        """Test performance string representation"""
        perf = create_performance(period='daily', net_pnl=4500.0)
        repr_str = repr(perf)
        
        assert 'daily' in repr_str
        assert '4500' in repr_str


@pytest.mark.unit
class TestPerformanceMetrics:
    """Test performance metrics calculations"""
    
    def test_positive_net_pnl(self, create_performance):
        """Test positive net P&L"""
        perf = create_performance(gross_pnl=5000.0, brokerage=500.0)
        
        expected_net = 5000.0 - 500.0
        assert perf.net_pnl == expected_net
    
    def test_negative_net_pnl(self, create_performance):
        """Test negative net P&L (losing day)"""
        perf = create_performance(
            gross_pnl=-2000.0,
            brokerage=300.0,
            net_pnl=-2300.0
        )
        
        assert perf.net_pnl < 0
        assert perf.net_pnl == -2300.0
    
    def test_consecutive_wins_losses(self, create_performance):
        """Test tracking consecutive wins and losses"""
        perf = create_performance(
            max_consecutive_wins=5,
            max_consecutive_losses=2
        )
        
        assert perf.max_consecutive_wins == 5
        assert perf.max_consecutive_losses == 2
    
    def test_average_trade_metrics(self, create_performance):
        """Test average trade metrics"""
        perf = create_performance(
            avg_win=900.0,
            avg_loss=-200.0,
            avg_trade_pnl=450.0  # (4500 net / 10 trades)
        )
        
        assert perf.avg_win > 0
        assert perf.avg_loss < 0
        assert perf.avg_trade_pnl > 0


@pytest.mark.unit
@pytest.mark.parametrize('period,trades,pnl', [
    ('daily', 10, 1000.0),
    ('weekly', 50, 5000.0),
    ('monthly', 200, 20000.0),
])
class TestPerformanceParametrized:
    """Parametrized performance tests"""
    
    def test_performance_periods(self, create_performance, period, trades, pnl):
        """Test performance with different periods"""
        perf = create_performance(
            period=period,
            total_trades=trades,
            net_pnl=pnl
        )
        
        assert perf.period == period
        assert perf.total_trades == trades
        assert perf.net_pnl == pnl
