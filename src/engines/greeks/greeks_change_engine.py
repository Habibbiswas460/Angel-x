"""
PHASE 3 — Greeks Change & Velocity Engine
Detects Greek movement, zone transitions, danger signals

Components:
    • GreeksChangeTracker - Maintain current + previous Greeks, calculate velocity
    • ZoneDetector - Identify Gamma peak, Theta kill, Delta neutral zones
    • MomentumAnalyzer - Detect bullish/bearish acceleration
"""

import logging
from datetime import datetime
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass, field

from .greeks_models import GreeksSnapshot, GreeksDelta, AtmIntelligence, OptionType, ZoneType

logger = logging.getLogger(__name__)


# ============================================================================
# Greeks Change Tracker
# ============================================================================


class GreeksChangeTracker:
    """
    Maintain current + previous Greeks snapshots
    Calculate velocity (ΔΔ, Γ expansion, Θ spike, Vega surge)

    Used for: Detecting movement, acceleration, danger zones
    """

    def __init__(self, max_history: int = 20):
        """Initialize tracker"""
        self.current_greeks: Dict[float, GreeksSnapshot] = {}  # strike -> latest Greeks
        self.previous_greeks: Dict[float, GreeksSnapshot] = {}  # strike -> previous Greeks
        self.history: Dict[float, List[GreeksSnapshot]] = {}  # strike -> history
        self.max_history = max_history

        logger.info(f"Greeks Change Tracker initialized (max_history={max_history})")

    def update(self, strike: float, new_greek: GreeksSnapshot) -> GreeksDelta:
        """
        Update Greeks for a strike
        Returns: GreeksDelta with changes detected
        """
        # Shift: current → previous
        if strike in self.current_greeks:
            self.previous_greeks[strike] = self.current_greeks[strike]
            # Set previous values for change calculation
            new_greek.delta_previous = self.previous_greeks[strike].delta
            new_greek.gamma_previous = self.previous_greeks[strike].gamma
            new_greek.theta_previous = self.previous_greeks[strike].theta
            new_greek.vega_previous = self.previous_greeks[strike].vega

        # Update current
        self.current_greeks[strike] = new_greek

        # Maintain history
        if strike not in self.history:
            self.history[strike] = []
        self.history[strike].append(new_greek)
        if len(self.history[strike]) > self.max_history:
            self.history[strike].pop(0)

        # Calculate delta
        delta = self._calculate_delta(strike)

        logger.debug(f"Greeks updated for strike {strike}: ΔΔ={delta.overall_delta_momentum:.3f}")
        return delta

    def _calculate_delta(self, strike: float) -> GreeksDelta:
        """Calculate GreeksDelta from current Greeks and previous"""
        current = self.current_greeks.get(strike)
        previous = self.previous_greeks.get(strike)

        delta = GreeksDelta(timestamp=datetime.now())

        if current and previous:
            # Individual changes
            delta.delta_changes[strike] = current.delta_change or 0.0
            delta.gamma_changes[strike] = current.gamma_expansion or 0.0
            delta.theta_changes[strike] = current.theta_spike or 0.0
            delta.vega_changes[strike] = current.vega_surge or 0.0

            # Aggregate
            delta.overall_delta_momentum = current.delta_change or 0.0
            delta.gamma_expansion_count = 1 if (current.gamma_expansion or 0) > 0 else 0
            delta.theta_spike_detected = (current.theta_spike or 0) < -0.001  # Negative = faster decay
            delta.vega_surge_detected = abs(current.vega_surge or 0) > 0.01

        return delta

    def get_current(self, strike: float) -> Optional[GreeksSnapshot]:
        """Get latest Greeks for strike"""
        return self.current_greeks.get(strike)

    def get_previous(self, strike: float) -> Optional[GreeksSnapshot]:
        """Get previous Greeks for strike"""
        return self.previous_greeks.get(strike)

    def get_all_current(self) -> Dict[float, GreeksSnapshot]:
        """Get all current Greeks"""
        return dict(self.current_greeks)

    def get_history(self, strike: float) -> List[GreeksSnapshot]:
        """Get history for strike (oldest to newest)"""
        return self.history.get(strike, [])


