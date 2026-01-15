"""
MarketData model for storing OHLC and Greeks data.

This model stores:
- OHLC (Open, High, Low, Close) data
- Greeks snapshots
- Implied volatility
- Open interest and volume
- Market snapshots at specific times
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.schema import Index
import enum

from src.database.base import Base, TimestampMixin, PrimaryKeyMixin


class DataInterval(str, enum.Enum):
    """Market data interval enumeration."""
    TICK = "tick"  # Real-time ticks
    MINUTE_1 = "1min"
    MINUTE_5 = "5min"
    MINUTE_15 = "15min"
    HOUR_1 = "1hour"
    DAY = "day"


class MarketData(Base, PrimaryKeyMixin, TimestampMixin):
    """
    MarketData model for storing market snapshots and historical data.
    
    Attributes:
        id: Primary key
        
        # Instrument Details
        symbol: Underlying symbol (e.g., NIFTY, BANKNIFTY)
        exchange: Exchange name
        option_type: Call or Put (if option), NULL for underlying
        strike_price: Option strike price (if option)
        expiry_date: Option expiry date (if option)
        
        # Time Details
        timestamp: Data snapshot timestamp
        interval: Data interval (tick/1min/5min/etc.)
        
        # OHLC Data
        open_price: Open price
        high_price: High price
        low_price: Low price
        close_price: Close price
        volume: Trading volume
        open_interest: Open interest (for options)
        
        # Bid/Ask
        bid_price: Best bid price
        bid_qty: Best bid quantity
        ask_price: Best ask price
        ask_qty: Best ask quantity
        
        # Greeks (for options)
        delta: Option delta
        gamma: Option gamma
        theta: Option theta
        vega: Option vega
        implied_volatility: Implied volatility
        
        # Underlying Data (if this is an option)
        underlying_price: Underlying asset price
        
        # Market Metrics
        ltp: Last traded price
        ltq: Last traded quantity
        total_buy_qty: Total buy quantity
        total_sell_qty: Total sell quantity
        
        # Timestamps
        created_at: Record creation time
        updated_at: Record update time
    """
    
    __tablename__ = "market_data"
    
    # Instrument Details
    symbol = Column(String(50), nullable=False, index=True)
    exchange = Column(String(20), nullable=False)
    option_type = Column(String(10), nullable=True)  # 'call', 'put', or NULL
    strike_price = Column(Float, nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Time Details
    timestamp = Column(DateTime, nullable=False, index=True)
    interval = Column(SQLEnum(DataInterval), default=DataInterval.TICK, index=True)
    
    # OHLC Data
    open_price = Column(Float, nullable=True)
    high_price = Column(Float, nullable=True)
    low_price = Column(Float, nullable=True)
    close_price = Column(Float, nullable=False)
    volume = Column(Integer, default=0)
    open_interest = Column(Integer, nullable=True)
    
    # Bid/Ask
    bid_price = Column(Float, nullable=True)
    bid_qty = Column(Integer, nullable=True)
    ask_price = Column(Float, nullable=True)
    ask_qty = Column(Integer, nullable=True)
    
    # Greeks (for options)
    delta = Column(Float, nullable=True)
    gamma = Column(Float, nullable=True)
    theta = Column(Float, nullable=True)
    vega = Column(Float, nullable=True)
    implied_volatility = Column(Float, nullable=True)
    
    # Underlying Data
    underlying_price = Column(Float, nullable=True)
    
    # Market Metrics
    ltp = Column(Float, nullable=True)  # Last traded price
    ltq = Column(Integer, nullable=True)  # Last traded quantity
    total_buy_qty = Column(Integer, nullable=True)
    total_sell_qty = Column(Integer, nullable=True)
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_market_symbol_time', 'symbol', 'timestamp'),
        Index('idx_market_symbol_interval', 'symbol', 'interval', 'timestamp'),
        Index('idx_market_strike_expiry', 'symbol', 'strike_price', 'expiry_date', 'timestamp'),
    )
    
    def __repr__(self):
        return (
            f"<MarketData(id={self.id}, symbol={self.symbol}, "
            f"strike={self.strike_price}, time={self.timestamp}, "
            f"close={self.close_price})>"
        )
    
    def to_dict(self):
        """Convert market data to dictionary."""
        return {
            "id": self.id,
            "instrument": {
                "symbol": self.symbol,
                "exchange": self.exchange,
                "option_type": self.option_type,
                "strike_price": self.strike_price,
                "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            },
            "time": {
                "timestamp": self.timestamp.isoformat() if self.timestamp else None,
                "interval": self.interval.value if self.interval else None,
            },
            "ohlc": {
                "open": self.open_price,
                "high": self.high_price,
                "low": self.low_price,
                "close": self.close_price,
                "volume": self.volume,
                "open_interest": self.open_interest,
            },
            "bid_ask": {
                "bid_price": self.bid_price,
                "bid_qty": self.bid_qty,
                "ask_price": self.ask_price,
                "ask_qty": self.ask_qty,
            },
            "greeks": {
                "delta": self.delta,
                "gamma": self.gamma,
                "theta": self.theta,
                "vega": self.vega,
                "iv": self.implied_volatility,
            },
            "underlying_price": self.underlying_price,
            "market": {
                "ltp": self.ltp,
                "ltq": self.ltq,
                "total_buy_qty": self.total_buy_qty,
                "total_sell_qty": self.total_sell_qty,
            },
            "timestamps": {
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            }
        }
