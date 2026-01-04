"""
PHASE 7 — EXIT INTELLIGENCE MODELS

Smart exit triggers, trailing logic, profit protection
Institution-grade exit management
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Tuple
from datetime import datetime, timedelta


# ============================================================================
# ENUMS - EXIT STATES
# ============================================================================

class TrailTrigger(Enum):
    """When to activate/update trailing SL"""
    DELTA_STRONG = "DELTA_STRONG"        # Delta strong & continue
    GAMMA_PEAK = "GAMMA_PEAK"            # Gamma at peak
    MOMENTUM_ACCELERATING = "MOMENTUM_ACCELERATING"
    MOMENTUM_DECELERATING = "MOMENTUM_DECELERATING"
    VOLUME_ACCUMULATION = "VOLUME_ACCUMULATION"
    PARTIAL_EXIT_LOCK = "PARTIAL_EXIT_LOCK"


class PartialExitSignal(Enum):
    """When to take partial profits"""
    FIRST_IMPULSE_DONE = "FIRST_IMPULSE_DONE"     # First move complete
    GAMMA_FLATTENING = "GAMMA_FLATTENING"         # Gamma rolling over
    VOLUME_DROP = "VOLUME_DROP"                   # Volume drying
    PROFIT_THRESHOLD = "PROFIT_THRESHOLD"         # Hit profit target
    TIME_THRESHOLD = "TIME_THRESHOLD"             # Duration expired


class OIReversalSignal(Enum):
    """OI-based reversal signals"""
    OI_UNWINDING = "OI_UNWINDING"                 # Position unwinding
    OI_BUILD_OPPOSITE = "OI_BUILD_OPPOSITE"       # Build against us
    CE_PE_FLIP = "CE_PE_FLIP"                     # Dominance flip
    MAX_OI_REACHED = "MAX_OI_REACHED"             # Peak OI passed


class ThetaExitSignal(Enum):
    """Time decay exit signals"""
    THETA_ACCELERATION = "THETA_ACCELERATION"     # Theta spiking
    TIME_WINDOW_EXCEEDED = "TIME_WINDOW_EXCEEDED" # Duration > limit
    IV_CRUSH_DETECTED = "IV_CRUSH_DETECTED"       # IV collapsing
    EXPIRY_APPROACHING = "EXPIRY_APPROACHING"     # Last day of expiry


class ExhaustionSignal(Enum):
    """Market exhaustion signals"""
    GAMMA_SPIKE_COLLAPSE = "GAMMA_SPIKE_COLLAPSE" # Gamma → 0 fast
    VOLUME_CLIMAX = "VOLUME_CLIMAX"              # Volume spike then dry
    DELTA_DIVERGENCE = "DELTA_DIVERGENCE"        # Price vs delta mismatch
    CANDLE_REVERSAL = "CANDLE_REVERSAL"          # Reversal candle


class CooldownReason(Enum):
    """Why to cooldown between trades"""
    PROFITABLE_TRADE = "PROFITABLE_TRADE"        # Just won
    LOSING_TRADE = "LOSING_TRADE"                # Just lost
    HIGH_VOLATILITY = "HIGH_VOLATILITY"          # VIX spike
    SYSTEM_STRESS = "SYSTEM_STRESS"              # Too many exits
    MARKET_CONDITION_CHANGED = "MARKET_CONDITION_CHANGED"


# ============================================================================
# TRAILING SL MODELS
# ============================================================================

@dataclass
class TrailingSLState:
    """Current trailing SL status"""
    is_active: bool = False
    activation_time: Optional[datetime] = None
    activation_price: Optional[float] = None
    
    # Current trail position
    current_trail_sl: Optional[float] = None
    trail_distance_points: float = 15.0
    last_updated: Optional[datetime] = None
    
    # Trail movement tracking
    times_tightened: int = 0
    times_relaxed: int = 0
    max_trail_gained: float = 0.0  # Points gained from activation
    
    # Trail state
    trail_trigger: Optional[TrailTrigger] = None
    reason: str = ""
    
    def trail_activated(self) -> bool:
        return self.is_active and self.current_trail_sl is not None
    
    def trail_profit_locked(self) -> float:
        """Profit locked by trailing SL vs original SL"""
        if self.activation_price is None or self.current_trail_sl is None:
            return 0.0
        return abs(self.activation_price - self.current_trail_sl)


@dataclass
class PartialExitState:
    """Partial exit tracking"""
    is_eligible: bool = False
    first_exit_taken: bool = False
    first_exit_time: Optional[datetime] = None
    first_exit_quantity: int = 0
    first_exit_price: Optional[float] = None
    first_exit_pnl: float = 0.0
    
    # Remaining position
    remaining_quantity: int = 0
    remaining_entry_price: Optional[float] = None
    remaining_pnl: float = 0.0
    
    # Signals
    signal_reason: Optional[PartialExitSignal] = None
    confidence: float = 0.0  # 0-1
    
    def ready_for_partial_exit(self) -> bool:
        return self.is_eligible and not self.first_exit_taken


# ============================================================================
# REVERSAL & EXHAUSTION MODELS
# ============================================================================

@dataclass
class OIReversalDetector:
    """OI reversal detection state"""
    oi_ce: int = 0
    oi_pe: int = 0
    oi_ce_prev: int = 0
    oi_pe_prev: int = 0
    last_update: Optional[datetime] = None
    
    # Tracking
    ce_oi_increasing: bool = False
    pe_oi_increasing: bool = False
    
    # Detection
    reversal_detected: bool = False
    reversal_signal: Optional[OIReversalSignal] = None
    reversal_confidence: float = 0.0
    reversal_reason: str = ""
    
    def oi_unwinding(self) -> bool:
        """Total OI decreasing (unwinding)"""
        total_curr = self.oi_ce + self.oi_pe
        total_prev = self.oi_ce_prev + self.oi_pe_prev
        return total_curr < total_prev and total_prev > 0
    
    def ce_pe_flip(self) -> bool:
        """Dominance switched"""
        was_ce_dominant = self.oi_ce_prev > self.oi_pe_prev
        is_ce_dominant = self.oi_ce > self.oi_pe
        return was_ce_dominant != is_ce_dominant


@dataclass
class ExhaustionDetector:
    """Market exhaustion detection"""
    gamma_current: float = 0.0
    gamma_prev: float = 0.0
    volume_current: int = 0
    volume_prev: int = 0
    delta_current: float = 0.0
    price_current: float = 0.0
    price_prev: float = 0.0
    
    # Detection
    exhaustion_detected: bool = False
    exhaustion_signal: Optional[ExhaustionSignal] = None
    exhaustion_confidence: float = 0.0
    
    def gamma_collapse(self) -> bool:
        """Gamma collapsed"""
        return self.gamma_prev > 0.01 and self.gamma_current < 0.003
    
    def volume_climax(self) -> bool:
        """Volume spike then dry"""
        return self.volume_current > self.volume_prev * 2
    
    def delta_divergence(self) -> bool:
        """Price moved but delta didn't"""
        price_move = abs(self.price_current - self.price_prev)
        delta_move = abs(self.delta_current)
        return price_move > 2.0 and delta_move < 0.2