# ============================================================================
# Zone Detector (Gamma Peak, Theta Kill, etc.)
# ============================================================================


class ZoneDetector:
    """
    Detect important zones in option chain
    Identifies: Gamma peak zone, Theta kill zone, Delta neutral zone

    Used for: Telling strategy where to trade and where to avoid
    """

    def __init__(
        self,
        gamma_peak_threshold: float = 0.08,  # Gamma >= 0.08 is peak
        theta_kill_threshold: float = -0.5,  # |Theta| >= 0.5/day is kill zone
        delta_neutral_tolerance: float = 0.05,  # Delta 0.45-0.55 is neutral
    ):
        """Initialize zone detector thresholds"""
        self.gamma_peak_threshold = gamma_peak_threshold
        self.theta_kill_threshold = abs(theta_kill_threshold)
        self.delta_neutral_tolerance = delta_neutral_tolerance

        logger.info(
            f"Zone Detector initialized: gamma_threshold={gamma_peak_threshold}, "
            f"theta_kill_threshold={self.theta_kill_threshold}"
        )

    def analyze_atm_zone(self, atm_strike: float, greeks_dict: Dict[float, GreeksSnapshot]) -> AtmIntelligence:
        """
        Analyze ATM ±5 zone and identify important zones

        Returns: AtmIntelligence with zone locations and signals
        """
        intelligence = AtmIntelligence(atm_strike=atm_strike)

        if not greeks_dict:
            logger.warning("No Greeks data to analyze")
            return intelligence

        # -------- Find Gamma Peak Zone --------
        max_gamma = 0.0
        gamma_peak_strike = None
        for strike, greek in greeks_dict.items():
            if greek.gamma > max_gamma:
                max_gamma = greek.gamma
                gamma_peak_strike = strike

        intelligence.gamma_peak_strike = gamma_peak_strike
        intelligence.gamma_peak_value = max_gamma
        intelligence.is_gamma_peak_safe = max_gamma < self.gamma_peak_threshold

        # -------- Find Theta Kill Zone --------
        max_theta_abs = 0.0
        theta_kill_strike = None
        for strike, greek in greeks_dict.items():
            theta_abs = abs(greek.theta)
            if theta_abs > max_theta_abs:
                max_theta_abs = theta_abs
                theta_kill_strike = strike

        intelligence.theta_kill_zone_strike = theta_kill_strike
        intelligence.theta_kill_value = max_theta_abs
        intelligence.is_theta_safe = max_theta_abs < self.theta_kill_threshold

        # -------- Find Delta Neutral Zone --------
        # Find call with Delta closest to 0.5 and put with Delta closest to -0.5
        closest_call = None
        closest_call_delta_diff = float("inf")
        closest_put = None
        closest_put_delta_diff = float("inf")

        for strike, greek in greeks_dict.items():
            if greek.option_type == OptionType.CALL:
                delta_diff = abs(greek.delta - 0.5)
                if delta_diff < closest_call_delta_diff:
                    closest_call_delta_diff = delta_diff
                    closest_call = strike
            else:  # PUT
                delta_diff = abs(greek.delta + 0.5)  # Put delta ~-0.5 for ATM
                if delta_diff < closest_put_delta_diff:
                    closest_put_delta_diff = delta_diff
                    closest_put = strike

        if closest_call and closest_put:
            intelligence.delta_neutral_zone = (closest_call, closest_put)

        # -------- ATM CE vs PE Delta Battle --------
        atm_ce = None
        atm_pe = None

        for strike, greek in greeks_dict.items():
            if abs(strike - atm_strike) < 1.0:  # Close to ATM
                if greek.option_type == OptionType.CALL:
                    atm_ce = greek
                else:
                    atm_pe = greek

        if atm_ce and atm_pe:
            intelligence.atm_ce_delta = atm_ce.delta
            intelligence.atm_pe_delta = atm_pe.delta  # Should be ~-0.5

            # Delta battle direction (which is winning?)
            # CE delta increases = bullish
            # PE delta increases (becomes less negative) = bullish
            combined_delta = atm_ce.delta + abs(atm_pe.delta)  # Normalize to 0-2
            if combined_delta > 1.05:
                intelligence.delta_battle_direction = "CE_LEADING"  # Bullish
            elif combined_delta < 0.95:
                intelligence.delta_battle_direction = "PE_LEADING"  # Bearish
            else:
                intelligence.delta_battle_direction = "NEUTRAL"

        intelligence.timestamp = datetime.now()

        logger.debug(
            f"Zone analysis: Gamma peak at {intelligence.gamma_peak_strike} "
            f"({intelligence.gamma_peak_value:.4f}), Theta kill at {intelligence.theta_kill_zone_strike} "
            f"({intelligence.theta_kill_value:.4f}), Delta battle: {intelligence.delta_battle_direction}"
        )

        return intelligence

    def get_zone_type(self, strike: float, greek: GreeksSnapshot) -> ZoneType:
        """Classify strike into zone type"""
        # Simple classification
        if greek.gamma > self.gamma_peak_threshold * 0.8:
            return ZoneType.GAMMA_PEAK

        if abs(greek.theta) > self.theta_kill_threshold * 0.8:
            return ZoneType.THETA_KILL

        if abs(greek.delta - 0.5) < self.delta_neutral_tolerance:
            return ZoneType.DELTA_NEUTRAL

        if greek.option_type == OptionType.CALL:
            if greek.delta > 0.5:
                return ZoneType.SAFE_CALL
        else:
            if greek.delta < -0.5:
                return ZoneType.SAFE_PUT

        # Default to DELTA_NEUTRAL if unclear
        return ZoneType.DELTA_NEUTRAL


