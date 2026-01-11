"""
PHASE 5 — Trade Eligibility Engine & Direction/Strike Selector

Final decision gate:
1. Check all 5 eligibility criteria (must ALL pass)
2. Select best direction & strike
3. Output execution signal
"""

from typing import Optional, Dict, List, Tuple
from datetime import datetime, time
from src.utils.market_bias_models import (
    BiasType, BiasStrength, TimeWindow, DataHealthStatus,
    TradeEligibilityAnalysis, EligibilityCheckResult,
    DirectionAndStrikeSelection, StrikeSelectionReason,
    DirectionType, Phase5Config,
    is_eligible_bias, is_strong_bias, is_trade_window,
    get_direction_from_bias,
)
import logging

logger = logging.getLogger(__name__)


class TradeEligibilityEngine:
    """
    Final eligibility gate with 5 checks (must ALL pass):
    1. Bias ≠ NEUTRAL
    2. Bias Strength ≥ MEDIUM
    3. Time Window OK
    4. Trap Probability LOW
    5. Data Health GREEN
    """
    
    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        self.last_analysis = None
    
    def check_eligibility(
        self,
        bias_type: BiasType,
        bias_strength: BiasStrength,
        time_window: TimeWindow,
        trap_probability: float,
        data_health: DataHealthStatus,
        data_age_seconds: float,
        time_allowed: bool,
        greeks_safe: bool,
    ) -> TradeEligibilityAnalysis:
        """
        Run all 5 eligibility checks
        
        Returns TradeEligibilityAnalysis with pass/fail status
        """
        
        # Check 1: Bias ≠ NEUTRAL
        bias_check = self._check_bias(bias_type)
        
        # Check 2: Bias Strength ≥ MEDIUM
        strength_check = self._check_strength(bias_strength)
        
        # Check 3: Time Window OK
        time_check = self._check_time(time_window, time_allowed)
        
        # Check 4: Trap Probability LOW
        trap_check = self._check_trap(trap_probability)
        
        # Check 5: Data Health GREEN
        data_check = self._check_data_health(data_health, data_age_seconds)
        
        # All checks must pass
        all_passed = all([
            bias_check.passed,
            strength_check.passed,
            time_check.passed,
            trap_check.passed,
            data_check.passed,
        ])
        
        # Calculate overall eligibility score
        check_scores = [
            bias_check.score,
            strength_check.score,
            time_check.score,
            trap_check.score,
            data_check.score,
        ]
        eligibility_score = sum(check_scores) / len(check_scores)
        
        # Determine block reason if not eligible
        block_reason = None
        if not all_passed:
            block_reasons = []
            if not bias_check.passed:
                block_reasons.append(bias_check.reason)
            if not strength_check.passed:
                block_reasons.append(strength_check.reason)
            if not time_check.passed:
                block_reasons.append(time_check.reason)
            if not trap_check.passed:
                block_reasons.append(trap_check.reason)
            if not data_check.passed:
                block_reasons.append(data_check.reason)
            block_reason = " | ".join(block_reasons)
        
        # Include greeks safety check in reasoning
        if all_passed and not greeks_safe:
            all_passed = False
            block_reason = "Greeks not safe (theta/IV/gamma)"
            eligibility_score *= 0.5
        
        analysis = TradeEligibilityAnalysis(
            bias_check=bias_check,
            strength_check=strength_check,
            time_check=time_check,
            trap_check=trap_check,
            data_health_check=data_check,
            trade_eligible=all_passed,
            eligibility_score=eligibility_score,
            block_reason=block_reason,
            data_health_status=data_health,
            data_age_seconds=data_age_seconds,
            timestamp=datetime.now(),
        )
        
        self.last_analysis = analysis
        return analysis
    
    def _check_bias(self, bias_type: BiasType) -> EligibilityCheckResult:
        """Check 1: Bias ≠ NEUTRAL"""
        passed = is_eligible_bias(bias_type)
        score = 1.0 if passed else 0.0
        reason = (
            "Bias is tradeable"
            if passed
            else "Bias is NEUTRAL (no clear direction)"
        )
        return EligibilityCheckResult("Bias Check", passed, score, reason)
    
    def _check_strength(self, bias_strength: BiasStrength) -> EligibilityCheckResult:
        """Check 2: Bias Strength ≥ MEDIUM"""
        passed = is_strong_bias(bias_strength, self.config.min_bias_strength)
        score = (
            1.0 if bias_strength == BiasStrength.EXTREME
            else 0.75 if bias_strength == BiasStrength.HIGH
            else 0.5 if bias_strength == BiasStrength.MEDIUM
            else 0.0
        )
        reason = (
            f"Bias strength {bias_strength.value} (sufficient)"
            if passed
            else f"Bias strength {bias_strength.value} (too weak)"
        )
        return EligibilityCheckResult("Strength Check", passed, score, reason)
    
    def _check_time(self, time_window: TimeWindow, time_allowed: bool) -> EligibilityCheckResult:
        """Check 3: Time Window OK"""
        passed = time_allowed
        score = (
            1.0 if time_window == TimeWindow.ALLOWED
            else 0.5 if time_window == TimeWindow.CAUTION
            else 0.0
        )
        reason = (
            f"Time window {time_window.value} (ok)"
            if passed
            else f"Time window {time_window.value} (blocked)"
        )
        return EligibilityCheckResult("Time Check", passed, score, reason)
    
    def _check_trap(self, trap_probability: float) -> EligibilityCheckResult:
        """Check 4: Trap Probability LOW"""
        passed = trap_probability <= self.config.max_trap_probability
        score = 1.0 - trap_probability  # Higher trap prob = lower score
        reason = (
            f"Trap probability {trap_probability:.0%} (acceptable)"
            if passed
            else f"Trap probability {trap_probability:.0%} (too high)"
        )
        return EligibilityCheckResult("Trap Check", passed, score, reason)
    
    def _check_data_health(
        self,
        data_health: DataHealthStatus,
        data_age_seconds: float,
    ) -> EligibilityCheckResult:
        """Check 5: Data Health GREEN"""
        
        # Data must be GREEN
        is_green = data_health == DataHealthStatus.GREEN
        
        # Data must be fresh
        is_fresh = data_age_seconds <= self.config.max_data_age_seconds
        
        passed = is_green and is_fresh
        
        score = (
            1.0 if is_green and is_fresh
            else 0.5 if is_green and not is_fresh
            else 0.2 if data_health == DataHealthStatus.YELLOW
            else 0.0
        )
        
        reason = (
            "Data health GREEN and fresh"
            if passed
            else f"Data health {data_health.value}, age {data_age_seconds:.1f}s"
        )
        
        return EligibilityCheckResult("Data Health Check", passed, score, reason)