# ============================================================================
# THETA & TIME DECAY MODELS
# ============================================================================

@dataclass
class ThetaDecayMonitor:
    """Theta decay tracking"""
    theta_current: float = 0.0
    theta_prev: float = 0.0
    theta_avg_per_minute: float = 0.0
    
    entry_time: Optional[datetime] = None
    last_update: Optional[datetime] = None
    
    # Acceleration detection
    theta_accelerating: bool = False
    theta_acceleration_rate: float = 0.0  # Per minute
    
    # Time limit
    max_holding_seconds: int = 600  # 10 mins default
    time_exceeded: bool = False
    
    # IV tracking
    iv_current: float = 0.0
    iv_entry: float = 0.0
    iv_crushing: bool = False
    
    def time_elapsed(self) -> int:
        """Seconds held"""
        if self.entry_time is None:
            return 0
        return int((datetime.now() - self.entry_time).total_seconds())
    
    def time_exceeded_limit(self) -> bool:
        return self.time_elapsed() > self.max_holding_seconds
    
    def theta_danger_zone(self) -> bool:
        """Theta getting dangerous"""
        return self.theta_accelerating and self.theta_acceleration_rate > 0.05


# ============================================================================
# COOLDOWN MODELS
# ============================================================================

@dataclass
class PostTradeCooldown:
    """Cooldown logic after trade exit"""
    last_trade_exit_time: Optional[datetime] = None
    last_trade_result: Optional[str] = None  # PROFIT/LOSS/NEUTRAL
    
    # Cooldown periods
    cooldown_after_win_secs: int = 120        # 2 mins after win
    cooldown_after_loss_secs: int = 300       # 5 mins after loss
    cooldown_after_volatility_secs: int = 600 # 10 mins after spike
    
    # State
    cooling_down: bool = False
    cooldown_reason: Optional[CooldownReason] = None
    cooldown_until: Optional[datetime] = None
    
    def is_in_cooldown(self) -> Tuple[bool, str]:
        """Check if still cooling down"""
        if not self.cooling_down or self.cooldown_until is None:
            return False, "Not cooling"
        
        if datetime.now() > self.cooldown_until:
            self.cooling_down = False
            return False, "Cooldown expired"
        
        secs_left = int((self.cooldown_until - datetime.now()).total_seconds())
        return True, f"Cooling for {secs_left}s"


