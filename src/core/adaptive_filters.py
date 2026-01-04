"""
PHASE 8: Adaptive Signal Filters
Dynamic noise reduction based on market conditions
Less trades, higher accuracy
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, time as dt_time
import math


@dataclass
class MarketCondition:
    """Current market state assessment"""
    volatility_regime: str  # LOW, MEDIUM, HIGH, EXTREME
    time_of_day: str  # OPENING, MID_MORNING, NOON, AFTERNOON, CLOSING
    trend_strength: float  # 0-1
    noise_level: float  # 0-1
    

class VolatilityRegimeDetector:
    """
    Detect current volatility regime
    Adjust filters based on market conditions
    """
    
    def __init__(self):
        self.volatility_history: List[float] = []
        self.max_history = 20
    
    def update_volatility(self, current_iv: float):
        """Track IV changes"""
        self.volatility_history.append(current_iv)
        if len(self.volatility_history) > self.max_history:
            self.volatility_history.pop(0)
    
    def get_regime(self) -> str:
        """Classify volatility regime"""
        if len(self.volatility_history) < 5:
            return "MEDIUM"
        
        avg_iv = sum(self.volatility_history) / len(self.volatility_history)
        recent_iv = self.volatility_history[-1]
        
        # Calculate IV percentile
        sorted_iv = sorted(self.volatility_history)
        percentile = sorted_iv.index(recent_iv) / len(sorted_iv)
        
        if percentile < 0.25:
            return "LOW"
        elif percentile < 0.5:
            return "MEDIUM"
        elif percentile < 0.75:
            return "HIGH"
        else:
            return "EXTREME"
    
    def get_iv_change_rate(self) -> float:
        """How fast is IV changing"""
        if len(self.volatility_history) < 2:
            return 0.0
        
        recent = self.volatility_history[-5:]
        if len(recent) < 2:
            return 0.0
        
        changes = [abs(recent[i] - recent[i-1]) for i in range(1, len(recent))]
        return sum(changes) / len(changes)


class TimeOfDayAnalyzer:
    """
    Analyze time-of-day patterns
    Different filters for different times
    """
    
    @staticmethod
    def get_time_window() -> str:
        """Get current time window"""
        now = datetime.now().time()
        
        # Market hours: 9:15 - 15:30
        opening = dt_time(9, 15)
        mid_morning = dt_time(10, 30)
        noon = dt_time(12, 0)
        afternoon = dt_time(14, 0)
        closing = dt_time(15, 15)
        
        if now < mid_morning:
            return "OPENING"  # 9:15 - 10:30
        elif now < noon:
            return "MID_MORNING"  # 10:30 - 12:00
        elif now < afternoon:
            return "NOON"  # 12:00 - 14:00
        elif now < closing:
            return "AFTERNOON"  # 14:00 - 15:15
        else:
            return "CLOSING"  # 15:15 - 15:30
    
    @staticmethod
    def get_strictness_multiplier(time_window: str) -> float:
        """
        How strict should filters be
        1.0 = normal, >1.0 = stricter, <1.0 = looser
        """
        multipliers = {
            "OPENING": 1.3,  # Stricter - high volatility, false moves
            "MID_MORNING": 1.0,  # Normal
            "NOON": 0.8,  # Slightly loose - good trends
            "AFTERNOON": 1.1,  # Slightly strict - momentum fades
            "CLOSING": 1.5  # Very strict - erratic moves
        }
        return multipliers.get(time_window, 1.0)


class BiasStrengthFilter:
    """
    Adaptive bias threshold based on conditions
    Strong bias required in high volatility
    """
    
    def __init__(self, base_threshold: float = 0.6):
        self.base_threshold = base_threshold
    
    def get_required_strength(self, market_condition: MarketCondition) -> float:
        """
        Calculate required bias strength for current conditions
        Returns threshold (0-1)
        """
        threshold = self.base_threshold
        
        # Adjust for volatility regime
        vol_adjustments = {
            "LOW": -0.1,  # Easier to trade
            "MEDIUM": 0.0,
            "HIGH": 0.1,  # Need stronger signal
            "EXTREME": 0.2  # Much stronger signal needed
        }
        threshold += vol_adjustments.get(market_condition.volatility_regime, 0.0)
        
        # Adjust for time of day
        time_multiplier = TimeOfDayAnalyzer.get_strictness_multiplier(market_condition.time_of_day)
        threshold *= time_multiplier
        
        # Adjust for noise level
        if market_condition.noise_level > 0.7:
            threshold += 0.15  # High noise = need stronger signal
        
        # Cap between reasonable limits
        return max(0.4, min(0.9, threshold))
    
    def passes_filter(self, bias_strength: float, market_condition: MarketCondition) -> bool:
        """Check if bias is strong enough"""
        required = self.get_required_strength(market_condition)
        return bias_strength >= required


class TrapProbabilityFilter:
    """
    Auto-tighten trap detection in risky conditions
    Avoid bull/bear trap losses
    """
    
    def __init__(self, base_threshold: float = 0.65):
        self.base_threshold = base_threshold
    
    def get_required_confidence(self, market_condition: MarketCondition) -> float:
        """Required confidence that it's NOT a trap"""
        confidence = self.base_threshold
        
        # Higher volatility = more traps
        if market_condition.volatility_regime == "HIGH":
            confidence += 0.1
        elif market_condition.volatility_regime == "EXTREME":
            confidence += 0.2
        
        # Opening/closing = more traps
        if market_condition.time_of_day in ["OPENING", "CLOSING"]:
            confidence += 0.15
        
        return min(0.95, confidence)
    
    def is_likely_trap(self, trap_probability: float, market_condition: MarketCondition) -> bool:
        """Check if setup looks like a trap"""
        required_confidence = self.get_required_confidence(market_condition)
        # If trap probability is high, we need high confidence it's NOT a trap
        return trap_probability > (1.0 - required_confidence)


