"""
PHASE 4 — OI + GREEKS CROSS-VALIDATOR
Truth Table & Alignment Detection

Validate OI + Volume signals against Phase 3 Greeks signals:

Smart Entry: Delta ↑ + OI ↑ + Volume ↑ ⇒ PROCEED
Trap: Delta ↑ + Volume ↑ + OI ↓ ⇒ BLOCK (Fake Move)
Explosive: Gamma ↑ + Fresh OI ⇒ High conviction
Theta Trap: Theta ↑ aggressive ⇒ EXIT signal

Greeks ≠ OI alignment → BLOCK TRADE

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from typing import Dict, Optional, Tuple
from datetime import datetime

from .smart_money_models import (
    SmartMoneyConfig,
)


logger = logging.getLogger(__name__)


class OiGreeksCrossValidator:
    """
    Cross-validate OI + Volume signals against Greeks signals

    Truth Table:
    1. Δ ↑ + OI ↑ + Volume ↑ → Smart Entry (quality 0.95)
    2. Δ ↑ + OI ↓ + Volume ↑ → Trap (quality 0.05)
    3. Δ ↓ + OI ↑ + Volume ↑ → Reversal (quality 0.4)
    4. Γ ↑ + Fresh OI → Explosive (quality 0.9)
    5. Θ ↑ aggressively → Theta Trap (quality 0.1, EXIT)

    Rule: If Greeks ≠ OI, trade is BLOCKED
    """

    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize validator"""
        self.config = config or SmartMoneyConfig()

        # Metrics
        self.validations_count = 0
        self.aligned_signals = 0
        self.misaligned_signals = 0
        self.smart_entries = 0
        self.traps_detected = 0
        self.explosive_moves = 0
        self.theta_traps = 0

    def validate_strike_alignment(
        self,
        strike: float,
        delta: float,
        gamma: float,
        theta: float,
        vega: float,
        oi_change: float,  # -1 to 1
        volume_change: float,  # as ratio
        previous_delta: Optional[float] = None,
        previous_gamma: Optional[float] = None,
        previous_theta: Optional[float] = None,
    ) -> Dict:
        """
        Validate single strike for alignment

        Returns: {
            "aligned": bool,
            "quality": 0-1 (higher = more reliable),
            "signal_type": "smart_entry" | "trap" | "reversal" | "explosive" | "theta_trap" | "neutral",
            "explanation": string,
            "can_trade": bool,
            "conviction": 0-1,
        }
        """

        self.validations_count += 1

        # Detect direction changes
        delta_up = previous_delta is not None and delta > previous_delta
        gamma_up = previous_gamma is not None and gamma > previous_gamma
        theta_up = previous_theta is not None and theta > previous_theta

        # OI direction
        oi_up = oi_change > 0.05
        oi_down = oi_change < -0.05

        # Volume direction
        volume_up = volume_change > 1.5

        # Apply truth table
        # Rule 1: Δ ↑ + OI ↑ + Volume ↑ → Smart Entry
        if delta_up and oi_up and volume_up:
            self.smart_entries += 1
            self.aligned_signals += 1
            return {
                "aligned": True,
                "quality": 0.95,
                "signal_type": "smart_entry",
                "explanation": "Δ↑ OI↑ Vol↑ - Smart money entering with conviction",
                "can_trade": True,
                "conviction": 0.95,
            }

        # Rule 2: Δ ↑ + OI ↓ + Volume ↑ → Trap (BLOCK)
        if delta_up and oi_down and volume_up:
            self.traps_detected += 1
            self.misaligned_signals += 1
            return {
                "aligned": False,
                "quality": 0.05,
                "signal_type": "trap",
                "explanation": "Δ↑ OI↓ Vol↑ - TRAP: Price up but positions unwinding",
                "can_trade": False,
                "conviction": 0.85,
            }

        # Rule 3: Δ ↓ + OI ↑ + Volume ↑ → Reversal
        if not delta_up and oi_up and volume_up:
            self.aligned_signals += 1
            return {
                "aligned": True,
                "quality": 0.4,
                "signal_type": "reversal",
                "explanation": "Δ↓ OI↑ Vol↑ - Reversal move with conviction",
                "can_trade": True,
                "conviction": 0.6,
            }

        # Rule 4: Γ ↑ + Fresh OI → Explosive
        if gamma_up and oi_up:
            self.explosive_moves += 1
            self.aligned_signals += 1
            return {
                "aligned": True,
                "quality": 0.9,
                "signal_type": "explosive",
                "explanation": "Γ↑ Fresh OI - Potential explosive move forming",
                "can_trade": True,
                "conviction": 0.9,
            }

        # Rule 5: Θ ↑ aggressively → Theta Trap (EXIT)
        if theta_up and abs(theta) > 0.5:
            self.theta_traps += 1
            self.misaligned_signals += 1
            return {
                "aligned": False,
                "quality": 0.1,
                "signal_type": "theta_trap",
                "explanation": "Θ↑ aggressive decay - THETA TRAP, avoid or exit",
                "can_trade": False,
                "conviction": 0.8,
            }

        # Neutral / insufficient signal
        self.aligned_signals += 1
        return {
            "aligned": True,
            "quality": 0.5,
            "signal_type": "neutral",
            "explanation": "Mixed or unclear signals",
            "can_trade": False,
            "conviction": 0.3,
        }

    def validate_chain_alignment(
        self,
        strikes_validation: Dict[float, Dict],  # {strike: validation_result, ...}
    ) -> Dict:
        """
        Validate entire chain for Greeks-OI alignment

        Returns: {
            "overall_aligned": bool,
            "alignment_score": 0-1,
            "tradeable": bool,
            "dominant_signal": string,
            "trap_count": int,
            "smart_entry_count": int,
            "confidence": 0-1,
            "warnings": list,
        }
        """

        if not strikes_validation:
            return {
                "overall_aligned": False,
                "alignment_score": 0.0,
                "tradeable": False,
                "dominant_signal": "no_data",
                "trap_count": 0,
                "smart_entry_count": 0,
                "confidence": 0.0,
                "warnings": ["No validation data provided"],
            }

        # Aggregate results
        aligned_count = sum(1 for v in strikes_validation.values() if v.get("aligned", False))
        trap_count = sum(1 for v in strikes_validation.values() if v.get("signal_type") == "trap")
        smart_entry_count = sum(1 for v in strikes_validation.values() if v.get("signal_type") == "smart_entry")

        # Calculate overall alignment
        total = len(strikes_validation)
        alignment_score = aligned_count / max(total, 1)

        # Determine if chain is tradeable
        warnings = []

        if trap_count > total * 0.3:
            warnings.append(f"High trap probability ({trap_count}/{total} strikes)")
            tradeable = False
        else:
            tradeable = aligned_count / total > self.config.greeks_oi_alignment_threshold

        # Find dominant signal
        signal_types = {}
        for v in strikes_validation.values():
            signal = v.get("signal_type", "neutral")
            signal_types[signal] = signal_types.get(signal, 0) + 1

        if signal_types:
            dominant_signal = max(signal_types, key=signal_types.get)
        else:
            dominant_signal = "neutral"

        # Overall confidence
        quality_sum = sum(v.get("quality", 0.5) for v in strikes_validation.values())
        confidence = quality_sum / max(total, 1)

        return {
            "overall_aligned": alignment_score > 0.7,
            "alignment_score": alignment_score,
            "tradeable": tradeable,
            "dominant_signal": dominant_signal,
            "trap_count": trap_count,
            "smart_entry_count": smart_entry_count,
            "confidence": confidence,
            "warnings": warnings,
            "signal_distribution": signal_types,
        }

    def is_trade_blockable(
        self,
        validation_result: Dict,
    ) -> bool:
        """
        Determine if trade should be blocked based on validation

        Blocks if:
        - Trap detected (OI ↓ with price ↑)
        - Theta aggressive
        - Overall alignment < 50%
        """

        if not validation_result.get("can_trade", True):
            return True

        if validation_result.get("signal_type") in ["trap", "theta_trap"]:
            return True

        return False

    def get_cross_validation_confidence(
        self,
        greeks_signal_strength: float,  # 0-1 from Greeks engine
        oi_signal_strength: float,  # 0-1 from OI classifier
        volume_signal_strength: float,  # 0-1 from volume detector
    ) -> float:
        """
        Combined confidence when all three signals agree

        Returns: 0-1
        Penalizes disagreement between signals
        """

        # If all signals strong → high confidence
        if greeks_signal_strength > 0.7 and oi_signal_strength > 0.7 and volume_signal_strength > 0.7:
            return 0.95

        # If two strong, one weak → moderate confidence
        strong_count = sum(1 for s in [greeks_signal_strength, oi_signal_strength, volume_signal_strength] if s > 0.6)

        if strong_count == 2:
            return 0.7

        # If only one strong → low confidence
        if strong_count == 1:
            return 0.4

        # If all weak → very low
        return 0.2

    def detect_alignment_divergence(
        self,
        greeks_direction: str,  # "BULL" | "BEAR" | "NEUTRAL"
        oi_direction: str,  # "BULL" | "BEAR" | "NEUTRAL"
        volume_direction: str,  # "BULL" | "BEAR" | "NEUTRAL"
    ) -> Dict:
        """
        Detect if Greeks, OI, Volume are pointing same direction

        Returns: {
            "aligned": bool,
            "divergence_type": "none" | "partial" | "full",
            "explanation": string,
        }
        """

        directions = [greeks_direction, oi_direction, volume_direction]

        # Check if all same
        if directions[0] == directions[1] == directions[2]:
            return {
                "aligned": True,
                "divergence_type": "none",
                "explanation": f"All aligned: {directions[0]}",
            }

        # Check if 2 out of 3 same
        if directions[0] == directions[1] or directions[1] == directions[2] or directions[0] == directions[2]:
            return {
                "aligned": True,
                "divergence_type": "partial",
                "explanation": f"Partial alignment: Greeks={greeks_direction}, "
                f"OI={oi_direction}, Vol={volume_direction}",
            }

        # All different
        return {
            "aligned": False,
            "divergence_type": "full",
            "explanation": f"Full divergence: Greeks={greeks_direction}, " f"OI={oi_direction}, Vol={volume_direction}",
        }

    def reset(self):
        """Reset metrics"""
        self.validations_count = 0
        self.aligned_signals = 0
        self.misaligned_signals = 0
        self.smart_entries = 0
        self.traps_detected = 0
        self.explosive_moves = 0
        self.theta_traps = 0

    def get_metrics(self) -> Dict:
        """Get validator metrics"""
        total = self.validations_count

        return {
            "total_validations": total,
            "aligned_signals": self.aligned_signals,
            "misaligned_signals": self.misaligned_signals,
            "alignment_rate": (self.aligned_signals / max(total, 1) * 100),
            "smart_entries": self.smart_entries,
            "traps_detected": self.traps_detected,
            "explosive_moves": self.explosive_moves,
            "theta_traps": self.theta_traps,
            "trap_rate": (self.traps_detected / max(total, 1) * 100),
        }
