"""
PHASE 3 — Greeks + OI Sync Validator (Fake Move Detection)
Detects: Fake moves, Smart money activity, Theta traps

Rules:
    • Delta ↑ + OI ↑ = Smart money (QUALITY signal)
    • Delta ↑ + OI ↓ = Fake move (DANGER)
    • Gamma ↑ + OI ↑ = Acceleration potential (BULLISH)
    • Theta ↑ aggressively = Trap zone (AVOID)
"""

import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

from .greeks_models import (
    GreeksSnapshot, OptionType, GreeksOiSyncResult
)
from .option_chain_data_models import StrikeData

logger = logging.getLogger(__name__)


class GreeksOiSyncValidator:
    """
    Validate Greeks against OI data
    Detects fake moves, smart money, theta traps
    
    Used for: Filtering out dangerous/fake trading setups
    """
    
    def __init__(
        self,
        oi_change_threshold: float = 0.05,      # 5% OI change threshold
        delta_oi_sync_weight: float = 0.7,      # 70% weight for delta-oi alignment
        fake_move_confidence: float = 0.8       # 80%+ confidence to flag fake
    ):
        """Initialize sync validator"""
        self.oi_change_threshold = oi_change_threshold
        self.delta_oi_sync_weight = delta_oi_sync_weight
        self.fake_move_confidence = fake_move_confidence
        
        # Tracking
        self.total_validations = 0
        self.fake_moves_detected = 0
        self.smart_money_signals = 0
        self.theta_exits = 0
        
        logger.info(
            f"Greeks-OI Sync Validator initialized "
            f"(oi_threshold={oi_change_threshold*100:.1f}%)"
        )
    
    def validate_strike_sync(
        self,
        current_greek: GreeksSnapshot,
        previous_greek: Optional[GreeksSnapshot],
        current_oi_data: StrikeData,
        previous_oi_data: Optional[StrikeData]
    ) -> GreeksOiSyncResult:
        """
        Validate single strike Greeks + OI alignment
        
        Returns: GreeksOiSyncResult with findings
        """
        result = GreeksOiSyncResult(timestamp=datetime.now())
        self.total_validations += 1
        
        if not previous_oi_data or previous_greek is None:
            # First snapshot, no previous data to compare
            result.recommendation = "NEUTRAL"
            return result
        
        # -------- Calculate Directions --------
        delta_direction = self._get_direction_change(
            current_greek.delta,
            previous_greek.delta
        )
        
        oi_direction = self._get_direction_change(
            current_oi_data.oi,
            previous_oi_data.oi
        )
        
        result.delta_direction = delta_direction
        result.oi_direction = oi_direction
        
        # -------- Rule 1: Delta ↑ + OI ↑ = Smart Money (QUALITY) --------
        if delta_direction == "UP" and oi_direction == "UP":
            result.smart_money_signal = True
            result.recommendation = "PROCEED"
            result.quality_score = 0.9
            self.smart_money_signals += 1
            logger.info(f"Smart money signal detected at strike {current_greek.strike}")
        
        # -------- Rule 2: Delta ↑ + OI ↓ = Fake Move (DANGER) --------
        elif delta_direction == "UP" and oi_direction == "DOWN":
            result.fake_move_detected = True
            result.recommendation = "AVOID"
            result.quality_score = 0.1
            self.fake_moves_detected += 1
            logger.warning(
                f"FAKE MOVE DETECTED at strike {current_greek.strike}: "
                f"Delta ↑ but OI ↓"
            )
        
        # -------- Rule 3: Delta ↓ + OI ↑ = Reversal Setup --------
        elif delta_direction == "DOWN" and oi_direction == "UP":
            result.recommendation = "CAUTION"
            result.quality_score = 0.4
            logger.info(f"Reversal setup at strike {current_greek.strike}")
        
        # -------- Rule 4: Gamma ↑ + OI ↑ = Acceleration Potential --------
        gamma_expanded = (current_greek.gamma_expansion or 0) > 0.001
        if gamma_expanded and oi_direction == "UP":
            result.recommendation = "PROCEED"
            result.quality_score = max(result.quality_score, 0.8)
            logger.debug(f"Gamma expansion + OI growth at strike {current_greek.strike}")
        
        # -------- Rule 5: Theta ↑ Aggressively = Trap Zone (EXIT) --------
        theta_spiked = (current_greek.theta_spike or 0) < -0.05  # More negative
        if theta_spiked:
            result.theta_exit_signal = True
            if result.recommendation != "AVOID":
                result.recommendation = "CAUTION"
            logger.warning(
                f"Theta spike detected at strike {current_greek.strike}: "
                f"Θ={current_greek.theta:.4f}"
            )
            self.theta_exits += 1
        
        # -------- Default alignment score --------
        if not result.fake_move_detected and not result.smart_money_signal:
            # Check if at least not contradicting
            if (delta_direction == "UP" and oi_direction != "DOWN") or \
               (delta_direction == "DOWN" and oi_direction != "UP"):
                result.quality_score = 0.6
                result.delta_oi_aligned = True
            else:
                result.quality_score = 0.3
                result.delta_oi_aligned = False
        
        logger.debug(
            f"Strike {current_greek.strike} sync check: "
            f"quality={result.quality_score:.2f}, "
            f"recommendation={result.recommendation}"
        )
        
        return result
    
    def validate_chain_sync(
        self,
        current_greeks: Dict[float, GreeksSnapshot],
        previous_greeks: Dict[float, GreeksSnapshot],
        current_oi_data: Dict[float, StrikeData],
        previous_oi_data: Dict[float, StrikeData]
    ) -> Dict:
        """
        Validate entire chain Greeks + OI alignment
        Aggregate view of fake moves, smart money, etc.
        
        Returns:
            {
                "overall_alignment": 0-1,
                "fake_move_count": int,
                "smart_money_count": int,
                "theta_danger_count": int,
                "recommendation": "PROCEED" | "CAUTION" | "AVOID" | "NEUTRAL",
                "details": [list of result objects]
            }
        """
        fake_count = 0
        smart_money_count = 0
        theta_danger_count = 0
        quality_scores = []
        details = []
        
        for strike, current_greek in current_greeks.items():
            previous_greek = previous_greeks.get(strike)
            current_oi = current_oi_data.get(strike)
            previous_oi = previous_oi_data.get(strike)
            
            if current_oi is None:
                continue
            
            result = self.validate_strike_sync(
                current_greek,
                previous_greek,
                current_oi,
                previous_oi
            )
            details.append(result)
            quality_scores.append(result.quality_score)
            
            if result.fake_move_detected:
                fake_count += 1
            if result.smart_money_signal:
                smart_money_count += 1
            if result.theta_exit_signal:
                theta_danger_count += 1
        
        # Aggregate recommendation
        overall_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0.5
        
        if fake_count > len(current_greeks) * 0.3:  # >30% strikes are fake
            recommendation = "AVOID"
        elif smart_money_count > len(current_greeks) * 0.4:  # >40% are smart money
            recommendation = "PROCEED"
        elif theta_danger_count > len(current_greeks) * 0.2:  # >20% danger zones
            recommendation = "CAUTION"
        else:
            recommendation = "NEUTRAL"
        
        result_dict = {
            "overall_alignment": overall_quality,
            "fake_move_count": fake_count,
            "smart_money_count": smart_money_count,
            "theta_danger_count": theta_danger_count,
            "recommendation": recommendation,
            "details": details,
            "timestamp": datetime.now()
        }
        
        logger.info(
            f"Chain sync validation: quality={overall_quality:.2f}, "
            f"fake={fake_count}, smart={smart_money_count}, "
            f"theta_danger={theta_danger_count}, rec={recommendation}"
        )
        
        return result_dict
    
    @staticmethod
    def _get_direction_change(current: float, previous: float) -> Optional[str]:
        """Determine if value moved UP, DOWN, or stayed FLAT"""
        threshold = 0.001  # 0.1% change threshold
        pct_change = (current - previous) / max(abs(previous), 0.01)
        
        if pct_change > threshold:
            return "UP"
        elif pct_change < -threshold:
            return "DOWN"
        else:
            return "FLAT"
    
    def get_metrics(self) -> Dict:
        """Return validation metrics"""
        return {
            "total_validations": self.total_validations,
            "fake_moves_detected": self.fake_moves_detected,
            "smart_money_signals": self.smart_money_signals,
            "theta_exits": self.theta_exits,
            "fake_move_ratio": (
                self.fake_moves_detected / max(self.total_validations, 1)
            ),
            "smart_money_ratio": (
                self.smart_money_signals / max(self.total_validations, 1)
            )
        }
