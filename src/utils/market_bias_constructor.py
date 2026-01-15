"""
PHASE 5 — Market Bias Constructor

Detects 3-state market bias:
- BULLISH: ATM CE dominance + supportive Delta/Gamma + bullish OI/Volume
- BEARISH: ATM PE dominance + supportive Delta/Gamma + bearish OI/Volume
- NEUTRAL: Mixed signals or low conviction (NO-TRADE mode)
"""

from typing import Dict, Tuple, Optional
from src.utils.market_bias_models import (
    BiasType,
    BiasStrength,
    BiasAnalysis,
    StrengthAnalysisDetails,
    Phase5Config,
    validate_bias_type,
    is_strong_bias,
)
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MarketBiasConstructor:
    """
    Constructs market bias from:
    - ATM CE vs PE dominance
    - Delta alignment
    - Gamma support
    - OI + Volume patterns from Phase 4
    """

    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        self.bias_history = []  # Track last 10 biases
        self.max_history = 10

    def detect_bias(
        self,
        ce_dominance: float,  # [0-1] (0=PE, 1=CE)
        delta_ce: float,  # CE delta value
        delta_pe: float,  # PE delta value
        gamma_ce: float,  # CE gamma value
        gamma_pe: float,  # PE gamma value
        oi_conviction: float,  # [0-1] from Phase 4
        volume_aggression: float,  # [0-1] from Phase 4
        primary_buildup: Optional[str] = None,  # From Phase 4 OI classifier
    ) -> BiasAnalysis:
        """
        Detect market bias from market indicators

        Returns BiasAnalysis with bias_type, strength, and reasoning
        """

        # Step 1: Determine primary bias direction
        bias_type, direction_confidence = self._determine_bias_direction(
            ce_dominance, delta_ce, delta_pe, primary_buildup
        )

        # Step 2: Check gamma support
        gamma_support = self._analyze_gamma_support(bias_type, gamma_ce, gamma_pe)

        # Step 3: Check delta alignment
        delta_alignment = self._analyze_delta_alignment(bias_type, delta_ce, delta_pe)

        # Step 4: Calculate conviction score
        conviction_score = self._calculate_conviction_score(
            direction_confidence=direction_confidence,
            delta_alignment=delta_alignment,
            gamma_support=gamma_support,
            oi_conviction=oi_conviction,
            volume_aggression=volume_aggression,
        )

        # Step 5: Determine strength
        # Force LOW strength for NEUTRAL bias (capital protection)
        if bias_type == BiasType.NEUTRAL:
            bias_strength = BiasStrength.LOW
        else:
            bias_strength = self._get_strength_from_conviction(conviction_score)

        # Step 6: Generate reasoning
        reasoning = self._generate_reasoning(bias_type, bias_strength, ce_dominance, gamma_support, delta_alignment)

        # Create analysis object
        analysis = BiasAnalysis(
            bias_type=bias_type,
            bias_strength=bias_strength,
            conviction_score=conviction_score,
            ce_dominance=ce_dominance,
            delta_alignment=delta_alignment,
            gamma_support=gamma_support,
            oi_conviction=oi_conviction,
            volume_aggression=volume_aggression,
            reasoning=reasoning,
            confidence_level=bias_strength.value,
            timestamp=datetime.now(),
        )

        # Store in history
        self._update_history(analysis)

        return analysis

    def _determine_bias_direction(
        self,
        ce_dominance: float,
        delta_ce: float,
        delta_pe: float,
        primary_buildup: Optional[str],
    ) -> Tuple[BiasType, float]:
        """
        Determine bias direction based on:
        - CE dominance (>0.55 = bullish, <0.45 = bearish)
        - Delta signs
        - OI buildup type
        """

        # CE dominance signal
        ce_dominance_score = 0.0
        if ce_dominance > 0.55:
            ce_dominance_score = (ce_dominance - 0.55) / 0.45  # 0-1
        elif ce_dominance < 0.45:
            ce_dominance_score = (0.45 - ce_dominance) / 0.45  # 0 to -1

        # Delta signal
        delta_score = 0.0
        if delta_ce > abs(delta_pe):  # CE delta dominates
            delta_score = min(delta_ce, 1.0)
        elif delta_pe < -abs(delta_ce):  # PE delta dominates (negative)
            delta_score = max(delta_pe, -1.0)

        # Combine signals
        combined_score = (ce_dominance_score * 0.6) + (delta_score * 0.4)

        # Determine bias
        if combined_score > 0.1:  # Bullish signal threshold
            bias_type = BiasType.BULLISH
            direction_confidence = min(abs(combined_score), 1.0)
        elif combined_score < -0.1:  # Bearish signal threshold
            bias_type = BiasType.BEARISH
            direction_confidence = min(abs(combined_score), 1.0)
        else:  # Mixed/Neutral
            bias_type = BiasType.NEUTRAL
            direction_confidence = 0.3

        return bias_type, direction_confidence

    def _analyze_gamma_support(
        self,
        bias_type: BiasType,
        gamma_ce: float,
        gamma_pe: float,
    ) -> float:
        """Check if gamma supports the bias direction"""

        if bias_type == BiasType.BULLISH:
            # Bullish: CE gamma should be higher (more responsive upside)
            if gamma_ce > gamma_pe:
                return min(gamma_ce / (gamma_ce + gamma_pe + 0.0001), 1.0)
            else:
                return 0.0  # Gamma doesn't support

        elif bias_type == BiasType.BEARISH:
            # Bearish: PE gamma should be higher (more responsive downside)
            if gamma_pe > gamma_ce:
                return min(gamma_pe / (gamma_ce + gamma_pe + 0.0001), 1.0)
            else:
                return 0.0  # Gamma doesn't support

        else:  # NEUTRAL
            # For neutral, gamma balance (close to 50/50) is good
            total = gamma_ce + gamma_pe
            if total > 0:
                ce_pct = gamma_ce / total
                return 1.0 - abs(ce_pct - 0.5) * 2  # Closer to 50/50 = higher score
            return 0.5

    def _analyze_delta_alignment(
        self,
        bias_type: BiasType,
        delta_ce: float,
        delta_pe: float,
    ) -> float:
        """Check if delta aligns with the bias direction"""

        if bias_type == BiasType.BULLISH:
            # Bullish: CE delta should be increasing (positive and higher)
            # PE delta should be declining (less negative)
            ce_alignment = min(abs(delta_ce), 1.0)  # 0 to 1
            pe_alignment = 1.0 - min(abs(delta_pe), 1.0)  # Penalize negative
            return (ce_alignment + pe_alignment) / 2

        elif bias_type == BiasType.BEARISH:
            # Bearish: PE delta should be decreasing (more negative)
            # CE delta should be declining (less positive)
            pe_alignment = min(abs(delta_pe), 1.0)  # 0 to 1
            ce_alignment = 1.0 - min(abs(delta_ce), 1.0)  # Penalize positive
            return (pe_alignment + ce_alignment) / 2

        else:  # NEUTRAL
            # For neutral, delta should be balanced
            delta_diff = abs(delta_ce + delta_pe)  # Should be close to 0
            return max(0.0, 1.0 - delta_diff)

    def _calculate_conviction_score(
        self,
        direction_confidence: float,  # [0-1]
        delta_alignment: float,  # [0-1]
        gamma_support: float,  # [0-1]
        oi_conviction: float,  # [0-1]
        volume_aggression: float,  # [0-1]
    ) -> float:
        """Calculate combined conviction score"""

        # Weighted average of all factors
        conviction = (
            (direction_confidence * 0.2)
            + (delta_alignment * 0.2)
            + (gamma_support * 0.15)
            + (oi_conviction * self.config.oi_conviction_weight)
            + (volume_aggression * self.config.volume_aggression_weight)
        )

        return min(max(conviction, 0.0), 1.0)

    def _get_strength_from_conviction(self, conviction_score: float) -> BiasStrength:
        """Convert conviction score to strength level"""

        if conviction_score >= self.config.bias_high_threshold:
            return BiasStrength.EXTREME
        elif conviction_score >= self.config.bias_medium_threshold:
            return BiasStrength.HIGH
        elif conviction_score >= self.config.bias_low_threshold:
            return BiasStrength.MEDIUM
        else:
            return BiasStrength.LOW

    def _generate_reasoning(
        self,
        bias_type: BiasType,
        strength: BiasStrength,
        ce_dominance: float,
        gamma_support: float,
        delta_alignment: float,
    ) -> str:
        """Generate human-readable reasoning for the bias"""

        if bias_type == BiasType.BULLISH:
            direction_text = "BULLISH"
        elif bias_type == BiasType.BEARISH:
            direction_text = "BEARISH"
        else:
            direction_text = "NEUTRAL"

        factors = []

        if ce_dominance > 0.55:
            factors.append(f"CE dominance {ce_dominance:.0%}")
        elif ce_dominance < 0.45:
            factors.append(f"PE dominance {1-ce_dominance:.0%}")

        if gamma_support > 0.6:
            factors.append(f"Gamma supportive ({gamma_support:.0%})")

        if delta_alignment > 0.6:
            factors.append(f"Delta aligned ({delta_alignment:.0%})")

        factors_text = " | ".join(factors) if factors else "Mixed signals"

        return f"{direction_text} ({strength.value}): {factors_text}"

    def _update_history(self, analysis: BiasAnalysis):
        """Store bias in history (keep last N)"""
        self.bias_history.append(analysis)
        if len(self.bias_history) > self.max_history:
            self.bias_history.pop(0)

    def get_bias_trend(self) -> str:
        """
        Analyze bias consistency over last few updates

        Returns: "consistent" | "changing" | "unstable"
        """
        if len(self.bias_history) < 3:
            return "insufficient_data"

        recent = self.bias_history[-3:]
        bias_types = [b.bias_type for b in recent]

        # All same = consistent
        if all(b == bias_types[0] for b in bias_types):
            return "consistent"

        # 2 out of 3 same = changing
        if bias_types.count(BiasType.BULLISH) >= 2 or bias_types.count(BiasType.BEARISH) >= 2:
            return "changing"

        # All different = unstable
        return "unstable"

    def get_primary_bias(self) -> BiasType:
        """Get most recent bias type"""
        if self.bias_history:
            return self.bias_history[-1].bias_type
        return BiasType.UNKNOWN

    def get_bias_strength_trend(self) -> str:
        """
        Check if bias strength is improving or degrading

        Returns: "strengthening" | "weakening" | "stable"
        """
        if len(self.bias_history) < 2:
            return "insufficient_data"

        prev_strength = self.bias_history[-2].conviction_score
        curr_strength = self.bias_history[-1].conviction_score

        diff = curr_strength - prev_strength

        if diff > 0.05:
            return "strengthening"
        elif diff < -0.05:
            return "weakening"
        else:
            return "stable"
