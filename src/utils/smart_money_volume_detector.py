"""
PHASE 4 — VOLUME SPIKE DETECTOR
Sudden Aggression & Volume Trend Analysis

Detect:
- Volume spikes (1.5x to 3x average)
- Sudden aggression bursts
- ATM vs OTM volume shift (direction signal)
- Relative volume trends

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
import statistics
from typing import Dict, Optional, Tuple, List
from collections import deque
from datetime import datetime

from .smart_money_models import (
    VolumeState,
    VolumeSnapshot,
    SmartMoneyConfig,
)


logger = logging.getLogger(__name__)


class VolumeSpikeDetector:
    """
    Analyzes volume patterns to detect retail vs institutional activity
    
    Classification:
    - NORMAL: Within expected range
    - SPIKE: 1.5x to 2.5x average volume
    - BURST: 2.5x to 3.5x average
    - AGGRESSIVE: >3.5x average
    - UNUSUAL: Unexpected pattern (reversal of trend, etc.)
    """
    
    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize with configuration"""
        self.config = config or SmartMoneyConfig()
        
        # Store volume history for each strike
        self.volume_history: Dict[Tuple[float, str], deque] = {}
        
        # Statistics cache (updated per snapshot)
        self.strike_stats: Dict[Tuple[float, str], Dict] = {}
        
        # Metrics
        self.spikes_detected = 0
        self.bursts_detected = 0
        self.aggressive_detected = 0
        self.snapshots_processed = 0
    
    def detect_volume_spike(
        self,
        strike: float,
        option_type: str,
        current_volume: int,
    ) -> Tuple[VolumeState, float]:
        """
        Detect if current volume is a spike
        
        Returns: (state, spike_factor)
        spike_factor = current_volume / rolling_average
        """
        
        key = (strike, option_type)
        
        # Initialize history if needed
        if key not in self.volume_history:
            self.volume_history[key] = deque(maxlen=self.config.history_size)
            self.strike_stats[key] = {}
        
        history = self.volume_history[key]
        
        # Add current volume
        history.append(current_volume)
        
        # Need at least 2 samples for comparison
        if len(history) < 2:
            self.snapshots_processed += 1
            return VolumeState.NORMAL, 1.0
        
        # Calculate rolling average (excluding current)
        if len(history) > 1:
            avg = statistics.mean(list(history)[:-1])
        else:
            avg = history[0]
        
        if avg == 0:
            spike_factor = 1.0
        else:
            spike_factor = current_volume / avg
        
        # Update stats
        self.strike_stats[key] = {
            "avg_volume": avg,
            "current_volume": current_volume,
            "spike_factor": spike_factor,
            "timestamp": datetime.now(),
        }
        
        # Classify
        state = self._classify_spike(spike_factor)
        
        # Update metrics
        if state == VolumeState.SPIKE:
            self.spikes_detected += 1
        elif state == VolumeState.BURST:
            self.bursts_detected += 1
        elif state == VolumeState.AGGRESSIVE:
            self.aggressive_detected += 1
        
        self.snapshots_processed += 1
        
        logger.debug(
            f"Strike {strike} {option_type}: {state.value} "
            f"(factor={spike_factor:.2f})"
        )
        
        return state, spike_factor
    
    def detect_atm_vs_otm_shift(
        self,
        atm_volume: int,
        otm_volume: int,
    ) -> str:
        """
        Detect if volume is shifting from OTM to ATM or vice versa
        
        Returns: "atm_focus", "otm_focus", "neutral"
        ATM volume spike = direction forming
        """
        
        if atm_volume == 0 and otm_volume == 0:
            return "neutral"
        
        if atm_volume == 0:
            ratio = 0
        elif otm_volume == 0:
            ratio = float('inf')
        else:
            ratio = atm_volume / otm_volume
        
        if ratio > 1.5:
            return "atm_focus"
        elif ratio < 0.67:
            return "otm_focus"
        else:
            return "neutral"
    
    def get_volume_aggression_score(
        self,
        strike: float,
        option_type: str,
    ) -> float:
        """
        Get aggression score for a strike (0-1)
        
        0.0 = normal/low activity
        1.0 = maximum aggression
        """
        
        key = (strike, option_type)
        if key not in self.strike_stats:
            return 0.0
        
        stats = self.strike_stats[key]
        spike_factor = stats.get("spike_factor", 1.0)
        
        # Map spike_factor to aggression score
        # Normal (1.0) → 0.0
        # Spike (1.5) → 0.3
        # Burst (2.5) → 0.6
        # Aggressive (3.5) → 1.0
        
        if spike_factor <= 1.0:
            return 0.0
        elif spike_factor <= 1.5:
            return (spike_factor - 1.0) / 0.5 * 0.3
        elif spike_factor <= 2.5:
            return 0.3 + (spike_factor - 1.5) / 1.0 * 0.3
        elif spike_factor <= 3.5:
            return 0.6 + (spike_factor - 2.5) / 1.0 * 0.4
        else:
            return 1.0
    
    def get_sudden_aggression_burst(
        self,
        strike: float,
        option_type: str,
    ) -> bool:
        """
        Detect if volume suddenly jumped in last snapshot
        
        True if: current_volume > 2x average of previous 5 samples
        """
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return False
        
        history = self.volume_history[key]
        if len(history) < 6:
            return False
        
        # Current volume
        current = history[-1]
        
        # Average of previous 5
        prev_avg = statistics.mean(list(history)[-6:-1])
        
        # Check for burst
        return current > prev_avg * 2.0
    
    def get_relative_volume_rank(
        self,
        strike: float,
        option_type: str,
    ) -> Tuple[float, int]:
        """
        Get where current volume ranks vs history
        
        Returns: (percentile, rank_out_of_n)
        percentile = 0-1 (0=lowest, 1=highest)
        rank = current rank out of history size
        """
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return 0.0, 0
        
        history = list(self.volume_history[key])
        if not history:
            return 0.0, 0
        
        current = history[-1]
        sorted_hist = sorted(history)
        
        # Find rank
        rank = sum(1 for v in sorted_hist if v <= current)
        total = len(sorted_hist)
        
        percentile = rank / max(total, 1)
        
        return percentile, rank
    
    def analyze_volume_trend(
        self,
        strike: float,
        option_type: str,
    ) -> str:
        """
        Analyze volume trend over recent history
        
        Returns: "increasing", "decreasing", "stable"
        """
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return "stable"
        
        history = list(self.volume_history[key])
        if len(history) < 3:
            return "stable"
        
        # Get last 3 samples
        recent = history[-3:]
        
        # Simple trend: compare first vs last
        if recent[-1] > recent[0] * 1.2:
            return "increasing"
        elif recent[-1] < recent[0] * 0.8:
            return "decreasing"
        else:
            return "stable"
    
    def get_cumulative_volume(
        self,
        strike: float,
        option_type: str,
        lookback_samples: int = 5,
    ) -> int:
        """Get cumulative volume over last N samples"""
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return 0
        
        history = list(self.volume_history[key])
        if not history:
            return 0
        
        recent = history[-lookback_samples:]
        return sum(recent)
    
    def get_average_volume(
        self,
        strike: float,
        option_type: str,
    ) -> float:
        """Get average volume across history"""
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return 0.0
        
        history = self.volume_history[key]
        if not history:
            return 0.0
        
        return statistics.mean(history)
    
    def get_volume_volatility(
        self,
        strike: float,
        option_type: str,
    ) -> float:
        """Get standard deviation of volume"""
        
        key = (strike, option_type)
        if key not in self.volume_history:
            return 0.0
        
        history = list(self.volume_history[key])
        if len(history) < 2:
            return 0.0
        
        return statistics.stdev(history)
    
    def reset(self):
        """Reset all state"""
        self.volume_history.clear()
        self.strike_stats.clear()
        self.spikes_detected = 0
        self.bursts_detected = 0
        self.aggressive_detected = 0
        self.snapshots_processed = 0
    
    def get_metrics(self) -> Dict:
        """Get detector metrics"""
        return {
            "snapshots_processed": self.snapshots_processed,
            "spikes_detected": self.spikes_detected,
            "bursts_detected": self.bursts_detected,
            "aggressive_detected": self.aggressive_detected,
            "strikes_tracked": len(self.volume_history),
        }
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _classify_spike(self, spike_factor: float) -> VolumeState:
        """Classify volume spike based on factor"""
        
        if spike_factor <= self.config.volume_spike_threshold:
            return VolumeState.NORMAL
        elif spike_factor <= self.config.volume_burst_threshold:
            return VolumeState.SPIKE
        elif spike_factor <= self.config.volume_aggression_threshold:
            return VolumeState.BURST
        else:
            return VolumeState.AGGRESSIVE