class OIConfirmationFilter:
    """
    Require stronger OI confirmation in uncertain conditions
    """
    
    def __init__(self, base_min_delta: float = 1000):
        self.base_min_delta = base_min_delta
    
    def get_required_oi_delta(self, market_condition: MarketCondition) -> float:
        """How much OI change is needed"""
        required = self.base_min_delta
        
        # High volatility = need more confirmation
        if market_condition.volatility_regime == "HIGH":
            required *= 1.5
        elif market_condition.volatility_regime == "EXTREME":
            required *= 2.0
        
        # Weak trend = need more confirmation
        if market_condition.trend_strength < 0.5:
            required *= 1.3
        
        return required
    
    def has_sufficient_oi(self, oi_delta: float, market_condition: MarketCondition) -> bool:
        """Check if OI change is significant enough"""
        required = self.get_required_oi_delta(market_condition)
        return abs(oi_delta) >= required


class VolatilityAwareFilter:
    """
    Adjust all filters based on IV levels
    High IV = stricter filters
    """
    
    def __init__(self):
        self.iv_percentiles: List[float] = []
    
    def update_iv_percentile(self, current_iv: float, historical_ivs: List[float]):
        """Track where current IV stands historically"""
        if not historical_ivs:
            return
        
        sorted_ivs = sorted(historical_ivs)
        try:
            rank = sorted_ivs.index(current_iv)
            percentile = rank / len(sorted_ivs)
            self.iv_percentiles.append(percentile)
            
            # Keep last 50
            if len(self.iv_percentiles) > 50:
                self.iv_percentiles.pop(0)
        except:
            pass
    
    def get_iv_multiplier(self) -> float:
        """
        Returns multiplier for all thresholds
        1.0 = normal, >1.0 = stricter
        """
        if not self.iv_percentiles:
            return 1.0
        
        recent_percentile = sum(self.iv_percentiles[-5:]) / min(5, len(self.iv_percentiles))
        
        if recent_percentile > 0.8:  # Very high IV
            return 1.4
        elif recent_percentile > 0.6:  # High IV
            return 1.2
        elif recent_percentile < 0.3:  # Low IV
            return 0.9
        else:
            return 1.0


