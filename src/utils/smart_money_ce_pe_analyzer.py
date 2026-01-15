"""
PHASE 4 — CE vs PE BATTLEFIELD ANALYZER
ATM Zone War Detection (Institutional Conflict)

Track:
- CE OI vs PE OI dominance
- CE Volume vs PE Volume aggression
- Delta skew (bulls vs bears positioning)
- War intensity (how contested is ATM zone)

Output: BattlefieldControl (BULLISH | BEARISH | NEUTRAL | BALANCED)

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from typing import Dict, Optional, Tuple, List
from collections import deque
from datetime import datetime

from .smart_money_models import (
    CePeBattlefield,
    BattlefieldControl,
    SmartMoneyConfig,
)


logger = logging.getLogger(__name__)


class CePeBattlefieldAnalyzer:
    """
    Analyze CE vs PE conflict in ATM zone

    Institutional positions create specific patterns:
    - Bullish Control: CE OI >> PE OI, CE Volume > PE Volume
    - Bearish Control: PE OI >> CE OI, PE Volume > CE Volume
    - Neutral/Chop: No clear dominance
    - Balanced: Fairly matched, potential reversal
    """

    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize analyzer"""
        self.config = config or SmartMoneyConfig()

        # History for momentum detection
        self.control_history: deque = deque(maxlen=20)

        # Current battlefield state
        self.current_battlefield: Optional[CePeBattlefield] = None

        # Metrics
        self.snapshots_analyzed = 0
        self.bullish_dominance_count = 0
        self.bearish_dominance_count = 0
        self.neutral_count = 0
        self.balanced_count = 0

    def analyze_battlefield(
        self,
        atm_strikes: List[float],
        strikes_data: Dict[float, Dict],  # {strike: {"CE": {...}, "PE": {...}}, ...}
    ) -> CePeBattlefield:
        """
        Analyze ATM zone CE vs PE war

        Input strikes_data format:
        {
            19900: {
                "CE": {"oi": 1000, "volume": 500, "delta": 0.3, "ltp": 100},
                "PE": {"oi": 800, "volume": 400, "delta": -0.3, "ltp": 80},
            },
            ...
        }

        Returns: CePeBattlefield analysis
        """

        # Filter to ATM zone (±5 strikes by default)
        atm_zone_strikes = self._filter_atm_zone(atm_strikes, strikes_data)

        # Aggregate CE and PE data
        ce_oi = 0
        pe_oi = 0
        ce_volume = 0
        pe_volume = 0
        ce_deltas = []
        pe_deltas = []

        for strike in atm_zone_strikes:
            if strike not in strikes_data:
                continue

            strike_data = strikes_data[strike]

            if "CE" in strike_data:
                ce_data = strike_data["CE"]
                ce_oi += ce_data.get("oi", 0)
                ce_volume += ce_data.get("volume", 0)
                if "delta" in ce_data:
                    ce_deltas.append(ce_data["delta"])

            if "PE" in strike_data:
                pe_data = strike_data["PE"]
                pe_oi += pe_data.get("oi", 0)
                pe_volume += pe_data.get("volume", 0)
                if "delta" in pe_data:
                    pe_deltas.append(pe_data["delta"])

        # Calculate dominance
        ce_oi_dominance = self._calculate_dominance(ce_oi, pe_oi)
        ce_volume_dominance = self._calculate_dominance(ce_volume, pe_volume)

        # Calculate delta skew (institutional positioning)
        delta_skew = self._calculate_delta_skew(ce_deltas, pe_deltas)

        # Determine control
        control = self._determine_control(
            ce_oi_dominance=ce_oi_dominance,
            ce_volume_dominance=ce_volume_dominance,
            delta_skew=delta_skew,
        )

        # Calculate war intensity
        war_intensity = self._calculate_war_intensity(
            ce_oi=ce_oi,
            pe_oi=pe_oi,
            ce_volume=ce_volume,
            pe_volume=pe_volume,
        )

        # Calculate momentum (which side winning recently)
        ce_momentum = self._calculate_momentum()

        # Create battlefield state
        battlefield = CePeBattlefield(
            ce_oi_dominance=ce_oi_dominance,
            ce_volume_dominance=ce_volume_dominance,
            delta_skew=delta_skew,
            ce_volume=ce_volume,
            pe_volume=pe_volume,
            ce_oi=ce_oi,
            pe_oi=pe_oi,
            control=control,
            war_intensity=war_intensity,
            ce_momentum=ce_momentum,
            timestamp=datetime.now(),
        )

        self.current_battlefield = battlefield
        self.control_history.append(control)

        # Update metrics
        self._update_metrics(control)
        self.snapshots_analyzed += 1

        logger.debug(
            f"Battlefield: {control.value} | " f"CE_OI: {ce_oi_dominance:.2f} | " f"War_Intensity: {war_intensity:.2f}"
        )

        return battlefield

    def get_current_battlefield(self) -> Optional[CePeBattlefield]:
        """Get current battlefield state"""
        return self.current_battlefield

    def get_control_trend(self) -> str:
        """
        Analyze control trend over recent snapshots

        Returns: "bullish_strengthening" | "bullish_weakening" |
                 "bearish_strengthening" | "bearish_weakening" |
                 "balanced" | "volatile"
        """

        if len(self.control_history) < 2:
            return "insufficient_data"

        # Get last 5 controls
        recent = list(self.control_history)[-5:]

        # Count each type
        bullish = sum(1 for c in recent if c == BattlefieldControl.BULLISH_CONTROL)
        bearish = sum(1 for c in recent if c == BattlefieldControl.BEARISH_CONTROL)

        # Determine trend
        if bullish >= 3:
            if bullish == 5:
                return "bullish_strengthening"
            else:
                return "bullish_weakening"
        elif bearish >= 3:
            if bearish == 5:
                return "bearish_strengthening"
            else:
                return "bearish_weakening"
        else:
            return "balanced"

    def get_expected_move_direction(self) -> str:
        """
        Predict expected move based on battlefield control

        Returns: "UP" | "DOWN" | "UNCLEAR"
        """

        if not self.current_battlefield:
            return "UNCLEAR"

        control = self.current_battlefield.control

        if control == BattlefieldControl.BULLISH_CONTROL:
            return "UP"
        elif control == BattlefieldControl.BEARISH_CONTROL:
            return "DOWN"
        else:
            return "UNCLEAR"

    def is_balanced_market(self) -> bool:
        """Check if market is balanced (no clear control)"""
        if not self.current_battlefield:
            return False

        return self.current_battlefield.control in [
            BattlefieldControl.NEUTRAL_CHOP,
            BattlefieldControl.BALANCED,
        ]

    def get_battlefield_metrics(self) -> Dict:
        """Get aggregated battlefield metrics"""

        if not self.current_battlefield:
            return {}

        bf = self.current_battlefield

        # Calculate imbalance score
        oi_imbalance = abs(bf.ce_oi_dominance - 0.5) * 2  # 0-1
        volume_imbalance = abs(bf.ce_volume_dominance - 0.5) * 2  # 0-1

        return {
            "control": bf.control.value,
            "ce_oi_dominance": bf.ce_oi_dominance,
            "ce_volume_dominance": bf.ce_volume_dominance,
            "delta_skew": bf.delta_skew,
            "war_intensity": bf.war_intensity,
            "oi_imbalance": oi_imbalance,
            "volume_imbalance": volume_imbalance,
            "ce_momentum": bf.ce_momentum,
            "trend": self.get_control_trend(),
            "expected_direction": self.get_expected_move_direction(),
        }

    def get_atm_zone_pressure(self) -> Tuple[str, float]:
        """
        Get pressure direction and intensity in ATM zone

        Returns: (direction, intensity)
        direction = "BULLISH" | "BEARISH" | "NEUTRAL"
        intensity = 0-1
        """

        if not self.current_battlefield:
            return "NEUTRAL", 0.0

        bf = self.current_battlefield

        # Determine direction from various indicators
        if bf.control == BattlefieldControl.BULLISH_CONTROL:
            direction = "BULLISH"
            intensity = bf.ce_oi_dominance
        elif bf.control == BattlefieldControl.BEARISH_CONTROL:
            direction = "BEARISH"
            intensity = bf.pe_oi_dominance = 1 - bf.ce_oi_dominance
        else:
            direction = "NEUTRAL"
            intensity = 0.5

        return direction, intensity

    def reset(self):
        """Reset all state"""
        self.control_history.clear()
        self.current_battlefield = None
        self.snapshots_analyzed = 0
        self.bullish_dominance_count = 0
        self.bearish_dominance_count = 0
        self.neutral_count = 0
        self.balanced_count = 0

    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================

    def _filter_atm_zone(
        self,
        atm_strikes: List[float],
        strikes_data: Dict[float, Dict],
    ) -> List[float]:
        """Filter strikes within ATM zone"""

        if not atm_strikes:
            return list(strikes_data.keys())

        # Get min ATM strike (lowest reference)
        atm_ref = min(atm_strikes) if atm_strikes else 0

        # Filter within ±5 of ATM (configurable)
        zone_range = self.config.ce_pe_atm_range

        filtered = [strike for strike in strikes_data.keys() if abs(strike - atm_ref) <= zone_range]

        return sorted(filtered)

    def _calculate_dominance(self, ce_value: int, pe_value: int) -> float:
        """
        Calculate dominance ratio (0-1)

        0.0 = PE dominant (100%)
        0.5 = Balanced
        1.0 = CE dominant (100%)
        """

        total = ce_value + pe_value
        if total == 0:
            return 0.5

        return ce_value / total

    def _calculate_delta_skew(
        self,
        ce_deltas: List[float],
        pe_deltas: List[float],
    ) -> float:
        """
        Calculate delta skew (institutional positioning)

        0.0 = PE dominated (negative deltas)
        0.5 = Balanced
        1.0 = CE dominated (positive deltas)
        """

        if not ce_deltas and not pe_deltas:
            return 0.5

        ce_avg = sum(ce_deltas) / len(ce_deltas) if ce_deltas else 0
        pe_avg = sum(pe_deltas) / len(pe_deltas) if pe_deltas else 0

        # Normalize to 0-1 range
        # CE deltas typically 0.2-0.7, PE deltas typically -0.7 to -0.2
        total_abs = abs(ce_avg) + abs(pe_avg)

        if total_abs == 0:
            return 0.5

        return abs(ce_avg) / total_abs

    def _determine_control(
        self,
        ce_oi_dominance: float,
        ce_volume_dominance: float,
        delta_skew: float,
    ) -> BattlefieldControl:
        """
        Determine battlefield control based on indicators

        BULLISH: CE > 55%, high CE volume, positive delta
        BEARISH: PE > 55%, high PE volume, negative delta
        BALANCED: ~50/50 split
        NEUTRAL/CHOP: Mixed signals
        """

        # Check if CE dominant
        if ce_oi_dominance > 0.55 and ce_volume_dominance > 0.55 and delta_skew > 0.55:
            return BattlefieldControl.BULLISH_CONTROL

        # Check if PE dominant
        if ce_oi_dominance < 0.45 and ce_volume_dominance < 0.45 and delta_skew < 0.45:
            return BattlefieldControl.BEARISH_CONTROL

        # Check if balanced
        if 0.45 <= ce_oi_dominance <= 0.55:
            return BattlefieldControl.BALANCED

        # Otherwise neutral/chop
        return BattlefieldControl.NEUTRAL_CHOP

    def _calculate_war_intensity(
        self,
        ce_oi: int,
        pe_oi: int,
        ce_volume: int,
        pe_volume: int,
    ) -> float:
        """
        Calculate war intensity (0-1)

        0.0 = No activity
        0.5 = Normal competition
        1.0 = Intense battle
        """

        # Total activity
        total_oi = ce_oi + pe_oi
        total_volume = ce_volume + pe_volume

        if total_oi == 0 or total_volume == 0:
            return 0.0

        # Balance in OI and volume (closer to 50/50 = more intense)
        ce_oi_ratio = ce_oi / total_oi
        ce_vol_ratio = ce_volume / total_volume

        # Distance from balanced (0.5)
        oi_balance = 1 - abs(ce_oi_ratio - 0.5) * 2  # 0-1
        vol_balance = 1 - abs(ce_vol_ratio - 0.5) * 2  # 0-1

        # Activity level
        activity = min((total_oi + total_volume) / 10000, 1.0)  # Normalize

        # War intensity = average balance * activity
        intensity = (oi_balance + vol_balance) / 2 * activity

        return min(intensity, 1.0)

    def _calculate_momentum(self) -> float:
        """
        Calculate CE momentum (positive = CE gaining)

        0.0 = PE completely dominant
        0.5 = Balanced
        1.0 = CE completely dominant
        """

        if not self.current_battlefield:
            return 0.5

        # Base momentum on current dominance
        momentum = self.current_battlefield.ce_oi_dominance

        # Adjust based on recent trend
        if len(self.control_history) >= 2:
            recent_controls = list(self.control_history)[-3:]

            bullish_count = sum(1 for c in recent_controls if c == BattlefieldControl.BULLISH_CONTROL)
            bearish_count = sum(1 for c in recent_controls if c == BattlefieldControl.BEARISH_CONTROL)

            if bullish_count > bearish_count:
                momentum = min(momentum + 0.1, 1.0)
            elif bearish_count > bullish_count:
                momentum = max(momentum - 0.1, 0.0)

        return momentum

    def _update_metrics(self, control: BattlefieldControl):
        """Update control metrics"""

        if control == BattlefieldControl.BULLISH_CONTROL:
            self.bullish_dominance_count += 1
        elif control == BattlefieldControl.BEARISH_CONTROL:
            self.bearish_dominance_count += 1
        elif control == BattlefieldControl.BALANCED:
            self.balanced_count += 1
        else:
            self.neutral_count += 1

    def get_metrics(self) -> Dict:
        """Get analyzer metrics"""
        total = self.snapshots_analyzed

        return {
            "snapshots_analyzed": total,
            "bullish_dominance": self.bullish_dominance_count,
            "bearish_dominance": self.bearish_dominance_count,
            "balanced": self.balanced_count,
            "neutral": self.neutral_count,
            "bullish_percentage": (self.bullish_dominance_count / max(total, 1) * 100),
            "bearish_percentage": (self.bearish_dominance_count / max(total, 1) * 100),
        }
