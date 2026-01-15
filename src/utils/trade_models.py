"""
PHASE 6 — ORDER EXECUTION + RISK MANAGEMENT ENGINE
Data Models & Configuration

Defines order structures, trade tracking, and risk control parameters.
Philosophy: "Trade is optional, Risk control is mandatory"
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict
from datetime import datetime, time
from decimal import Decimal


# ============================================================================
# ENUMS - STATE DEFINITIONS
# ============================================================================


class OrderStatus(Enum):
    """Order lifecycle states"""

    PENDING = "PENDING"  # Waiting for placement
    PLACED = "PLACED"  # Order sent to broker
    EXECUTED = "EXECUTED"  # Order filled
    REJECTED = "REJECTED"  # Broker rejected
    CANCELLED = "CANCELLED"  # Manual/auto cancelled
    FAILED = "FAILED"  # Technical failure


class OrderType(Enum):
    """Order types"""

    BUY = "BUY"  # Entry order
    SELL = "SELL"  # Exit order
    SL = "SL"  # Stop-loss order


class PositionStatus(Enum):
    """Position lifecycle states"""

    ENTRY_PENDING = "ENTRY_PENDING"  # Entry order placed
    ENTRY_EXECUTED = "ENTRY_EXECUTED"  # Entered position
    SL_ACTIVE = "SL_ACTIVE"  # Stop-loss armed
    MONITORING = "MONITORING"  # Active trade, monitoring
    EXIT_TRIGGERED = "EXIT_TRIGGERED"  # SL or target hit
    EXITED = "EXITED"  # Position closed
    FAILED = "FAILED"  # Entry failed, no position


class TradeResult(Enum):
    """Trade outcome"""

    PROFIT = "PROFIT"  # Profit
    LOSS = "LOSS"  # Loss
    BREAKEVEN = "BREAKEVEN"  # No gain/loss
    CANCELLED = "CANCELLED"  # Trade cancelled
    FAILED = "FAILED"  # Trade failed


class ExitReason(Enum):
    """Why trade exited"""

    TARGET_HIT = "TARGET_HIT"  # Profit target reached
    SL_HIT = "SL_HIT"  # Stop-loss hit
    FORCED_EXIT = "FORCED_EXIT"  # Emergency/manual exit
    TIME_DECAY = "TIME_DECAY"  # Theta decay exit
    MARKET_CLOSE = "MARKET_CLOSE"  # Market closed
    SYSTEM_ERROR = "SYSTEM_ERROR"  # Technical error
    KILL_SWITCH = "KILL_SWITCH"  # Kill switch activated


class KillSwitchReason(Enum):
    """Why kill switch was activated"""

    MANUAL = "MANUAL"  # User clicked
    BROKER_ERROR = "BROKER_ERROR"  # Connection lost
    DATA_FREEZE = "DATA_FREEZE"  # No data update
    SPREAD_EXPLOSION = "SPREAD_EXPLOSION"  # Bid-ask widened
    CONNECTIVITY_LOSS = "CONNECTIVITY_LOSS"  # Network issue
    SYSTEM_ERROR = "SYSTEM_ERROR"  # Software error
    MARKET_EVENT = "MARKET_EVENT"  # Trading halt
    EMERGENCY = "EMERGENCY"  # Critical


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class Phase6Config:
    """Phase 6 configurable parameters"""

    # Position sizing
    fixed_risk_per_trade: float = 500.0  # Fixed ₹ risk per trade
    max_position_size: int = 100  # Max contracts per trade
    min_position_size: int = 1  # Min contracts per trade

    # Trade frequency control
    max_trades_per_day: int = 3  # Max trades in a day
    cooldown_minutes_after_sl: int = 15  # Cooldown after SL hit
    consecutive_loss_limit: int = 2  # Lock after 2 consecutive losses
    trading_lock_minutes: int = 30  # Trading lock duration

    # Stop-loss parameters
    hard_sl_percent: float = 2.0  # Hard SL: 2% of entry
    max_sl_distance_points: int = 50  # Max SL distance (points)
    min_sl_distance_points: int = 10  # Min SL distance (points)

    # Target & trail parameters
    initial_target_percent: float = 1.0  # Initial target: 1% profit
    trail_activation_percent: float = 0.5  # Trail after 0.5% profit
    trail_distance_points: int = 15  # Trail distance

    # Order placement
    order_timeout_seconds: int = 30  # Order expiry timeout
    sl_order_timeout_seconds: int = 60  # SL order timeout
    position_entry_retry_attempts: int = 2  # Retry attempts for entry

    # Monitoring & exit
    monitor_interval_seconds: int = 5  # Check interval
    force_exit_on_data_freeze: bool = True  # Exit if data stops
    force_exit_on_spread_spike: bool = True  # Exit if bid-ask widens
    max_spread_points: int = 20  # Max acceptable spread

    # Emergency thresholds
    daily_loss_limit: float = 2000.0  # Daily loss hard limit
    consecutive_loss_amount: float = 500.0  # Amount after which lock
    gamma_exhaustion_exit: bool = True  # Exit on gamma exhaustion
    theta_spike_exit: bool = True  # Exit on theta spike

    # Time windows
    min_exit_time: time = time(11, 30)  # Minimum exit time (11:30)
    force_exit_time: time = time(15, 15)  # Force exit (15:15)


# ============================================================================
# ORDER MODELS
# ============================================================================


@dataclass
class BrokerOrder:
    """Single broker order"""

    order_id: str  # Broker order ID
    symbol: str  # NIFTY
    option_type: str  # CE or PE
    strike: float  # Strike price
    quantity: int  # Quantity
    order_type: OrderType  # BUY/SELL/SL
    price: float  # Order price
    order_time: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: int = 0
    filled_price: Optional[float] = None
    error_message: Optional[str] = None

    def __hash__(self):
        return hash(self.order_id)


@dataclass
class LinkedOrders:
    """Buy order + SL order (atomic pair)"""

    entry_order: BrokerOrder  # Buy order
    sl_order: BrokerOrder  # Stop-loss order
    created_time: datetime = field(default_factory=datetime.now)
    entry_filled: bool = False
    sl_armed: bool = False

    def both_placed(self) -> bool:
        """Both orders placed successfully"""
        return self.entry_order.status == OrderStatus.PLACED and self.sl_order.status == OrderStatus.PLACED

    def entry_executed(self) -> bool:
        """Entry order filled"""
        return self.entry_order.status == OrderStatus.EXECUTED


# ============================================================================
# POSITION MODELS
# ============================================================================


@dataclass
class TradeLevel:
    """Price level with structure info"""

    price: float
    level_type: str  # "ENTRY", "SL", "TARGET", "TRAIL"
    reason: str  # Why this level
    delta_at_level: Optional[float] = None
    gamma_at_level: Optional[float] = None
    time_set: datetime = field(default_factory=datetime.now)


@dataclass
class ActiveTrade:
    """Active trade tracking"""

    trade_id: str  # Unique trade ID
    symbol: str  # NIFTY
    option_type: str  # CE or PE
    strike: float  # Strike
    quantity: int  # Quantity

    # Entry info
    entry_price: float  # Average entry price
    entry_time: datetime  # Entry time
    linked_orders: Optional["LinkedOrders"] = None  # Buy + SL orders

    # Levels
    entry_level: Optional[TradeLevel] = None  # Entry level
    sl_level: Optional[TradeLevel] = None  # Stop-loss level
    target_level: Optional[TradeLevel] = None  # Initial target
    trail_sl: Optional[TradeLevel] = None  # Trailing SL (if active)

    # Trade monitoring
    max_profit: float = 0.0  # Max unrealized P&L
    current_ltp: Optional[float] = None  # Last traded price
    status: PositionStatus = PositionStatus.ENTRY_PENDING
    monitoring_since: datetime = field(default_factory=datetime.now)

    # Risk metrics
    risk_amount: float = 0.0  # ₹ at risk (entry - SL)
    reward_amount: float = 0.0  # ₹ potential reward
    risk_reward_ratio: float = 0.0  # RR ratio

    # Greeks at entry
    delta_at_entry: Optional[float] = None
    gamma_at_entry: Optional[float] = None
    theta_at_entry: Optional[float] = None

    # Live Greeks
    delta_current: Optional[float] = None
    gamma_current: Optional[float] = None
    theta_current: Optional[float] = None

    def pnl_unrealized(self) -> float:
        """Unrealized P&L"""
        if self.current_ltp is None:
            return 0.0
        point_diff = self.current_ltp - self.entry_price
        return point_diff * self.quantity * 100  # 1 point = ₹100 per contract

    def delta_flipped(self) -> bool:
        """Check if delta has flipped"""
        if self.delta_at_entry is None or self.delta_current is None:
            return False
        # Bullish (positive delta) -> check if became negative
        if self.delta_at_entry > 0.5:
            return self.delta_current < 0.3
        # Bearish (negative delta) -> check if became positive
        elif self.delta_at_entry < -0.5:
            return self.delta_current > -0.3
        return False


@dataclass
class ClosedTrade:
    """Completed trade record"""

    trade_id: str
    symbol: str
    option_type: str
    strike: float
    quantity: int

    # Entry
    entry_price: float
    entry_time: datetime

    # Exit
    exit_price: float
    exit_time: datetime
    exit_reason: ExitReason

    # Result
    pnl: float  # Profit/Loss in ₹
    pnl_percent: float  # Profit/Loss %
    result: TradeResult  # PROFIT/LOSS/BREAKEVEN

    # Duration
    duration_seconds: int = 0

    # Risk metrics
    risk_amount: float = 0.0
    reward_realized: float = 0.0
    max_unrealized_pnl: float = 0.0

    def duration_string(self) -> str:
        """Human-readable duration"""
        mins = self.duration_seconds // 60
        secs = self.duration_seconds % 60
        return f"{mins}m {secs}s"


# ============================================================================
# RISK MANAGEMENT MODELS
# ============================================================================


@dataclass
class RiskLimitStatus:
    """Daily risk limit tracking"""

    trades_today: int = 0  # Trades executed
    losses_today: int = 0  # Number of losses
    consecutive_losses: int = 0  # Consecutive losses
    daily_pnl: float = 0.0  # Daily P&L
    daily_loss: float = 0.0  # Daily losses

    last_sl_time: Optional[datetime] = None  # Last SL hit time
    cooldown_active: bool = False  # In cooldown period
    trading_locked: bool = False  # Trading locked (cooldown)
    lock_until: Optional[datetime] = None  # Lock expiry time

    def can_trade(self, current_time: datetime) -> tuple[bool, str]:
        """Check if can trade now"""
        if self.trading_locked:
            if current_time > self.lock_until:
                return True, "Trading lock expired"
            else:
                return False, f"Trading locked until {self.lock_until}"

        if self.trades_today >= 3:
            return False, "Max trades (3) reached today"

        if self.consecutive_losses >= 2:
            return False, "Consecutive loss limit reached"

        if self.daily_loss >= 2000.0:
            return False, "Daily loss limit (₹2000) reached"

        return True, "OK to trade"

    def on_sl_hit(self, current_time: datetime):
        """Called when SL hits"""
        self.last_sl_time = current_time
        self.losses_today += 1
        self.consecutive_losses += 1

        # Trigger cooldown
        from datetime import timedelta

        cooldown_end = current_time + timedelta(minutes=15)
        self.lock_until = cooldown_end
        self.trading_locked = True

    def on_profit(self):
        """Called when trade profits"""
        self.consecutive_losses = 0  # Reset consecutive loss counter


# ============================================================================
# ORDER PLACEMENT MODELS
# ============================================================================


@dataclass
class OrderPlacementRequest:
    """Request to place buy + SL order atomically"""

    symbol: str  # NIFTY
    option_type: str  # CE or PE
    strike: float  # Strike price
    quantity: int  # Quantity
    entry_price: float  # Entry price (LTP)
    sl_price: float  # Stop-loss price
    target_price: float  # Target price
    reason: str  # Why this trade


@dataclass
class OrderPlacementResponse:
    """Response from order placement"""

    success: bool  # Placement successful
    linked_orders: Optional[LinkedOrders] = None
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# MONITORING MODELS
# ============================================================================


@dataclass
class TradeMonitorUpdate:
    """Real-time trade monitoring data"""

    current_ltp: float  # Current LTP
    delta_ce: Optional[float] = None  # CE delta
    delta_pe: Optional[float] = None  # PE delta
    gamma_ce: Optional[float] = None  # CE gamma
    gamma_pe: Optional[float] = None  # PE gamma
    theta_ce: Optional[float] = None  # CE theta
    theta_pe: Optional[float] = None  # PE theta
    bid_ask_spread: float = 0.0  # Bid-ask spread (points)
    volume: int = 0  # Current volume
    oi: int = 0  # Current OI
    timestamp: datetime = field(default_factory=datetime.now)

    # Alerts
    delta_flipped: bool = False  # Delta flipped
    gamma_exhausted: bool = False  # Gamma exhaustion
    theta_dangerous: bool = False  # Theta spike
    spread_wide: bool = False  # Spread widened


@dataclass
class Phase6Metrics:
    """Phase 6 diagnostics & metrics"""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0
    total_pnl: float = 0.0

    active_trades: int = 0
    trades_today: int = 0
    daily_pnl: float = 0.0

    last_trade_time: Optional[datetime] = None
    last_trade_result: Optional[str] = None


@dataclass
class Phase6HealthReport:
    """Engine health status"""

    broker_connected: bool = True
    data_feed_active: bool = True
    order_system_ok: bool = True
    risk_limits_ok: bool = True

    active_positions: int = 0
    pending_orders: int = 0

    health_status: str = "GREEN"  # GREEN/YELLOW/RED
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_order_type(order_type: str) -> bool:
    """Validate order type"""
    try:
        OrderType[order_type.upper()]
        return True
    except KeyError:
        return False


def validate_position_status(status: str) -> bool:
    """Validate position status"""
    try:
        PositionStatus[status.upper()]
        return True
    except KeyError:
        return False


def is_trade_exit_trigger(reason: ExitReason) -> bool:
    """Check if reason should exit trade"""
    return reason in [
        ExitReason.TARGET_HIT,
        ExitReason.SL_HIT,
        ExitReason.FORCED_EXIT,
        ExitReason.KILL_SWITCH,
    ]


def calculate_position_risk(entry_price: float, sl_price: float, quantity: int) -> float:
    """Calculate risk in ₹"""
    point_diff = abs(entry_price - sl_price)
    return point_diff * quantity * 100  # 1 point = ₹100 per contract