class AdaptiveSignalFilter:
    """
    Master adaptive filter orchestrator
    Combines all adaptive filters for optimal noise reduction
    """
    
    def __init__(self):
        self.vol_detector = VolatilityRegimeDetector()
        self.bias_filter = BiasStrengthFilter()
        self.trap_filter = TrapProbabilityFilter()
        self.oi_filter = OIConfirmationFilter()
        self.vol_aware = VolatilityAwareFilter()
        
        # Track filter decisions
        self.total_signals = 0
        self.passed_signals = 0
        self.filter_reasons: Dict[str, int] = {}
    
    def assess_market_condition(self, current_iv: float, oi_data: Dict) -> MarketCondition:
        """
        Assess current market conditions
        Returns MarketCondition object
        """
        # Update volatility tracking
        self.vol_detector.update_volatility(current_iv)
        
        # Determine regime
        vol_regime = self.vol_detector.get_regime()
        time_window = TimeOfDayAnalyzer.get_time_window()
        
        # Calculate noise level (based on IV change rate)
        iv_change_rate = self.vol_detector.get_iv_change_rate()
        noise_level = min(1.0, iv_change_rate / 5.0)  # Normalize
        
        # Estimate trend strength (placeholder - should use actual trend data)
        trend_strength = 0.5  # Default medium
        
        return MarketCondition(
            volatility_regime=vol_regime,
            time_of_day=time_window,
            trend_strength=trend_strength,
            noise_level=noise_level
        )
    
    def evaluate_signal(self, signal_data: Dict) -> Dict:
        """
        Evaluate if signal passes all adaptive filters
        
        signal_data should contain:
        - bias_strength: float (0-1)
        - trap_probability: float (0-1)
        - oi_delta: float
        - current_iv: float
        - oi_data: dict
        
        Returns: {
            "passed": bool,
            "confidence": float,
            "reasons": list
        }
        """
        self.total_signals += 1
        
        # Assess market condition
        market = self.assess_market_condition(
            signal_data.get('current_iv', 20),
            signal_data.get('oi_data', {})
        )
        
        reasons = []
        filters_passed = []
        filters_failed = []
        
        # 1. Bias strength filter
        bias_strength = signal_data.get('bias_strength', 0.0)
        if self.bias_filter.passes_filter(bias_strength, market):
            filters_passed.append("bias_strength")
        else:
            required = self.bias_filter.get_required_strength(market)
            filters_failed.append(f"bias_too_weak ({bias_strength:.2f} < {required:.2f})")
            reasons.append(f"Bias strength {bias_strength:.2f} below threshold {required:.2f}")
        
        # 2. Trap probability filter
        trap_prob = signal_data.get('trap_probability', 0.5)
        if not self.trap_filter.is_likely_trap(trap_prob, market):
            filters_passed.append("trap_check")
        else:
            filters_failed.append(f"likely_trap (prob: {trap_prob:.2f})")
            reasons.append(f"High trap probability: {trap_prob:.2f}")
        
        # 3. OI confirmation filter
        oi_delta = signal_data.get('oi_delta', 0)
        if self.oi_filter.has_sufficient_oi(oi_delta, market):
            filters_passed.append("oi_confirmation")
        else:
            required = self.oi_filter.get_required_oi_delta(market)
            filters_failed.append(f"insufficient_oi ({abs(oi_delta):.0f} < {required:.0f})")
            reasons.append(f"OI delta {abs(oi_delta):.0f} below required {required:.0f}")
        
        # 4. Time of day check
        if market.time_of_day not in ["OPENING", "CLOSING"]:
            filters_passed.append("time_window")
        else:
            # Allow but reduce confidence
            reasons.append(f"Risky time window: {market.time_of_day}")
        
        # Determine if signal passes
        passed = len(filters_failed) == 0
        
        if passed:
            self.passed_signals += 1
        
        # Track filter reasons
        for reason in filters_failed:
            self.filter_reasons[reason] = self.filter_reasons.get(reason, 0) + 1
        
        # Calculate confidence
        # More filters passed = higher confidence
        total_filters = len(filters_passed) + len(filters_failed)
        base_confidence = len(filters_passed) / max(total_filters, 1)
        
        # Adjust for market conditions
        if market.volatility_regime == "EXTREME":
            base_confidence *= 0.8
        elif market.time_of_day in ["OPENING", "CLOSING"]:
            base_confidence *= 0.85
        
        return {
            "passed": passed,
            "confidence": base_confidence,
            "reasons": reasons,
            "market_condition": {
                "volatility": market.volatility_regime,
                "time": market.time_of_day,
                "noise": market.noise_level
            },
            "filters_passed": filters_passed,
            "filters_failed": filters_failed
        }
    
    def get_filter_efficiency(self) -> Dict:
        """Get filtering statistics"""
        if self.total_signals == 0:
            return {
                "total_signals": 0,
                "passed": 0,
                "rejection_rate": 0.0,
                "top_rejection_reasons": []
            }
        
        rejection_rate = ((self.total_signals - self.passed_signals) / self.total_signals) * 100
        
        # Top rejection reasons
        sorted_reasons = sorted(self.filter_reasons.items(), key=lambda x: x[1], reverse=True)
        top_reasons = [(reason, count) for reason, count in sorted_reasons[:5]]
        
        return {
            "total_signals": self.total_signals,
            "passed": self.passed_signals,
            "rejected": self.total_signals - self.passed_signals,
            "rejection_rate": rejection_rate,
            "top_rejection_reasons": top_reasons
        }
    
    def adjust_sensitivity(self, win_rate: float):
        """
        Auto-adjust filter sensitivity based on performance
        Low win rate → stricter filters
        High win rate → can loosen slightly
        """
        if win_rate < 45:
            # Too many losses - tighten all filters
            self.bias_filter.base_threshold += 0.05
            self.trap_filter.base_threshold += 0.05
            self.oi_filter.base_min_delta *= 1.2
        elif win_rate > 65:
            # Very good - can slightly loosen
            self.bias_filter.base_threshold = max(0.5, self.bias_filter.base_threshold - 0.02)
            self.trap_filter.base_threshold = max(0.6, self.trap_filter.base_threshold - 0.02)
        
        # Keep within reasonable bounds
        self.bias_filter.base_threshold = max(0.4, min(0.8, self.bias_filter.base_threshold))
        self.trap_filter.base_threshold = max(0.5, min(0.85, self.trap_filter.base_threshold))
