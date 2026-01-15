"""
PHASE 4 — FAKE MOVE & TRAP FILTER
Avoid Scalper Traps & Theta Crushes

Detect and block:
1. Scalper Trap: Low OI + High Volume (fake breakout)
2. Noise Trap: Gamma flat + Volume spike (no acceleration)
3. Theta Crush: Theta aggressive + Decay (time decay trap)
4. Reversal Trap: Volume fail at resistance/support
5. Liquidity Trap: Low OI at extreme strikes

Output: TrapType + Probability (0-1)
Angel-X says: NO TRADE

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from typing import Dict, Optional, Tuple, List

from .smart_money_models import (
    TrapType,
    SmartMoneyConfig,
)


logger = logging.getLogger(__name__)


class FakeMoveAndTrapFilter:
    """
    Detect and filter out retail scalper traps

    Traps are where volume is high but OI is low (or decreasing)
    Market makers create false breakouts to stop retail traders

    Angel-X blocks these automatically
    """

    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize filter"""
        self.config = config or SmartMoneyConfig()

        # Metrics
        self.traps_detected = 0
        self.scalper_traps = 0
        self.noise_traps = 0
        self.theta_traps = 0
        self.reversal_traps = 0
        self.liquidity_traps = 0
        self.validations_count = 0

    def detect_scalper_trap(
        self,
        oi: int,
        previous_oi: Optional[int],
        volume: int,
        previous_volume: Optional[int],
    ) -> Tuple[bool, float]:
        """
        Detect Scalper Trap: Low OI + High Volume

        Psychology: Market maker absorbs volume without building OI
        Signal: Price moves but nobody building positions

        Returns: (is_trap, probability 0-1)
        """

        # Trap if:
        # OI is low (< threshold)
        # Volume is high (> threshold)
        # OI is decreasing or flat (positions unwinding)

        oi_low = oi < self.config.trap_low_oi_threshold

        volume_high = False
        if previous_volume and previous_volume > 0:
            volume_high = volume / previous_volume > self.config.trap_volume_surge_threshold

        oi_decreasing = False
        if previous_oi is not None:
            oi_decreasing = oi < previous_oi

        # Trap probability
        prob = 0.0

        if oi_low:
            prob += 0.3

        if volume_high:
            prob += 0.4

        if oi_decreasing:
            prob += 0.3

        is_trap = prob >= 0.6

        if is_trap:
            self.scalper_traps += 1
            self.traps_detected += 1

        logger.debug(f"Scalper trap check: OI={oi}, Vol={volume}, " f"Trap={is_trap}, Prob={prob:.2f}")

        return is_trap, min(prob, 1.0)

    def detect_noise_trap(
        self,
        gamma: float,
        volume: int,
        previous_volume: Optional[int],
    ) -> Tuple[bool, float]:
        """
        Detect Noise Trap: Gamma flat + Volume spike

        Psychology: High volume but no acceleration potential
        Signal: Volume spike with low gamma = no follow-through

        Returns: (is_trap, probability 0-1)
        """

        # Trap if:
        # Gamma is flat (< threshold, indicating no acceleration)
        # Volume is high (spike)

        gamma_flat = abs(gamma) < self.config.trap_gamma_flat_threshold

        volume_spike = False
        if previous_volume and previous_volume > 0:
            volume_spike = volume / previous_volume > self.config.trap_volume_surge_threshold

        # Trap probability
        prob = 0.0

        if gamma_flat:
            prob += 0.4

        if volume_spike:
            prob += 0.6

        is_trap = prob >= 0.7

        if is_trap:
            self.noise_traps += 1
            self.traps_detected += 1

        logger.debug(f"Noise trap check: Gamma={gamma}, Vol={volume}, " f"Trap={is_trap}, Prob={prob:.2f}")

        return is_trap, min(prob, 1.0)

    def detect_theta_trap(
        self,
        theta: float,
        previous_theta: Optional[float],
        days_to_expiry: float,
    ) -> Tuple[bool, float]:
        """
        Detect Theta Trap: Theta aggressive + Fast decay

        Psychology: Theta decay accelerates near expiry
        Signal: Theta jumping aggressively = rapid decay coming

        Returns: (is_trap, probability 0-1)
        """

        # Trap if:
        # Theta is very negative (aggressive decay)
        # Theta increasing in magnitude (accelerating)
        # Days to expiry is low (< 2 days = gamma/theta extreme)

        theta_aggressive = abs(theta) > 0.5

        theta_accelerating = False
        if previous_theta is not None:
            theta_accelerating = abs(theta) > abs(previous_theta) * 1.2

        expiry_close = days_to_expiry < 2.0

        # Trap probability
        prob = 0.0

        if theta_aggressive:
            prob += 0.3

        if theta_accelerating:
            prob += 0.4

        if expiry_close:
            prob += 0.3

        is_trap = prob >= 0.6

        if is_trap:
            self.theta_traps += 1
            self.traps_detected += 1

        logger.debug(f"Theta trap check: Theta={theta}, DTE={days_to_expiry}, " f"Trap={is_trap}, Prob={prob:.2f}")

        return is_trap, min(prob, 1.0)

    def detect_reversal_trap(
        self,
        volume: int,
        previous_volume: Optional[int],
        price_change: float,
        previous_price_change: Optional[float],
    ) -> Tuple[bool, float]:
        """
        Detect Reversal Trap: Volume fail at key levels

        Psychology: Volume fails when buyers/sellers exhaust
        Signal: Volume spike but price reverses next candle

        Returns: (is_trap, probability 0-1)
        """

        # Trap if:
        # Previous volume was high
        # Current volume is normal or decreasing
        # Price moved up then reversed down (or vice versa)

        volume_declining = False
        if previous_volume and previous_volume > 0:
            volume_declining = volume < previous_volume * 0.5

        price_reversing = False
        if previous_price_change is not None:
            # Opposite direction from previous
            price_reversing = (previous_price_change > 0 and price_change < 0) or (
                previous_price_change < 0 and price_change > 0
            )

        # Trap probability
        prob = 0.0

        if volume_declining:
            prob += 0.5

        if price_reversing:
            prob += 0.5

        is_trap = prob >= 0.7

        if is_trap:
            self.reversal_traps += 1
            self.traps_detected += 1

        logger.debug(
            f"Reversal trap check: Vol_Declining={volume_declining}, "
            f"Price_Reversing={price_reversing}, Trap={is_trap}, Prob={prob:.2f}"
        )

        return is_trap, min(prob, 1.0)

    def detect_liquidity_trap(
        self,
        oi: int,
        strike_position: str,  # "ATM" | "OTM" | "ITM"
    ) -> Tuple[bool, float]:
        """
        Detect Liquidity Trap: Low OI at extreme strikes

        Psychology: Retail trapped in low-liquidity strikes
        Signal: Trading at extreme strike with minimal OI

        Returns: (is_trap, probability 0-1)
        """

        # Trap if:
        # Strike is OTM (away from ATM)
        # OI is low

        oi_very_low = oi < self.config.trap_low_oi_threshold / 2

        is_extreme = strike_position == "OTM"

        # Trap probability
        prob = 0.0

        if oi_very_low:
            prob += 0.4

        if is_extreme:
            prob += 0.6

        is_trap = prob >= 0.7

        if is_trap:
            self.liquidity_traps += 1
            self.traps_detected += 1

        logger.debug(f"Liquidity trap check: OI={oi}, Position={strike_position}, " f"Trap={is_trap}, Prob={prob:.2f}")

        return is_trap, min(prob, 1.0)

    def comprehensive_trap_check(
        self,
        oi: int,
        previous_oi: Optional[int],
        volume: int,
        previous_volume: Optional[int],
        gamma: float,
        theta: float,
        previous_theta: Optional[float],
        price_change: float,
        previous_price_change: Optional[float],
        days_to_expiry: float,
        strike_position: str = "ATM",
    ) -> Dict:
        """
        Comprehensive trap detection across all types

        Returns: {
            "is_trap": bool,
            "trap_type": TrapType,
            "probability": 0-1,
            "reasons": [list of trap reasons],
            "should_block": bool,
        }
        """

        self.validations_count += 1

        reasons = []
        trap_probabilities = {}

        # Check all trap types
        scalper_trap, scalper_prob = self.detect_scalper_trap(oi, previous_oi, volume, previous_volume)
        if scalper_trap:
            trap_probabilities["scalper"] = scalper_prob
            reasons.append("Low OI + High Volume (Scalper Trap)")

        noise_trap, noise_prob = self.detect_noise_trap(gamma, volume, previous_volume)
        if noise_trap:
            trap_probabilities["noise"] = noise_prob
            reasons.append("Gamma flat + Volume spike (Noise Trap)")

        theta_trap, theta_prob = self.detect_theta_trap(theta, previous_theta, days_to_expiry)
        if theta_trap:
            trap_probabilities["theta"] = theta_prob
            reasons.append("Theta aggressive + Decay (Theta Trap)")

        reversal_trap, reversal_prob = self.detect_reversal_trap(
            volume, previous_volume, price_change, previous_price_change
        )
        if reversal_trap:
            trap_probabilities["reversal"] = reversal_prob
            reasons.append("Volume fail at level (Reversal Trap)")

        liquidity_trap, liquidity_prob = self.detect_liquidity_trap(oi, strike_position)
        if liquidity_trap:
            trap_probabilities["liquidity"] = liquidity_prob
            reasons.append("Low OI at extreme strike (Liquidity Trap)")

        # Determine overall trap status
        is_trap = len(trap_probabilities) > 0

        if is_trap:
            avg_probability = sum(trap_probabilities.values()) / len(trap_probabilities)
        else:
            avg_probability = 0.0

        # Determine primary trap type
        if trap_probabilities:
            trap_type_name = max(trap_probabilities, key=trap_probabilities.get)
            trap_type = {
                "scalper": TrapType.SCALPER_TRAP,
                "noise": TrapType.NOISE_TRAP,
                "theta": TrapType.THETA_CRUSH_TRAP,
                "reversal": TrapType.REVERSAL_TRAP,
                "liquidity": TrapType.SCALPER_TRAP,  # Similar to scalper trap
            }.get(trap_type_name, TrapType.NO_TRAP)
        else:
            trap_type = TrapType.NO_TRAP

        # Should block if multiple traps or high probability
        should_block = len(trap_probabilities) > 1 or avg_probability > 0.75

        return {
            "is_trap": is_trap,
            "trap_type": trap_type,
            "probability": avg_probability,
            "reasons": reasons,
            "should_block": should_block,
            "trap_breakdown": trap_probabilities,
        }

    def reset(self):
        """Reset metrics"""
        self.traps_detected = 0
        self.scalper_traps = 0
        self.noise_traps = 0
        self.theta_traps = 0
        self.reversal_traps = 0
        self.liquidity_traps = 0
        self.validations_count = 0

    def get_metrics(self) -> Dict:
        """Get filter metrics"""

        return {
            "total_validations": self.validations_count,
            "total_traps_detected": self.traps_detected,
            "scalper_traps": self.scalper_traps,
            "noise_traps": self.noise_traps,
            "theta_traps": self.theta_traps,
            "reversal_traps": self.reversal_traps,
            "liquidity_traps": self.liquidity_traps,
            "trap_detection_rate": (self.traps_detected / max(self.validations_count, 1) * 100),
        }
