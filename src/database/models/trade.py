"""
Trade model for storing trade records.

This model stores:
- Trade entry and exit details
- Option details (strike, expiry, type)
- Greeks at entry and exit
- P&L calculations
- Trade metadata and tags
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, Enum as SQLEnum
from sqlalchemy.schema import Index
import enum

from src.database.base import Base, TimestampMixin, PrimaryKeyMixin


class TradeStatus(str, enum.Enum):
    """Trade status enumeration."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"
    ERROR = "error"


class TradeDirection(str, enum.Enum):
    """Trade direction enumeration."""
    BUY = "buy"
    SELL = "sell"


class OptionType(str, enum.Enum):
    """Option type enumeration."""
    CALL = "call"
    PUT = "put"


class Trade(Base, PrimaryKeyMixin, TimestampMixin):
    """
    Trade model for storing individual trade records.
    
    Attributes:
        id: Primary key
        trade_id: Unique trade identifier
        status: Trade status (open/closed/cancelled/error)
        
        # Instrument Details
        symbol: Underlying symbol (e.g., NIFTY, BANKNIFTY)
        exchange: Exchange name (NSE, NFO, etc.)
        option_type: Call or Put
        strike_price: Option strike price
        expiry_date: Option expiry date
        lot_size: Lot size for the instrument
        
        # Entry Details
        entry_time: Trade entry timestamp
        entry_direction: Buy or Sell
        entry_price: Entry price per lot
        entry_quantity: Number of lots
        entry_order_id: Broker order ID for entry
        
        # Entry Greeks
        entry_delta: Delta at entry
        entry_gamma: Gamma at entry
        entry_theta: Theta at entry
        entry_vega: Vega at entry
        entry_iv: Implied volatility at entry
        
        # Exit Details
        exit_time: Trade exit timestamp
        exit_price: Exit price per lot
        exit_quantity: Number of lots exited
        exit_order_id: Broker order ID for exit
        exit_reason: Reason for exit (profit target, stop loss, etc.)
        
        # Exit Greeks
        exit_delta: Delta at exit
        exit_gamma: Gamma at exit
        exit_theta: Theta at exit
        exit_vega: Vega at exit
        exit_iv: Implied volatility at exit
        
        # P&L
        gross_pnl: Gross profit/loss
        brokerage: Brokerage charges
        taxes: Taxes and charges
        net_pnl: Net profit/loss
        pnl_percentage: P&L as percentage
        
        # Risk Metrics
        max_loss: Maximum loss during trade
        max_profit: Maximum profit during trade
        stop_loss: Stop loss level
        target: Target profit level
        
        # Market Data
        underlying_price_entry: Underlying price at entry
        underlying_price_exit: Underlying price at exit
        
        # Metadata
        strategy_name: Strategy that generated the trade
        tags: Comma-separated tags
        notes: Additional notes
        is_paper_trade: Paper trading flag
        
        # Timestamps
        created_at: Record creation time
        updated_at: Record update time
    """
    
    __tablename__ = "trades"
    
    # Trade Identification
    trade_id = Column(String(100), unique=True, index=True, nullable=False)
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.OPEN, nullable=False, index=True)
    
    # Instrument Details
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    option_type = Column(SQLEnum(OptionType), nullable=False)
    strike_price = Column(Float, nullable=False)
    expiry_date = Column(DateTime, nullable=False, index=True)
    lot_size = Column(Integer, nullable=False)
    
    # Entry Details
    entry_time = Column(DateTime, nullable=False, index=True)
    entry_direction = Column(SQLEnum(TradeDirection), nullable=False)
    entry_price = Column(Float, nullable=False)
    entry_quantity = Column(Integer, nullable=False)
    entry_order_id = Column(String(100), nullable=True)
    
    # Entry Greeks
    entry_delta = Column(Float, nullable=True)
    entry_gamma = Column(Float, nullable=True)
    entry_theta = Column(Float, nullable=True)
    entry_vega = Column(Float, nullable=True)
    entry_iv = Column(Float, nullable=True)
    
    # Exit Details
    exit_time = Column(DateTime, nullable=True, index=True)
    exit_price = Column(Float, nullable=True)
    exit_quantity = Column(Integer, nullable=True)
    exit_order_id = Column(String(100), nullable=True)
    exit_reason = Column(String(200), nullable=True)
    
    # Exit Greeks
    exit_delta = Column(Float, nullable=True)
    exit_gamma = Column(Float, nullable=True)
    exit_theta = Column(Float, nullable=True)
    exit_vega = Column(Float, nullable=True)
    exit_iv = Column(Float, nullable=True)
    
    # P&L
    gross_pnl = Column(Float, default=0.0)
    brokerage = Column(Float, default=0.0)
    taxes = Column(Float, default=0.0)
    net_pnl = Column(Float, default=0.0)
    pnl_percentage = Column(Float, default=0.0)
    
    # Risk Metrics
    max_loss = Column(Float, nullable=True)
    max_profit = Column(Float, nullable=True)
    stop_loss = Column(Float, nullable=True)
    target = Column(Float, nullable=True)
    
    # Market Data
    underlying_price_entry = Column(Float, nullable=True)
    underlying_price_exit = Column(Float, nullable=True)
    
    # Metadata
    strategy_name = Column(String(100), nullable=True, index=True)
    tags = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)
    is_paper_trade = Column(Boolean, default=False, index=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_trade_symbol_date', 'symbol', 'entry_time'),
        Index('idx_trade_status_date', 'status', 'entry_time'),
        Index('idx_trade_strategy', 'strategy_name', 'entry_time'),
    )
    
    def __repr__(self):
        return (
            f"<Trade(id={self.id}, trade_id={self.trade_id}, "
            f"symbol={self.symbol}, strike={self.strike_price}, "
            f"status={self.status}, pnl={self.net_pnl})>"
        )
    
    def to_dict(self):
        """Convert trade to dictionary."""
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "status": self.status.value if self.status else None,
            "symbol": self.symbol,
            "exchange": self.exchange,
            "option_type": self.option_type.value if self.option_type else None,
            "strike_price": self.strike_price,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "lot_size": self.lot_size,
            "entry_time": self.entry_time.isoformat() if self.entry_time else None,
            "entry_direction": self.entry_direction.value if self.entry_direction else None,
            "entry_price": self.entry_price,
            "entry_quantity": self.entry_quantity,
            "entry_greeks": {
                "delta": self.entry_delta,
                "gamma": self.entry_gamma,
                "theta": self.entry_theta,
                "vega": self.entry_vega,
                "iv": self.entry_iv,
            },
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_price": self.exit_price,
            "exit_quantity": self.exit_quantity,
            "exit_reason": self.exit_reason,
            "exit_greeks": {
                "delta": self.exit_delta,
                "gamma": self.exit_gamma,
                "theta": self.exit_theta,
                "vega": self.exit_vega,
                "iv": self.exit_iv,
            },
            "pnl": {
                "gross": self.gross_pnl,
                "brokerage": self.brokerage,
                "taxes": self.taxes,
                "net": self.net_pnl,
                "percentage": self.pnl_percentage,
            },
            "risk": {
                "max_loss": self.max_loss,
                "max_profit": self.max_profit,
                "stop_loss": self.stop_loss,
                "target": self.target,
            },
            "underlying_price": {
                "entry": self.underlying_price_entry,
                "exit": self.underlying_price_exit,
            },
            "metadata": {
                "strategy_name": self.strategy_name,
                "tags": self.tags.split(",") if self.tags else [],
                "notes": self.notes,
                "is_paper_trade": self.is_paper_trade,
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            }
        }