# ============================================================================
# Momentum Analyzer
# ============================================================================


class MomentumAnalyzer:
    """
    Analyze Greek momentum across the chain
    Detects: Bullish/bearish acceleration, trend reversals
    """

    def __init__(self):
        """Initialize analyzer"""
        logger.info("Momentum Analyzer initialized")

    def analyze_momentum(self, greeks_dict: Dict[float, GreeksSnapshot], atm_strike: float) -> Dict:
        """
        Analyze momentum signals from Greeks

        Returns:
            {
                "direction": "BULLISH" | "BEARISH" | "NEUTRAL",
                "strength": 0-1,
                "acceleration_score": 0-1,
                "signals": ["signal1", "signal2", ...]
            }
        """
        momentum_data = {"direction": "NEUTRAL", "strength": 0.5, "acceleration_score": 0.5, "signals": []}

        if not greeks_dict:
            return momentum_data

        # -------- Delta Momentum --------
        bullish_delta_count = 0
        bearish_delta_count = 0
        total_delta_change = 0.0

        for strike, greek in greeks_dict.items():
            if greek.delta_change is not None:
                total_delta_change += greek.delta_change
                if greek.delta_change > 0:
                    bullish_delta_count += 1
                elif greek.delta_change < 0:
                    bearish_delta_count += 1

        if bullish_delta_count > bearish_delta_count:
            momentum_data["direction"] = "BULLISH"
            momentum_data["strength"] = min(bullish_delta_count / max(len(greeks_dict), 1), 1.0)
            momentum_data["signals"].append("DELTA_ACCUMULATION_BULLISH")
        elif bearish_delta_count > bullish_delta_count:
            momentum_data["direction"] = "BEARISH"
            momentum_data["strength"] = min(bearish_delta_count / max(len(greeks_dict), 1), 1.0)
            momentum_data["signals"].append("DELTA_ACCUMULATION_BEARISH")

        # -------- Gamma Expansion --------
        gamma_expanding = 0
        gamma_compressing = 0

        for strike, greek in greeks_dict.items():
            if greek.gamma_expansion is not None:
                if greek.gamma_expansion > 0.001:
                    gamma_expanding += 1
                elif greek.gamma_expansion < -0.001:
                    gamma_compressing += 1

        if gamma_expanding > gamma_compressing:
            momentum_data["acceleration_score"] += 0.2
            momentum_data["signals"].append("GAMMA_EXPANDING")

        # Normalize
        momentum_data["acceleration_score"] = min(momentum_data["acceleration_score"], 1.0)

        logger.debug(
            f"Momentum: {momentum_data['direction']} "
            f"(strength={momentum_data['strength']:.2f}, "
            f"accel={momentum_data['acceleration_score']:.2f})"
        )

        return momentum_data