class ChainVolumeAnalyzer:
    """
    Analyze volume patterns across entire option chain
    
    Detect:
    - Total chain volume vs normal
    - Volume migration patterns
    - Concentration in specific strikes
    """
    
    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize analyzer"""
        self.config = config or SmartMoneyConfig()
        self.chain_volume_history: deque = deque(maxlen=self.config.history_size)
        self.strike_volume_distribution: Dict[float, float] = {}
    
    def analyze_chain_volume(
        self,
        strikes_volume: Dict[float, int],  # {strike: volume, ...}
    ) -> Tuple[float, str]:
        """
        Analyze total chain volume
        
        Returns: (aggression_score 0-1, trend string)
        """
        
        total_volume = sum(strikes_volume.values())
        self.chain_volume_history.append(total_volume)
        
        if len(self.chain_volume_history) < 2:
            return 0.5, "insufficient_data"
        
        # Calculate average of previous
        avg = statistics.mean(list(self.chain_volume_history)[:-1])
        
        if avg == 0:
            return 0.5, "no_baseline"
        
        # Current vs average
        current_factor = total_volume / avg
        
        # Map to aggression
        if current_factor < 0.8:
            trend = "low_activity"
            aggression = current_factor * 0.5
        elif current_factor < 1.2:
            trend = "normal_activity"
            aggression = 0.5
        elif current_factor < 1.8:
            trend = "elevated_activity"
            aggression = 0.5 + (current_factor - 1.2) / 0.6 * 0.3
        else:
            trend = "surge_activity"
            aggression = 0.8 + min((current_factor - 1.8) / 1.0 * 0.2, 0.2)
        
        return min(aggression, 1.0), trend
    
    def get_volume_concentration(
        self,
        strikes_volume: Dict[float, int],
    ) -> Dict[float, float]:
        """
        Get volume concentration per strike
        
        Returns: {strike: percentage_of_total, ...}
        """
        
        total = sum(strikes_volume.values())
        if total == 0:
            return {}
        
        concentration = {}
        for strike, vol in strikes_volume.items():
            concentration[strike] = vol / total
        
        self.strike_volume_distribution = concentration
        return concentration
    
    def get_top_volume_strikes(
        self,
        strikes_volume: Dict[float, int],
        top_n: int = 3,
    ) -> List[Tuple[float, int]]:
        """Get top N strikes by volume"""
        
        sorted_strikes = sorted(
            strikes_volume.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return sorted_strikes[:top_n]
