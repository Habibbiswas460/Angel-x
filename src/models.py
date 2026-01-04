"""
Angel-X Core Data Models
Centralized type definitions and data structures
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS - Trading Constants
# ============================================================================

class OrderSide(Enum):
    """Order side enumeration"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type enumeration"""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP_LOSS = "SL"
    STOP_LOSS_MARKET = "SL-M"


class OrderStatus(Enum):
    """Order status enumeration"""
    PENDING = "PENDING"
    OPEN = "OPEN"
    COMPLETE = "COMPLETE"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class ProductType(Enum):
    """Product type enumeration"""
    INTRADAY = "INTRADAY"
    DELIVERY = "DELIVERY"
    MIS = "MIS"
    NRML = "NRML"


class OptionType(Enum):
    """Option type enumeration"""
    CALL = "CE"
    PUT = "PE"


class BiasState(Enum):
    """Market bias state"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    NEUTRAL = "NEUTRAL"
    NO_TRADE = "NO_TRADE"


class ExitReason(Enum):
    """Exit reason enumeration"""
    TARGET = "TARGET"
    STOP_LOSS = "STOP_LOSS"
    TIME_EXIT = "TIME_EXIT"
    GAMMA_EXIT = "GAMMA_EXIT"
    THETA_EXIT = "THETA_EXIT"
    REVERSAL_EXIT = "REVERSAL_EXIT"
    MANUAL_EXIT = "MANUAL_EXIT"
    STRATEGY_STOP = "STRATEGY_STOP"


# ============================================================================
# MARKET DATA MODELS
# ============================================================================

@dataclass
class Tick:
    """Market tick data"""
    symbol: str
    exchange: str
    ltp: float
    bid: float
    ask: float
    volume: int
    timestamp: datetime
    high: float = 0.0
    low: float = 0.0
    open: float = 0.0
    close: float = 0.0
    oi: int = 0


@dataclass
class OptionChainData:
    """Option chain data point"""
    strike: int
    option_type: str  # CE or PE
    ltp: float
    bid: float
    ask: float
    volume: int
    oi: int
    iv: float
    delta: float
    gamma: float
    theta: float
    vega: float
    timestamp: datetime


@dataclass
class Greeks:
    """Option Greeks"""
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "delta": self.delta,
            "gamma": self.gamma,
            "theta": self.theta,
            "vega": self.vega,
            "iv": self.iv,
            "timestamp": self.timestamp.isoformat()
        }


# ============================================================================
# ORDER MODELS
# ============================================================================

@dataclass
class Order:
    """Trading order"""
    symbol: str
    exchange: str
    side: OrderSide
    order_type: OrderType
    quantity: int
    price: Optional[float] = None
    trigger_price: Optional[float] = None
    product: ProductType = ProductType.MIS
    order_id: Optional[str] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    average_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    tag: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "side": self.side.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": self.price,
            "trigger_price": self.trigger_price,
            "product": self.product.value,
            "order_id": self.order_id,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "average_price": self.average_price,
            "timestamp": self.timestamp.isoformat(),
            "tag": self.tag
        }


@dataclass
class Position:
    """Trading position"""
    symbol: str
    exchange: str
    quantity: int
    average_price: float
    current_price: float
    pnl: float
    pnl_percent: float
    product: ProductType
    entry_time: datetime
    last_update: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "symbol": self.symbol,
            "exchange": self.exchange,
            "quantity": self.quantity,
            "average_price": self.average_price,
            "current_price": self.current_price,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "product": self.product.value,
            "entry_time": self.entry_time.isoformat(),
            "last_update": self.last_update.isoformat()
        }


# ============================================================================
# TRADE MODELS
# ============================================================================

@dataclass
class Trade:
    """Completed trade record"""
    symbol: str
    option_type: str
    strike: int
    entry_price: float
    exit_price: float
    quantity: int
    entry_time: datetime
    exit_time: datetime
    pnl: float
    pnl_percent: float
    exit_reason: ExitReason
    
    # Greeks at entry
    entry_delta: float = 0.0
    entry_gamma: float = 0.0
    entry_theta: float = 0.0
    entry_vega: float = 0.0
    entry_iv: float = 0.0
    
    # Greeks at exit
    exit_delta: float = 0.0
    exit_gamma: float = 0.0
    exit_theta: float = 0.0
    exit_vega: float = 0.0
    exit_iv: float = 0.0
    
    # Market conditions
    bias_at_entry: str = "NEUTRAL"
    oi_at_entry: int = 0
    oi_at_exit: int = 0
    
    # Metadata
    trade_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    @property
    def holding_duration(self) -> float:
        """Holding duration in minutes"""
        return (self.exit_time - self.entry_time).total_seconds() / 60
    
    @property
    def won(self) -> bool:
        """Whether trade was profitable"""
        return self.pnl > 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "trade_id": self.trade_id,
            "symbol": self.symbol,
            "option_type": self.option_type,
            "strike": self.strike,
            "entry_price": self.entry_price,
            "exit_price": self.exit_price,
            "quantity": self.quantity,
            "entry_time": self.entry_time.isoformat(),
            "exit_time": self.exit_time.isoformat(),
            "holding_duration": self.holding_duration,
            "pnl": self.pnl,
            "pnl_percent": self.pnl_percent,
            "won": self.won,
            "exit_reason": self.exit_reason.value,
            "entry_greeks": {
                "delta": self.entry_delta,
                "gamma": self.entry_gamma,
                "theta": self.entry_theta,
                "vega": self.entry_vega,
                "iv": self.entry_iv
            },
            "exit_greeks": {
                "delta": self.exit_delta,
                "gamma": self.exit_gamma,
                "theta": self.exit_theta,
                "vega": self.exit_vega,
                "iv": self.exit_iv
            },
            "market_conditions": {
                "bias_at_entry": self.bias_at_entry,
                "oi_at_entry": self.oi_at_entry,
                "oi_at_exit": self.oi_at_exit
            },
            "tags": self.tags,
            "notes": self.notes
        }


# ============================================================================
# SIGNAL MODELS
# ============================================================================

@dataclass
class TradingSignal:
    """Trading signal with complete context"""
    signal_type: str  # BUY_CALL, BUY_PUT, etc.
    confidence: float  # 0.0 - 1.0
    strike: int
    option_type: str
    entry_price: float
    reason_tags: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Supporting data
    bias_state: str = "NEUTRAL"
    bias_confidence: float = 0.0
    oi_conviction: str = "WEAK"
    gamma: float = 0.0
    delta: float = 0.0
    theta: float = 0.0
    iv: float = 0.0
    
    # Adaptive context (Phase 10)
    adaptive_confidence: Optional[float] = None
    market_regime: Optional[str] = None
    recommended_size: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "strike": self.strike,
            "option_type": self.option_type,
            "entry_price": self.entry_price,
            "reason_tags": self.reason_tags,
            "timestamp": self.timestamp.isoformat(),
            "bias_state": self.bias_state,
            "bias_confidence": self.bias_confidence,
            "oi_conviction": self.oi_conviction,
            "greeks": {
                "gamma": self.gamma,
                "delta": self.delta,
                "theta": self.theta,
                "iv": self.iv
            },
            "adaptive": {
                "confidence": self.adaptive_confidence,
                "regime": self.market_regime,
                "recommended_size": self.recommended_size
            }
        }


# ============================================================================
# EXPORT ALL MODELS
# ============================================================================

__all__ = [
    # Enums
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "ProductType",
    "OptionType",
    "BiasState",
    "ExitReason",
    
    # Market Data
    "Tick",
    "OptionChainData",
    "Greeks",
    
    # Orders & Positions
    "Order",
    "Position",
    
    # Trades
    "Trade",
    
    # Signals
    "TradingSignal"
]
