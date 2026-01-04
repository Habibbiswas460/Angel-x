"""
Phase 2: Option Chain Data Models & Structures

Clean, typed data structures for option chain information.
No business logic - just data containers.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum


class OptionType(Enum):
    """Option type enumeration"""
    CE = "CE"  # Call option
    PE = "PE"  # Put option


@dataclass
class StrikeData:
    """Single strike price data (CE or PE)"""
    
    strike: float                  # Strike price (e.g., 20000.0)
    option_type: OptionType        # CE or PE
    
    ltp: float                     # Last Traded Price
    bid: Optional[float] = None    # Bid price (if available)
    ask: Optional[float] = None    # Ask price (if available)
    
    volume: int = 0                # Total trading volume
    oi: int = 0                    # Open Interest
    oi_prev: Optional[int] = None  # Previous OI (for delta)
    
    timestamp: Optional[datetime] = None  # Exchange timestamp
    
    # Metadata
    token: Optional[str] = None    # Broker token
    exchange: str = "NFO"          # Exchange
    
    def __post_init__(self):
        """Validate data on creation"""
        if self.ltp < 0:
            raise ValueError(f"LTP cannot be negative: {self.ltp}")
        if self.oi < 0 or self.volume < 0:
            raise ValueError(f"OI/Volume cannot be negative: OI={self.oi}, Vol={self.volume}")
    
    @property
    def oi_change(self) -> Optional[int]:
        """Calculate OI change from previous"""
        if self.oi_prev is not None:
            return self.oi - self.oi_prev
        return None
    
    @property
    def bid_ask_spread(self) -> Optional[float]:
        """Calculate bid-ask spread"""
        if self.bid is not None and self.ask is not None and self.bid > 0:
            return (self.ask - self.bid) / self.bid * 100
        return None
    
    @property
    def is_liquid(self) -> bool:
        """Check if strike has minimum liquidity"""
        return self.volume > 0 and self.oi > 0


@dataclass
class StrikePair:
    """CE & PE for same strike"""
    
    strike: float              # Strike price
    ce: Optional[StrikeData]   # Call option data
    pe: Optional[StrikeData]   # Put option data
    
    def __post_init__(self):
        """Validate alignment"""
        if self.ce and self.pe:
            if self.ce.strike != self.strike or self.pe.strike != self.strike:
                raise ValueError(f"Strike mismatch: {self.ce.strike} vs {self.pe.strike} vs {self.strike}")
    
    @property
    def is_complete(self) -> bool:
        """Both CE & PE present"""
        return self.ce is not None and self.pe is not None
    
    @property
    def both_liquid(self) -> bool:
        """Both sides have liquidity"""
        return (self.ce and self.ce.is_liquid) and (self.pe and self.pe.is_liquid)


@dataclass
class OptionChainSnapshot:
    """Complete snapshot of option chain"""
    
    # Universe definition
    underlying: str            # e.g., "NIFTY"
    expiry: str               # e.g., "08JAN26"
    
    # Data
    strikes: Dict[float, StrikePair] = field(default_factory=dict)
    atm_strike: Optional[float] = None
    
    # Metadata
    timestamp: datetime = field(default_factory=datetime.utcnow)
    fetch_latency_ms: float = 0.0  # Time to fetch from broker
    
    # Health
    is_partial: bool = False   # Some strikes missing
    data_quality_score: float = 0.0  # 0-100
    
    @property
    def strike_count(self) -> int:
        """Total strikes in snapshot"""
        return len(self.strikes)
    
    @property
    def complete_pairs(self) -> int:
        """Count of complete CE/PE pairs"""
        return sum(1 for pair in self.strikes.values() if pair.is_complete)
    
    @property
    def liquid_pairs(self) -> int:
        """Count of liquid CE/PE pairs"""
        return sum(1 for pair in self.strikes.values() if pair.both_liquid)
    
    def get_atm_ce(self) -> Optional[StrikeData]:
        """Get ATM call option"""
        if self.atm_strike and self.atm_strike in self.strikes:
            return self.strikes[self.atm_strike].ce
        return None
    
    def get_atm_pe(self) -> Optional[StrikeData]:
        """Get ATM put option"""
        if self.atm_strike and self.atm_strike in self.strikes:
            return self.strikes[self.atm_strike].pe
        return None
    
    def get_strike(self, offset: int) -> Optional[StrikePair]:
        """Get strike at offset from ATM (e.g., -1 = 1 strike lower)"""
        if not self.atm_strike:
            return None
        
        # Assume strikes are spaced by standard interval (typically 100 for NIFTY)
        strike_interval = 100  # TODO: auto-detect
        target_strike = self.atm_strike + (offset * strike_interval)
        
        return self.strikes.get(target_strike)
    
    def get_chain_summary(self) -> Dict:
        """Summary of chain health"""
        return {
            'underlying': self.underlying,
            'expiry': self.expiry,
            'atm_strike': self.atm_strike,
            'total_strikes': self.strike_count,
            'complete_pairs': self.complete_pairs,
            'liquid_pairs': self.liquid_pairs,
            'is_partial': self.is_partial,
            'data_quality': self.data_quality_score,
            'fetch_latency_ms': self.fetch_latency_ms,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class OptionChainDelta:
    """Changes from previous snapshot"""
    
    timestamp: datetime
    
    # Strikes that changed
    oi_changes: Dict[str, int] = field(default_factory=dict)  # "20000-CE": +500
    volume_changes: Dict[str, int] = field(default_factory=dict)
    ltp_changes: Dict[str, float] = field(default_factory=dict)
    
    # Health
    new_strikes_added: List[float] = field(default_factory=list)
    strikes_removed: List[float] = field(default_factory=list)
    stale_strikes: List[float] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        """Any changes detected"""
        return bool(self.oi_changes or self.volume_changes or 
                   self.ltp_changes or self.new_strikes_added or 
                   self.strikes_removed)
    
    @property
    def momentum_hints(self) -> Dict[str, str]:
        """Raw momentum signals (not tradable, just hints)"""
        hints = {}
        
        # OI increases suggest buyers/sellers entering
        for key, change in self.oi_changes.items():
            if change > 100:
                hints[f"{key}_oi_increasing"] = True
            elif change < -100:
                hints[f"{key}_oi_decreasing"] = True
        
        # Volume spikes
        for key, change in self.volume_changes.items():
            if change > 1000:
                hints[f"{key}_volume_spike"] = True
        
        return hints


@dataclass
class ExpiryInfo:
    """Information about contract expiry"""
    
    expiry_code: str           # e.g., "08JAN26"
    expiry_date: datetime
    is_weekly: bool = True
    
    @property
    def days_to_expiry(self) -> int:
        """Days remaining to expiry"""
        return (self.expiry_date - datetime.utcnow()).days
    
    @property
    def is_expiry_day(self) -> bool:
        """Is today the expiry day"""
        return self.days_to_expiry == 0
    
    @property
    def is_near_expiry(self) -> bool:
        """Is expiry within 3 days"""
        return 0 <= self.days_to_expiry <= 3


@dataclass
class UniverseDefinition:
    """Scope lock for option chain universe"""
    
    underlying: str            # e.g., "NIFTY"
    expiry: ExpiryInfo         # Active expiry
    
    atm_reference: float       # Reference for ATM calculation
    strikes_range: int = 5     # ATM ± N strikes
    
    @property
    def strike_range_lower(self) -> float:
        """Lower bound of strike range"""
        strike_interval = 100  # TODO: auto-detect from broker
        return self.atm_reference - (self.strikes_range * strike_interval)
    
    @property
    def strike_range_upper(self) -> float:
        """Upper bound of strike range"""
        strike_interval = 100
        return self.atm_reference + (self.strikes_range * strike_interval)
    
    @property
    def expected_strike_count(self) -> int:
        """Expected strikes (CE + PE)"""
        strike_interval = 100
        strikes_per_side = (self.strikes_range * 2) + 1
        return strikes_per_side * 2  # CE + PE


# Health Status Enum
class DataHealthStatus(Enum):
    """Health status of option chain data"""
    HEALTHY = "HEALTHY"       # All good
    DEGRADED = "DEGRADED"     # Some missing data
    UNHEALTHY = "UNHEALTHY"   # Too much missing
    STALE = "STALE"           # Data too old
    OFFLINE = "OFFLINE"       # No data


@dataclass
class DataHealthReport:
    """Health status of data"""
    
    status: DataHealthStatus
    timestamp: datetime
    
    # Metrics
    missing_strikes_percent: float = 0.0
    stale_strikes_percent: float = 0.0
    fetch_success_rate: float = 100.0
    avg_fetch_latency_ms: float = 0.0
    
    # Details
    last_fetch_time: Optional[datetime] = None
    error_message: Optional[str] = None
    recovery_suggestion: Optional[str] = None
    
    @property
    def is_trading_ready(self) -> bool:
        """Can strategy trade on this data"""
        return self.status == DataHealthStatus.HEALTHY and self.fetch_success_rate >= 95.0
