"""
Performance model for tracking trading performance metrics.

This model stores:
- Daily/weekly/monthly performance statistics  
- Win/loss ratios
- Maximum drawdown
- Sharpe ratio and other performance metrics
- Capital utilization
"""

from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, Enum as SQLEnum
from sqlalchemy.schema import Index
import enum

from src.database.base import Base, TimestampMixin, PrimaryKeyMixin


class PerformancePeriod(str, enum.Enum):
    """Performance period enumeration."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Performance(Base, PrimaryKeyMixin, TimestampMixin):
    """Performance model for storing performance metrics."""
    
    __tablename__ = "performance"
    
    # Period Identification
    period = Column(SQLEnum(PerformancePeriod), nullable=False, index=True)
    period_date = Column(Date, nullable=False, index=True)
    
    # Trade Statistics
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    breakeven_trades = Column(Integer, default=0)
    
    # P&L Statistics
    gross_pnl = Column(Float, default=0.0)
    brokerage_total = Column(Float, default=0.0)
    taxes_total = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    
    # Win/Loss Metrics
    win_rate = Column(Float, default=0.0)
    avg_win = Column(Float, default=0.0)
    avg_loss = Column(Float, default=0.0)
    largest_win = Column(Float, default=0.0)
    largest_loss = Column(Float, default=0.0)
    
    # Risk Metrics
    max_drawdown = Column(Float, default=0.0)
    max_drawdown_percentage = Column(Float, default=0.0)
    profit_factor = Column(Float, default=0.0)
    sharpe_ratio = Column(Float, nullable=True)
    sortino_ratio = Column(Float, nullable=True)
    
    # Capital Metrics
    starting_capital = Column(Float, default=0.0)
    ending_capital = Column(Float, default=0.0)
    peak_capital = Column(Float, default=0.0)
    capital_utilization = Column(Float, default=0.0)
    
    # Trade Duration
    avg_trade_duration_minutes = Column(Float, default=0.0)
    shortest_trade_minutes = Column(Float, nullable=True)
    longest_trade_minutes = Column(Float, nullable=True)
    
    # Greeks Exposure
    max_delta_exposure = Column(Float, nullable=True)
    max_gamma_exposure = Column(Float, nullable=True)
    avg_theta_decay = Column(Float, nullable=True)
    
    # Strategy Performance
    strategy_breakdown = Column(String(2000), nullable=True)
    
    # Metadata
    notes = Column(String(1000), nullable=True)
    is_paper_trading = Column(Boolean, default=False, index=True)
    
    # Unique constraint on period + date
    __table_args__ = (
        Index('idx_performance_period_date', 'period', 'period_date', unique=True),
    )
    
    def __repr__(self):
        return (
            f"<Performance(id={self.id}, period={self.period}, "
            f"date={self.period_date}, trades={self.total_trades}, "
            f"pnl={self.net_pnl})>"
        )