# ============================================================================
# TRADE JOURNAL MODELS
# ============================================================================

@dataclass
class TradeContextSnapshot:
    """Entry context capture"""
    entry_price: float
    entry_time: datetime
    option_type: str
    strike: float
    
    # Greeks at entry
    delta_entry: float
    gamma_entry: float
    theta_entry: float
    iv_entry: float
    
    # Market context
    oi_ce_entry: int
    oi_pe_entry: int
    volume_entry: int


@dataclass
class ExitContextSnapshot:
    """Exit context capture"""
    exit_price: float
    exit_time: datetime
    exit_reason: str  # Why we exited
    
    # Greeks at exit
    delta_exit: float
    gamma_exit: float
    theta_exit: float
    iv_exit: float
    
    # Market context
    oi_ce_exit: int
    oi_pe_exit: int
    volume_exit: int
    
    # Trade metrics
    pnl: float = 0.0
    pnl_percent: float = 0.0
    duration_seconds: int = 0
    max_profit: float = 0.0
    max_loss: float = 0.0


@dataclass
class TradeJournalEntry:
    """Complete trade journal snapshot"""
    trade_id: str = ""
    entry_context: Optional[TradeContextSnapshot] = None
    exit_context: Optional[ExitContextSnapshot] = None

    # Basic pricing
    entry_price: float = 0.0
    exit_price: float = 0.0
    pnl_rupees: float = 0.0
    pnl_percent: float = 0.0
    duration_seconds: int = 0
    
    # Exit details
    was_partial_exit: bool = False
    partial_exit_qty: int = 0
    remaining_qty: int = 0
    
    trailing_sl_used: bool = False
    trail_profit_locked: float = 0.0
    
    # Analysis
    trade_quality: str = ""  # EXCELLENT/GOOD/FAIR/POOR
    learnings: str = ""      # What we learned
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Phase7Metrics:
    """Exit intelligence metrics"""
    total_trades: int = 0
    successful_exits: int = 0
    failed_exits: int = 0
    
    # Exit types
    trailing_sl_exits: int = 0
    partial_exits: int = 0
    oireverse_exits: int = 0
    theta_exits: int = 0
    exhaustion_exits: int = 0
    time_forced_exits: int = 0
    
    # Profit metrics
    profit_locked_trailing: float = 0.0
    profit_locked_partial: float = 0.0
    avg_holding_time_secs: float = 0.0
    
    # Win rate & quality
    win_rate: float = 0.0
    avg_exit_quality: str = ""


@dataclass
class Phase7Config:
    """Phase 7 configuration"""
    
    # Trailing SL
    trail_activation_profit_percent: float = 0.5  # Activate at 0.5% profit
    trail_distance_points: int = 15               # Trail 15 pts from peak
    trail_tighten_on_gamma_peak: bool = True
    
    # Partial exits
    partial_exit_quantity_percent: float = 0.60   # Exit 60% at first
    partial_exit_profit_percent: float = 0.8      # Exit at 0.8% profit
    
    # Time limits
    max_holding_seconds: int = 600                # 10 mins max
    lunch_session_start: str = "11:30"            # Exit before lunch
    
    # OI reversal
    oi_reversal_threshold_percent: float = 5.0    # 5% change
    
    # Exhaustion
    gamma_collapse_threshold: float = 0.003
    volume_spike_multiplier: float = 2.0
    
    # Theta decay
    theta_acceleration_threshold: float = 0.05
    
    # Cooldown
    cooldown_after_win_secs: int = 120
    cooldown_after_loss_secs: int = 300


# ============================================================================
# HELPER TYPES
# ============================================================================

from typing import Tuple

__all__ = [
    'TrailTrigger', 'PartialExitSignal', 'OIReversalSignal',
    'ThetaExitSignal', 'ExhaustionSignal', 'CooldownReason',
    'TrailingSLState', 'PartialExitState', 'OIReversalDetector',
    'ExhaustionDetector', 'ThetaDecayMonitor', 'PostTradeCooldown',
    'TradeContextSnapshot', 'ExitContextSnapshot', 'TradeJournalEntry',
    'Phase7Metrics', 'Phase7Config',
]