class DirectionAndStrikeSelector:
    """
    Selects best direction (CALL/PUT) and strike (ATM, ATM+1, ATM-1)
    based on:
    - Highest gamma (gamma support for the bias)
    - Fresh OI (recent position activity)
    - Volume leadership
    """
    
    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
    
    def select_direction_and_strike(
        self,
        bias_type: BiasType,
        atm_strike: float,
        # CE data for ATM, ATM+1
        ce_atm_gamma: float = 0.0,
        ce_atm_fresh_oi: float = 0.0,
        ce_atm_volume: float = 0.0,
        ce_atm_plus1_gamma: Optional[float] = None,
        ce_atm_plus1_fresh_oi: Optional[float] = None,
        ce_atm_plus1_volume: Optional[float] = None,
        # PE data for ATM, ATM-1
        pe_atm_gamma: float = 0.0,
        pe_atm_fresh_oi: float = 0.0,
        pe_atm_volume: float = 0.0,
        pe_atm_minus1_gamma: Optional[float] = None,
        pe_atm_minus1_fresh_oi: Optional[float] = None,
        pe_atm_minus1_volume: Optional[float] = None,
    ) -> DirectionAndStrikeSelection:
        """
        Select best direction and strike for trade
        
        For BULLISH: Choose best CALL (ATM or ATM+1)
        For BEARISH: Choose best PUT (ATM or ATM-1)
        """
        
        if bias_type == BiasType.BULLISH:
            return self._select_call(
                atm_strike,
                ce_atm_gamma, ce_atm_fresh_oi, ce_atm_volume,
                ce_atm_plus1_gamma, ce_atm_plus1_fresh_oi, ce_atm_plus1_volume,
            )
        
        elif bias_type == BiasType.BEARISH:
            return self._select_put(
                atm_strike,
                pe_atm_gamma, pe_atm_fresh_oi, pe_atm_volume,
                pe_atm_minus1_gamma, pe_atm_minus1_fresh_oi, pe_atm_minus1_volume,
            )
        
        else:
            # NEUTRAL - shouldn't happen in practice
            return DirectionAndStrikeSelection(
                direction=DirectionType.NEUTRAL,
                strike_offset=0,
                instrument_name=None,
                reason=StrikeSelectionReason(0, 0, 0, 0.0, 0.0, 0.0, 0.0, "No bias"),
                entry_confidence=0.0,
            )
    
    def _select_call(
        self,
        atm_strike: float,
        ce_atm_gamma: float,
        ce_atm_fresh_oi: float,
        ce_atm_volume: float,
        ce_atm_plus1_gamma: Optional[float] = None,
        ce_atm_plus1_fresh_oi: Optional[float] = None,
        ce_atm_plus1_volume: Optional[float] = None,
    ) -> DirectionAndStrikeSelection:
        """Select best CALL (ATM or ATM+1)"""
        
        # Score ATM
        atm_score = self._calculate_strike_score(
            ce_atm_gamma, ce_atm_fresh_oi, ce_atm_volume
        )
        
        # Score ATM+1
        plus1_score = 0.0
        if ce_atm_plus1_gamma is not None:
            plus1_score = self._calculate_strike_score(
                ce_atm_plus1_gamma, ce_atm_plus1_fresh_oi, ce_atm_plus1_volume
            )
        
        # Choose best
        if plus1_score > atm_score and ce_atm_plus1_gamma is not None:
            strike_offset = 1
            selected_score = plus1_score
            reason = StrikeSelectionReason(
                gamma_rank=1,
                fresh_oi_rank=0 if ce_atm_plus1_fresh_oi > ce_atm_fresh_oi else 1,
                volume_rank=0 if ce_atm_plus1_volume > ce_atm_volume else 1,
                gamma_value=ce_atm_plus1_gamma,
                fresh_oi_strength=ce_atm_plus1_fresh_oi,
                volume_value=ce_atm_plus1_volume,
                weighted_score=plus1_score,
                selection_reason="ATM+1 CALL selected (better gamma/volume)"
            )
        else:
            strike_offset = 0
            selected_score = atm_score
            reason = StrikeSelectionReason(
                gamma_rank=0,
                fresh_oi_rank=0,
                volume_rank=0,
                gamma_value=ce_atm_gamma,
                fresh_oi_strength=ce_atm_fresh_oi,
                volume_value=ce_atm_volume,
                weighted_score=atm_score,
                selection_reason="ATM CALL selected (higher confidence)"
            )
        
        return DirectionAndStrikeSelection(
            direction=DirectionType.CALL,
            strike_offset=strike_offset,
            instrument_name=f"NIFTY2601{int(atm_strike + strike_offset * 100)}CE",
            reason=reason,
            entry_confidence=selected_score,
        )
    
    def _select_put(
        self,
        atm_strike: float,
        pe_atm_gamma: float,
        pe_atm_fresh_oi: float,
        pe_atm_volume: float,
        pe_atm_minus1_gamma: Optional[float] = None,
        pe_atm_minus1_fresh_oi: Optional[float] = None,
        pe_atm_minus1_volume: Optional[float] = None,
    ) -> DirectionAndStrikeSelection:
        """Select best PUT (ATM or ATM-1)"""
        
        # Score ATM
        atm_score = self._calculate_strike_score(
            pe_atm_gamma, pe_atm_fresh_oi, pe_atm_volume
        )
        
        # Score ATM-1
        minus1_score = 0.0
        if pe_atm_minus1_gamma is not None:
            minus1_score = self._calculate_strike_score(
                pe_atm_minus1_gamma, pe_atm_minus1_fresh_oi, pe_atm_minus1_volume
            )
        
        # Choose best
        if minus1_score > atm_score and pe_atm_minus1_gamma is not None:
            strike_offset = -1
            selected_score = minus1_score
            reason = StrikeSelectionReason(
                gamma_rank=1,
                fresh_oi_rank=0 if pe_atm_minus1_fresh_oi > pe_atm_fresh_oi else 1,
                volume_rank=0 if pe_atm_minus1_volume > pe_atm_volume else 1,
                gamma_value=pe_atm_minus1_gamma,
                fresh_oi_strength=pe_atm_minus1_fresh_oi,
                volume_value=pe_atm_minus1_volume,
                weighted_score=minus1_score,
                selection_reason="ATM-1 PUT selected (better gamma/volume)"
            )
        else:
            strike_offset = 0
            selected_score = atm_score
            reason = StrikeSelectionReason(
                gamma_rank=0,
                fresh_oi_rank=0,
                volume_rank=0,
                gamma_value=pe_atm_gamma,
                fresh_oi_strength=pe_atm_fresh_oi,
                volume_value=pe_atm_volume,
                weighted_score=atm_score,
                selection_reason="ATM PUT selected (higher confidence)"
            )
        
        return DirectionAndStrikeSelection(
            direction=DirectionType.PUT,
            strike_offset=strike_offset,
            instrument_name=f"NIFTY2601{int(atm_strike + strike_offset * 100)}PE",
            reason=reason,
            entry_confidence=selected_score,
        )
    
    def _calculate_strike_score(
        self,
        gamma: float,
        fresh_oi: float,
        volume: float,
    ) -> float:
        """
        Calculate strike selection score
        
        Weighted combination of:
        - Highest Gamma (responsiveness)
        - Fresh OI (new positions)
        - Volume (liquidity & interest)
        """
        
        # Normalize gamma (cap at reasonable range)
        gamma_norm = min(gamma / 0.03, 1.0)  # Normalize to 0-1
        
        # Normalize fresh OI strength (0-1)
        fresh_oi_norm = min(fresh_oi, 1.0)
        
        # Normalize volume (cap at 1000+)
        volume_norm = min(volume / 1000, 1.0)
        
        # Weighted score
        score = (
            (gamma_norm * 0.5) +      # Gamma is most important
            (fresh_oi_norm * 0.3) +   # Fresh positions
            (volume_norm * 0.2)       # Volume support
        )
        
        return min(max(score, 0.0), 1.0)
