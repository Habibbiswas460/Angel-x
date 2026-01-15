"""
PHASE 3 — Greeks Data Models & Structures
Institution-grade Greek values with change tracking for scalping

Components:
    • GreeksSnapshot - Single strike Greeks (Δ, Γ, Θ, ν)
    • GreeksDelta - Change from previous Greeks
    • AtmIntelligence - Strike zone analysis (Gamma peak, Theta kill)
    • GreeksHealthStatus - Data quality enum
    • VolatilityState - IV trend tracking
    • StrategySignal - Clean output for strategy layer (NO Greek complexity)
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, List, Tuple
import math


class OptionType(Enum):
    """Option leg type"""

    CALL = "CE"
    PUT = "PE"


class VolatilityState(Enum):
    """Implied Volatility trend state"""

    CRUSHING = "CRUSHING"  # IV falling hard
    STABLE_LOW = "STABLE_LOW"  # Low, not changing
    STABLE_MID = "STABLE_MID"  # Medium, stable
    STABLE_HIGH = "STABLE_HIGH"  # High, stable
    SURGING = "SURGING"  # IV rising fast


class ZoneType(Enum):
    """Strike zone classification"""

    GAMMA_PEAK = "GAMMA_PEAK"  # Acceleration zone
    THETA_KILL = "THETA_KILL"  # Decay trap zone
    DELTA_NEUTRAL = "DELTA_NEUTRAL"  # Balanced zone
    SAFE_CALL = "SAFE_CALL"  # CE bullish zone
    SAFE_PUT = "SAFE_PUT"  # PE bearish zone


class GreeksHealthStatus(Enum):
    """Greeks data quality status"""

    HEALTHY = "HEALTHY"  # All good
    DEGRADED = "DEGRADED"  # Slight issues (old IV)
    UNHEALTHY = "UNHEALTHY"  # Major issues (frozen)
    STALE = "STALE"  # Too old
    IV_MISSING = "IV_MISSING"  # Cannot calculate


@dataclass
class GreeksSnapshot:
    """
    Single strike Greeks at a point in time

    Greeks interpretation (directional scalping):
        • Delta (Δ) [0-1] - Move 1 rupee up → call ≈ Δ rupee profit
        • Gamma (Γ) [0-0.1] - Delta change per 1 rupee move
        • Theta (Θ) [negative] - Daily decay (|Θ| rupee lost per day)
        • Vega (ν) [+/-] - 1% IV change → ν rupee P&L

    For strategy: Only track CHANGE, not absolute
    """

    strike: float  # Strike price (e.g., 20050.0)
    option_type: OptionType  # CE or PE

    # Greeks (absolute values)
    delta: float  # 0.0 to 1.0
    gamma: float  # 0.0 to ~0.1 (never negative)
    theta: float  # Usually negative (time decay)
    vega: float  # +/- based on option type

    # Greek greeks (velocity)
    delta_previous: Optional[float] = None  # For ΔΔ calculation
    gamma_previous: Optional[float] = None  # For Γ expansion tracking
    theta_previous: Optional[float] = None  # For Θ spike detection
    vega_previous: Optional[float] = None  # For Vega surge tracking

    # Supporting data
    implied_volatility: float = 0.0  # IV % (e.g., 15.5)
    iv_source: str = "broker"  # "broker" or "calculated"
    last_price: float = 0.0  # LTP for reference
    timestamp: datetime = field(default_factory=datetime.now)

    # Data quality flags
    is_fresh: bool = True  # Within 60 seconds
    calculation_stable: bool = True  # Greeks stable (not jumping)

    def __post_init__(self):
        """Validate Greeks ranges"""
        # Delta validation depends on option type
        if self.option_type == OptionType.CALL:
            assert 0.0 <= self.delta <= 1.0, f"Call Delta must be 0-1, got {self.delta}"
        else:  # PUT
            assert -1.0 <= self.delta <= 0.0, f"Put Delta must be -1 to 0, got {self.delta}"

        assert self.gamma >= 0.0, f"Gamma must be >= 0, got {self.gamma}"
        # Theta is negative, Vega is +/-
        assert self.vega is not None, "Vega cannot be None"

    # ---- Properties: Change Detection (Most Important) ----

    @property
    def delta_change(self) -> Optional[float]:
        """ΔΔ - Delta change (0 = flat, >0 = bullish acceleration, <0 = bearish)"""
        if self.delta_previous is None:
            return None
        return self.delta - self.delta_previous

    @property
    def gamma_expansion(self) -> Optional[float]:
        """Γ expansion (higher = more acceleration potential)"""
        if self.gamma_previous is None:
            return None
        return self.gamma - self.gamma_previous

    @property
    def theta_spike(self) -> Optional[float]:
        """Θ spike (more negative = faster decay, danger signal)"""
        if self.theta_previous is None:
            return None
        return self.theta - self.theta_previous  # More negative = bigger decay

    @property
    def vega_surge(self) -> Optional[float]:
        """Vega change (IV sensitivity shift)"""
        if self.vega_previous is None:
            return None
        return self.vega - self.vega_previous

    @property
    def theta_urgency(self) -> float:
        """
        Urgency score for Theta decay [0-1]
        Higher = faster decay = more dangerous
        Used for: Exit signals, trade avoidance
        """
        if self.theta == 0:
            return 0.0
        urgency = abs(self.theta)  # More negative = higher urgency
        # Normalize: assume max theta decay ~-2 per day
        return min(urgency / 2.0, 1.0)

    @property
    def acceleration_potential(self) -> float:
        """
        Gamma-based acceleration score [0-1]
        Higher = more acceleration per rupee move (scalp-friendly)
        """
        # Normalize gamma to 0-1 scale (max gamma ~0.1)
        return min(self.gamma / 0.1, 1.0)

    def has_greek_movement(self) -> bool:
        """Check if any Greek changed since last snapshot"""
        if self.delta_previous is None:
            return False

        threshold = 0.001  # 0.1% change threshold
        return (
            abs(self.delta_change or 0) > threshold
            or abs(self.gamma_expansion or 0) > threshold
            or abs(self.theta_spike or 0) > threshold
            or abs(self.vega_surge or 0) > threshold
        )


@dataclass
class GreeksDelta:
    """
    Greek changes from previous snapshot
    Used for: Detecting trade opportunities, fake moves, danger zones
    """

    timestamp: datetime = field(default_factory=datetime.now)

    # Individual changes
    delta_changes: Dict[float, float] = field(default_factory=dict)  # strike -> ΔΔ
    gamma_changes: Dict[float, float] = field(default_factory=dict)  # strike -> Γ change
    theta_changes: Dict[float, float] = field(default_factory=dict)  # strike -> Θ change
    vega_changes: Dict[float, float] = field(default_factory=dict)  # strike -> Vega change

    # Aggregate signals
    overall_delta_momentum: float = 0.0  # Avg of all ΔΔ (-1 to +1)
    gamma_expansion_count: int = 0  # How many strikes showed Γ expansion
    theta_spike_detected: bool = False  # Any Θ spike (danger)?
    vega_surge_detected: bool = False  # IV shifting?

    # Zone changes
    gamma_peak_shift: Optional[float] = None  # New gamma peak strike (or None if moved)
    theta_kill_zone_shift: Optional[float] = None  # New Theta kill zone


@dataclass
class AtmIntelligence:
    """
    Strike zone intelligence around ATM
    Tells strategy: What zones exist, What's dangerous, What's opportunity
    """

    atm_strike: float  # Current ATM reference

    # Zone locations (or None if not found)
    gamma_peak_strike: Optional[float] = None  # Highest Gamma strike
    gamma_peak_value: float = 0.0  # Peak Gamma value

    theta_kill_zone_strike: Optional[float] = None  # Highest |Theta| strike
    theta_kill_value: float = 0.0  # Peak |Theta| value

    delta_neutral_zone: Optional[Tuple[float, float]] = None  # (call_strike, put_strike) closest to Δ=0.5

    # ATM battle (CE vs PE)
    atm_ce_delta: Optional[float] = None  # CE Delta at ATM
    atm_pe_delta: Optional[float] = None  # PE Delta at ATM  (1 - call delta for ATM)
    delta_battle_direction: Optional[str] = None  # "CE_LEADING", "PE_LEADING", "NEUTRAL"

    # Safety signals
    is_gamma_peak_safe: bool = True  # True if Gamma peak is not too aggressive
    is_theta_safe: bool = True  # True if no dangerous Theta zone

    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def is_tradeable(self) -> bool:
        """True if ATM zone looks tradeable (not in Theta kill zone)"""
        return self.is_theta_safe and self.is_gamma_peak_safe


@dataclass
class StrategySignal:
    """
    CLEAN OUTPUT FOR STRATEGY LAYER
    Strategy never sees Greeks — only gets these signals

    Philosophy: Strategy = Dumb + Fast. Intelligence here, Execution there.
    """

    timestamp: datetime = field(default_factory=datetime.now)

    # Core signals (0-1 scale, 0 = bearish, 0.5 = neutral, 1 = bullish)
    direction_bias: float = 0.5  # CE Δ - PE Δ (what's winning?)

    acceleration_score: float = 0.5  # Gamma expansion level

    theta_pressure: float = 0.0  # 0 = safe, 1 = extreme decay (avoid)

    volatility_state: VolatilityState = VolatilityState.STABLE_MID

    # Safety signals
    is_data_healthy: bool = True  # Are Greeks OK?
    is_tradeable: bool = True  # ATM zone safe?
    fake_move_detected: bool = False  # Delta ↑ but OI ↓?

    # Recommendation (strategy doesn't have to follow)
    trade_recommendation: str = "NEUTRAL"  # "BUY_CALL", "BUY_PUT", "AVOID", "NEUTRAL"
    confidence: float = 0.5  # 0-1 confidence in recommendation

    # Debug info (for diagnostics)
    _debug_info: Dict = field(default_factory=dict)

    def __post_init__(self):
        """Validate signal ranges"""
        assert 0.0 <= self.direction_bias <= 1.0
        assert 0.0 <= self.acceleration_score <= 1.0
        assert 0.0 <= self.theta_pressure <= 1.0
        assert 0.0 <= self.confidence <= 1.0


@dataclass
class GreeksHealthReport:
    """
    Greeks engine health & data quality report
    Tells: Are Greeks trustworthy? What's broken?
    """

    status: GreeksHealthStatus = GreeksHealthStatus.HEALTHY

    # Metrics
    snapshot_count: int = 0  # How many strikes have fresh Greeks
    stale_count: int = 0  # How many are old
    iv_available: bool = True  # Can we calculate Greeks?

    # Issues detected
    frozen_greeks: int = 0  # Strikes with no Greek movement
    iv_spike: Optional[float] = None  # IV jumped % (or None if normal)
    calculation_errors: int = 0  # How many failed BS calculations

    # Recommendation
    can_trade: bool = True  # Should strategy trade with this data?
    last_healthy_time: Optional[datetime] = None
    recovery_suggestion: str = ""

    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GreeksOiSyncResult:
    """
    Result of Greeks + OI validation (Sync Guard)
    Detects fake moves and smart money activity
    """

    timestamp: datetime = field(default_factory=datetime.now)

    # Validations
    delta_oi_aligned: bool = True  # Delta ↑ & OI ↑? (or both ↓)
    fake_move_detected: bool = False  # Delta ↑ but OI ↓ (DANGER)
    smart_money_signal: bool = False  # Gamma ↑ + OI ↑ (QUALITY)
    theta_exit_signal: bool = False  # Theta ↑ + close to expiry (EXIT)

    # Details
    delta_direction: Optional[str] = None  # "UP", "DOWN", "FLAT"
    oi_direction: Optional[str] = None  # "UP", "DOWN", "FLAT"
    quality_score: float = 0.5  # 0-1, how aligned are Greeks + OI

    recommendation: str = "NEUTRAL"  # "PROCEED", "CAUTION", "AVOID", "NEUTRAL"


# ============================================================================
# Convenience Type Aliases
# ============================================================================

GreeksSnapshotDict = Dict[float, GreeksSnapshot]  # strike -> Greeks
ZoneAnalysis = Dict[str, Optional[float]]  # zone_type -> strike
