"""
PHASE 4 — OI + VOLUME INTELLIGENCE ENGINE
Data Models for Smart Money Detection

Smart Money Detector মডেলস - Institutional positioning detection
Volume = Interest | OI = Commitment | Greeks = Risk Profile

Three together = TRADEABLE MOVE

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import deque


# ============================================================================
# ENUMS - Institutional State Classification
# ============================================================================


class OiBuildUpType(Enum):
    """
    4 Institutional states for OI build-up
    Only LONG_BUILD_UP & SHORT_BUILD_UP = high conviction scalping
    """

    LONG_BUILD_UP = "long_buildup"  # Price ↑ | OI ↑ | Vol ↑
    SHORT_BUILD_UP = "short_buildup"  # Price ↓ | OI ↑ | Vol ↑
    SHORT_COVERING = "short_covering"  # Price ↑ | OI ↓ | Vol ↑
    LONG_UNWINDING = "long_unwinding"  # Price ↓ | OI ↓ | Vol ↑
    NEUTRAL = "neutral"  # No clear pattern
    INSUFFICIENT_DATA = "insufficient"  # Not enough snapshots


class VolumeState(Enum):
    """Volume spike detection state"""

    NORMAL = "normal"
    SPIKE = "spike"
    BURST = "burst"
    AGGRESSIVE = "aggressive"
    UNUSUAL = "unusual"


class BattlefieldControl(Enum):
    """CE vs PE dominance in ATM zone"""

    BULLISH_CONTROL = "bullish"
    BEARISH_CONTROL = "bearish"
    NEUTRAL_CHOP = "neutral"
    BALANCED = "balanced"


class TrapType(Enum):
    """Trap detection classification"""

    NO_TRAP = "no_trap"
    SCALPER_TRAP = "scalper_trap"  # Low OI + high volume
    NOISE_TRAP = "noise_trap"  # Gamma flat + volume spike
    THETA_CRUSH_TRAP = "theta_crush"  # Theta aggressive + decay
    REVERSAL_TRAP = "reversal_trap"  # Volume fail at resistance


# ============================================================================
# STRIKE-LEVEL DATA STRUCTURES
# ============================================================================


@dataclass
class VolumeSnapshot:
    """Single strike volume data point"""

    strike: float
    option_type: str  # "CE" or "PE"
    volume: int
    timestamp: datetime
    bid_quantity: int = 0
    ask_quantity: int = 0

    def __post_init__(self):
        if self.volume < 0:
            raise ValueError(f"Volume cannot be negative: {self.volume}")
        if self.option_type not in ["CE", "PE"]:
            raise ValueError(f"Invalid option_type: {self.option_type}")


@dataclass
class OiSnapshot:
    """Single strike OI data point"""

    strike: float
    option_type: str  # "CE" or "PE"
    oi: int
    timestamp: datetime

    def __post_init__(self):
        if self.oi < 0:
            raise ValueError(f"OI cannot be negative: {self.oi}")


@dataclass
class StrikeLevelIntelligence:
    """Intelligence for single strike"""

    strike: float
    option_type: str

    # OI build-up state
    buildup_type: OiBuildUpType
    buildup_confidence: float  # 0-1

    # Volume state
    volume_state: VolumeState
    relative_volume: float  # Current vs rolling average

    # Fresh position detection
    is_fresh_position: bool
    fresh_position_confidence: float  # 0-1

    # Price delta
    price_change: float  # As percentage

    # OI change
    oi_change: float  # As percentage

    # Volume change
    volume_change: float  # As percentage

    # Associated Greeks info
    delta: float  # From Phase 3
    gamma: float
    theta: float

    # Trap detection
    trap_type: TrapType
    trap_probability: float  # 0-1

    # Cross-validation result
    greeks_oi_aligned: bool  # True if Greeks signal = OI signal
    alignment_confidence: float  # 0-1


@dataclass
class CePeBattlefield:
    """ATM zone CE vs PE conflict analysis"""

    # OI dominance
    ce_oi_dominance: float  # 0-1 (0=PE dominant, 1=CE dominant)

    # Volume dominance
    ce_volume_dominance: float  # 0-1

    # Delta skew (institutional positioning)
    delta_skew: float  # 0-1 (0=bearish skew, 1=bullish skew)

    # Absolute volumes
    ce_volume: int
    pe_volume: int

    # Absolute OI
    ce_oi: int
    pe_oi: int

    # Battlefield control
    control: BattlefieldControl

    # War intensity (0-1, how contested is the zone)
    war_intensity: float

    # Recent momentum (which side winning recently)
    ce_momentum: float  # 0-1 (positive = CE gaining)

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FreshPositionSignal:
    """Fresh position detection signal"""

    # Position characteristics
    is_fresh: bool
    confidence: float  # 0-1

    # What triggered it
    oi_jump_magnitude: float  # % change
    volume_surge_magnitude: float  # % change

    # Type of fresh position
    entry_type: str  # "long_entry", "short_entry", "adjustment"

    # Strength assessment
    strength: float  # 0-1

    # Expected volatility from position
    expected_volatility: float  # 0-1

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# AGGREGATED CHAIN-LEVEL DATA STRUCTURES
# ============================================================================


@dataclass
class SmartMoneySignal:
    """
    Clean output for strategy layer
    Strategy never sees raw data, only this processed signal
    """

    # Market control indicator
    market_control: BattlefieldControl

    # Conviction scores (0-1)
    oi_conviction_score: float  # How certain is OI showing conviction
    volume_aggression_score: float  # How aggressive is volume
    smart_money_probability: float  # Likelihood of smart money move

    # Risk indicators
    trap_probability: float  # 0-1
    fake_move_probability: float  # 0-1

    # Fresh money
    fresh_position_detected: bool
    fresh_position_strength: float  # 0-1

    # Direction signal
    direction_bias: str  # "BULLISH" | "BEARISH" | "NEUTRAL" | "CHOP"
    direction_confidence: float  # 0-1

    # Trade recommendation
    can_trade: bool
    recommendation: str  # "BUY_CALL" | "BUY_PUT" | "AVOID" | "NEUTRAL"

    # Reason for recommendation
    reason: str  # Explanation string

    # Data freshness
    timestamp: datetime = field(default_factory=datetime.now)
    data_age_seconds: int = 0

    # Metrics
    dominant_strikes: List[float] = field(default_factory=list)  # ATM ±N strikes showing action


@dataclass
class SmartMoneyMetrics:
    """Aggregated metrics for the chain"""

    # Build-up type distribution
    long_buildup_strikes: int
    short_buildup_strikes: int
    short_covering_strikes: int
    long_unwinding_strikes: int

    # Fresh positions detected
    fresh_positions_count: int
    fresh_positions_strength: float  # Average strength

    # Volume metrics
    total_volume_current: int
    total_volume_previous: int
    volume_surge_percentage: float

    # OI metrics
    total_oi_current: int
    total_oi_previous: int
    oi_change_percentage: float

    # Fake moves detected
    trap_count: int
    trap_probability_average: float

    # Greeks alignment
    greeks_oi_aligned_count: int
    alignment_percentage: float

    # CE vs PE
    battlefield_control: BattlefieldControl
    war_intensity: float

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SmartMoneyHealthReport:
    """Data quality report for smart money engine"""

    status: str  # "HEALTHY" | "DEGRADED" | "UNHEALTHY" | "STALE"
    can_analyze: bool

    # Coverage
    strikes_analyzed: int = 0
    strikes_with_volume: int = 0
    strikes_with_oi: int = 0

    # Data age
    max_data_age_seconds: int = 0

    # Validation stats
    validation_passed: int = 0
    validation_failed: int = 0

    # Data issues
    issues: List[str] = field(default_factory=list)

    timestamp: datetime = field(default_factory=datetime.now)


# ============================================================================
# HISTORICAL TRACKING
# ============================================================================


@dataclass
class OiVolumeHistory:
    """
    Track OI + Volume changes for single strike over time
    Used for trend detection, volume spike analysis
    """

    strike: float
    option_type: str

    # Rolling history (configurable size, default 20)
    oi_history: deque = field(default_factory=lambda: deque(maxlen=20))
    volume_history: deque = field(default_factory=lambda: deque(maxlen=20))
    price_history: deque = field(default_factory=lambda: deque(maxlen=20))

    # Statistics
    avg_volume_20: float = 0.0
    avg_oi_20: float = 0.0

    # Change rates
    volume_change_rate: float = 0.0  # Current vs 5-snapshot average
    oi_change_rate: float = 0.0

    # Volatility in measurements
    volume_volatility: float = 0.0  # Std dev of changes
    oi_volatility: float = 0.0

    timestamp: datetime = field(default_factory=datetime.now)

    def add_snapshot(self, oi: int, volume: int, price: float):
        """Add new snapshot and update statistics"""
        self.oi_history.append(oi)
        self.volume_history.append(volume)
        self.price_history.append(price)

        if len(self.oi_history) > 0:
            self.avg_oi_20 = sum(self.oi_history) / len(self.oi_history)
            self.avg_volume_20 = sum(self.volume_history) / len(self.volume_history)

    def get_volume_spike_factor(self) -> float:
        """Current volume / average volume"""
        if self.avg_volume_20 == 0:
            return 1.0
        return self.volume_history[-1] / self.avg_volume_20 if self.volume_history else 1.0

    def get_oi_change_factor(self) -> float:
        """Current OI / previous OI"""
        if len(self.oi_history) < 2:
            return 1.0
        prev_oi = self.oi_history[-2] if len(self.oi_history) >= 2 else self.oi_history[-1]
        if prev_oi == 0:
            return 1.0
        return self.oi_history[-1] / prev_oi


# ============================================================================
# CONFIGURATION
# ============================================================================


@dataclass
class SmartMoneyConfig:
    """Configuration for Smart Money Engine"""

    # Volume spike thresholds
    volume_spike_threshold: float = 1.5  # 1.5x average = spike
    volume_burst_threshold: float = 2.5  # 2.5x average = burst
    volume_aggression_threshold: float = 3.0  # 3x average = aggressive

    # OI build-up classification thresholds
    price_change_threshold: float = 0.02  # 2% price move
    oi_change_threshold: float = 0.05  # 5% OI change
    volume_confirmation_threshold: float = 1.5  # 1.5x avg volume

    # Fresh position detection
    fresh_position_oi_jump: float = 0.10  # 10% OI jump
    fresh_position_volume_surge: float = 2.0  # 2x volume surge
    first_time_oi_threshold: int = 100  # Minimum OI for "first time" detection

    # Trap detection
    trap_low_oi_threshold: int = 50  # Less than 50 OI
    trap_volume_surge_threshold: float = 3.0  # 3x volume surge
    trap_gamma_flat_threshold: float = 0.02  # Low gamma

    # CE vs PE zone size
    ce_pe_atm_range: float = 5.0  # ATM ±5 strikes for battlefield

    # Cross-validation thresholds
    greeks_oi_alignment_threshold: float = 0.7  # 70% agreement

    # Data requirements
    min_strikes_for_analysis: int = 8
    max_data_age_seconds: int = 60

    # History size
    history_size: int = 20

    # Fresh position decay (confidence multiplier per second)
    fresh_position_decay_rate: float = 0.95

    def __post_init__(self):
        """Validate configuration"""
        if self.volume_spike_threshold <= 1.0:
            raise ValueError("volume_spike_threshold must be > 1.0")
        if self.oi_change_threshold < 0 or self.oi_change_threshold > 1.0:
            raise ValueError("oi_change_threshold must be 0-1")


# ============================================================================
# DEBUG / DETAILED STATUS
# ============================================================================


@dataclass
class DetailedSmartMoneyStatus:
    """Full diagnostic status for debugging"""

    # Overall status
    is_ready: bool
    health_status: str

    # Component readiness
    data_freshness_ok: bool
    greeks_data_available: bool
    oi_volume_data_available: bool

    # Detailed metrics
    strikes_analyzed: int
    high_conviction_strikes: int
    fresh_position_count: int

    # Signal quality
    signal_confidence: float
    alignment_score: float  # How well Greeks + OI + Volume align

    # Last signal info
    last_signal_timestamp: datetime = field(default_factory=datetime.now)
    last_signal_direction: str = ""

    # Active issues
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    # Metadata
    config: SmartMoneyConfig = field(default_factory=SmartMoneyConfig)

    def add_warning(self, msg: str):
        """Add warning message"""
        self.warnings.append(f"{datetime.now().isoformat()}: {msg}")

    def add_error(self, msg: str):
        """Add error message"""
        self.errors.append(f"{datetime.now().isoformat()}: {msg}")


# ============================================================================
# VALIDATION FUNCTIONS
# ============================================================================


def validate_buildup_type(
    price_change: float, oi_change: float, volume_change: float, config: SmartMoneyConfig
) -> OiBuildUpType:
    """
    Classify OI build-up type based on price, OI, volume changes

    Price ↑ | OI ↑ | Vol ↑ = Long Build-Up
    Price ↓ | OI ↑ | Vol ↑ = Short Build-Up
    Price ↑ | OI ↓ | Vol ↑ = Short Covering
    Price ↓ | OI ↓ | Vol ↑ = Long Unwinding
    """

    price_threshold = config.price_change_threshold
    oi_threshold = config.oi_change_threshold
    volume_threshold = config.volume_confirmation_threshold

    price_up = price_change > price_threshold
    price_down = price_change < -price_threshold

    oi_up = oi_change > oi_threshold
    oi_down = oi_change < -oi_threshold

    volume_surge = volume_change > volume_threshold

    if not volume_surge:
        return OiBuildUpType.NEUTRAL

    if price_up and oi_up:
        return OiBuildUpType.LONG_BUILD_UP
    elif price_down and oi_up:
        return OiBuildUpType.SHORT_BUILD_UP
    elif price_up and oi_down:
        return OiBuildUpType.SHORT_COVERING
    elif price_down and oi_down:
        return OiBuildUpType.LONG_UNWINDING
    else:
        return OiBuildUpType.NEUTRAL


def is_high_conviction_buildup(buildup_type: OiBuildUpType) -> bool:
    """Only LONG_BUILD_UP and SHORT_BUILD_UP are high conviction"""
    return buildup_type in [OiBuildUpType.LONG_BUILD_UP, OiBuildUpType.SHORT_BUILD_UP]
