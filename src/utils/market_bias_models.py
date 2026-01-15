"""
PHASE 5 — MARKET BIAS + TRADE ELIGIBILITY ENGINE
Data Models & Enums

Defines all data structures for bias detection, eligibility gating, and execution signals.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, List
from datetime import datetime, time


# ============================================================================
# ENUMS - STATE DEFINITIONS
# ============================================================================


class BiasType(Enum):
    """Market bias states"""

    BULLISH = "BULLISH"  # Confident upside bias
    BEARISH = "BEARISH"  # Confident downside bias
    NEUTRAL = "NEUTRAL"  # No clear bias (NO-TRADE mode)
    UNKNOWN = "UNKNOWN"  # Insufficient data


class BiasStrength(Enum):
    """Bias conviction levels"""

    LOW = "LOW"  # <0.5 conviction - NO TRADE
    MEDIUM = "MEDIUM"  # 0.5-0.75 conviction - OK to trade
    HIGH = "HIGH"  # >0.75 conviction - Strong signal
    EXTREME = "EXTREME"  # >0.9 conviction - Maximum conviction

    def __lt__(self, other):
        if isinstance(other, BiasStrength):
            order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
            return order.index(self) < order.index(other)
        return NotImplemented

    def __le__(self, other):
        if isinstance(other, BiasStrength):
            order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
            return order.index(self) <= order.index(other)
        return NotImplemented

    def __gt__(self, other):
        if isinstance(other, BiasStrength):
            order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
            return order.index(self) > order.index(other)
        return NotImplemented

    def __ge__(self, other):
        if isinstance(other, BiasStrength):
            order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
            return order.index(self) >= order.index(other)
        return NotImplemented


class TimeWindow(Enum):
    """Intraday trading windows"""

    ALLOWED = "ALLOWED"  # 9:20-11:15 (Full trading)
    CAUTION = "CAUTION"  # 11:15-12:00 (High filter)
    THETA_DANGER = "THETA_DANGER"  # Post 12:00 (Blocked)
    PRE_MARKET = "PRE_MARKET"  # Before 9:20
    AFTER_HOURS = "AFTER_HOURS"  # After market close


class DataHealthStatus(Enum):
    """Health of input data"""

    GREEN = "GREEN"  # All data valid & fresh
    YELLOW = "YELLOW"  # Some data stale but usable
    RED = "RED"  # Data missing or corrupt - NO TRADE


class DirectionType(Enum):
    """Trade direction"""

    CALL = "CALL"  # Buy Call (Bullish)
    PUT = "PUT"  # Buy Put (Bearish)
    NEUTRAL = "NEUTRAL"  # No trade


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class Phase5Config:
    """Phase 5 configurable thresholds"""

    # Bias Strength Thresholds
    bias_low_threshold: float = 0.5  # <0.5 = LOW
    bias_medium_threshold: float = 0.75  # 0.5-0.75 = MEDIUM
    bias_high_threshold: float = 0.9  # 0.75-0.9 = HIGH
    # >0.9 = EXTREME

    # Minimum requirements for trade eligibility
    min_bias_strength: BiasStrength = BiasStrength.MEDIUM
    max_trap_probability: float = 0.3  # >30% trap = NO TRADE
    max_theta_threshold: float = -0.8  # More negative = too risky
    max_gamma_exhaustion: float = 0.005  # <0.005 gamma = exhausted

    # Time windows
    morning_start: time = time(9, 20)
    morning_end: time = time(11, 15)
    caution_start: time = time(11, 15)
    caution_end: time = time(12, 0)
    theta_danger_start: time = time(12, 0)

    # Data freshness
    max_data_age_seconds: int = 5  # Data older than 5s is stale

    # Strike selection
    preferred_atm_range: float = 1.0  # Prefer strikes within ±1 of ATM
    max_atm_offset: int = 1  # Max ATM±1 strikes

    # Conviction requirements
    oi_conviction_weight: float = 0.3
    volume_aggression_weight: float = 0.25
    delta_gamma_weight: float = 0.25
    trap_probability_weight: float = 0.2


# ============================================================================
# BIAS & STRENGTH MODELS
# ============================================================================


@dataclass
class BiasAnalysis:
    """Result of market bias detection"""

    bias_type: BiasType
    bias_strength: BiasStrength
    conviction_score: float  # [0-1] raw conviction value

    # Component scores contributing to bias
    ce_dominance: float  # [0-1] (0=PE, 1=CE)
    delta_alignment: float  # [0-1] alignment with bias
    gamma_support: float  # [0-1] gamma support for bias
    oi_conviction: float  # [0-1] from Phase 4
    volume_aggression: float  # [0-1] from Phase 4

    # Reasoning
    reasoning: str  # Why this bias?
    confidence_level: str  # "Low", "Medium", "High", "Extreme"

    # Timestamp
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class StrengthAnalysisDetails:
    """Details of bias strength calculation"""

    oi_score: float  # OI conviction component
    volume_score: float  # Volume aggression component
    delta_gamma_score: float  # Delta/Gamma acceleration component
    trap_reduction: float  # Trap probability reduction

    weights_applied: Dict[str, float] = field(default_factory=dict)
    final_score: float = 0.0


# ============================================================================
# TIME & THETA GATE MODELS
# ============================================================================


@dataclass
class TimeGateAnalysis:
    """Result of time window analysis"""

    current_time: time
    time_window: TimeWindow
    allowed: bool

    # Filtering rules
    is_morning_window: bool  # 9:20-11:15
    is_caution_window: bool  # 11:15-12:00
    is_theta_danger: bool  # Post 12:00

    reasoning: str
    recommendation: str  # "PROCEED", "HIGH_FILTER", "BLOCK"


@dataclass
class ThetaVelocityAlert:
    """Theta and Greeks velocity analysis"""

    theta_current: float
    theta_previous: float
    theta_spike_detected: bool  # Theta worsening rapidly

    gamma_current: float
    gamma_exhausted: bool  # Gamma <threshold

    iv_crush_detected: bool  # IV declining rapidly
    iv_current: float
    iv_previous: float

    safe_to_trade: bool
    warnings: List[str]

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# ELIGIBILITY GATE MODELS
# ============================================================================


@dataclass
class EligibilityCheckResult:
    """Individual eligibility check"""

    check_name: str  # "Bias Check", "Time Check", etc.
    passed: bool
    score: float  # [0-1] how well it passed
    reason: str  # Why passed/failed


@dataclass
class TradeEligibilityAnalysis:
    """Complete eligibility assessment"""

    # Individual checks (must ALL be true)
    bias_check: EligibilityCheckResult  # Bias ≠ NEUTRAL
    strength_check: EligibilityCheckResult  # Strength ≥ MEDIUM
    time_check: EligibilityCheckResult  # Time window OK
    trap_check: EligibilityCheckResult  # Trap probability LOW
    data_health_check: EligibilityCheckResult  # Data health GREEN

    # Overall eligibility
    trade_eligible: bool  # All checks passed?
    eligibility_score: float  # Overall [0-1]

    # Blocking reason if not eligible
    block_reason: Optional[str]  # Why not eligible?

    # Data quality
    data_health_status: DataHealthStatus
    data_age_seconds: float  # How old is current data?

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# DIRECTION & INSTRUMENT SELECTION
# ============================================================================


@dataclass
class StrikeSelectionReason:
    """Why a particular strike was selected"""

    gamma_rank: int  # Rank by gamma
    fresh_oi_rank: int  # Rank by fresh OI
    volume_rank: int  # Rank by volume

    gamma_value: float
    fresh_oi_strength: float
    volume_value: float

    weighted_score: float  # Combined score
    selection_reason: str


@dataclass
class DirectionAndStrikeSelection:
    """Selected direction and strike for trade"""

    direction: DirectionType  # CALL / PUT / NEUTRAL
    strike_offset: int  # 0 for ATM, +1 for ATM+1, -1 for ATM-1

    # Instrument detail
    instrument_name: Optional[str]  # e.g., "NIFTY2601220000CE"

    # Why this choice
    reason: StrikeSelectionReason

    # Risk/reward
    entry_confidence: float  # [0-1]

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# EXECUTION SIGNAL (CLEAN OUTPUT)
# ============================================================================


@dataclass
class ExecutionSignal:
    """
    Final output → goes to execution engine
    Dumb execution layer receives this and acts immediately
    """

    # TRADE DECISION
    trade_allowed: bool  # true = place order, false = skip

    # DIRECTION & INSTRUMENT
    direction: DirectionType  # CALL / PUT / NEUTRAL
    strike_offset: int  # 0, +1, -1

    # CONFIDENCE
    confidence_level: float  # [0-1]
    conviction_category: str  # "Low", "Medium", "High", "Extreme"

    # CONTEXT
    market_bias: BiasType
    bias_strength: BiasStrength
    time_window: TimeWindow

    # METADATA
    signal_id: str  # Unique ID for tracking
    timestamp: datetime
    reasoning_brief: str  # 1-line reason

    # ADDITIONAL INFO FOR STRATEGY
    fresh_position_active: bool
    oi_conviction_score: float
    volume_aggression_score: float
    trap_probability: float

    # BLOCKING REASON (if trade_allowed=false)
    block_reason: Optional[str] = None


# ============================================================================
# DIAGNOSTICS & HEALTH REPORTING
# ============================================================================


@dataclass
class Phase5Metrics:
    """Diagnostic metrics for Phase 5"""

    bias_distribution: Dict[str, int] = field(default_factory=dict)  # Count by bias type
    strength_distribution: Dict[str, int] = field(default_factory=dict)  # Count by strength
    eligibility_pass_rate: float = 0.0  # % of updates that pass eligibility

    blocked_due_to_bias: int = 0
    blocked_due_to_strength: int = 0
    blocked_due_to_time: int = 0
    blocked_due_to_trap: int = 0
    blocked_due_to_data_health: int = 0

    trades_allowed: int = 0
    trades_blocked: int = 0

    last_bias: Optional[BiasType] = None
    last_strength: Optional[BiasStrength] = None


@dataclass
class Phase5HealthReport:
    """Overall engine health status"""

    health_status: str  # "HEALTHY", "DEGRADED", "UNHEALTHY"

    # Component status
    bias_engine_ok: bool
    time_gate_ok: bool
    theta_guard_ok: bool
    eligibility_gate_ok: bool
    data_flow_ok: bool

    # Issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Last signal
    last_signal_time: Optional[datetime] = None
    signals_processed: int = 0

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_bias_type(bias: BiasType) -> bool:
    """Validate bias type"""
    return bias in [BiasType.BULLISH, BiasType.BEARISH, BiasType.NEUTRAL, BiasType.UNKNOWN]


def validate_bias_strength(strength: BiasStrength) -> bool:
    """Validate bias strength"""
    return strength in [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]


def is_eligible_bias(bias: BiasType) -> bool:
    """Check if bias allows trading"""
    return bias in [BiasType.BULLISH, BiasType.BEARISH]


def is_strong_bias(strength: BiasStrength, min_strength: BiasStrength = BiasStrength.MEDIUM) -> bool:
    """Check if bias is strong enough to trade"""
    strength_order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
    min_order = [BiasStrength.LOW, BiasStrength.MEDIUM, BiasStrength.HIGH, BiasStrength.EXTREME]
    return strength_order.index(strength) >= min_order.index(min_strength)


def is_trade_window(time_window: TimeWindow) -> bool:
    """Check if trading is allowed in this time window"""
    return time_window in [TimeWindow.ALLOWED, TimeWindow.CAUTION]


def get_direction_from_bias(bias: BiasType) -> DirectionType:
    """Convert bias to direction"""
    if bias == BiasType.BULLISH:
        return DirectionType.CALL
    elif bias == BiasType.BEARISH:
        return DirectionType.PUT
    else:
        return DirectionType.NEUTRAL
