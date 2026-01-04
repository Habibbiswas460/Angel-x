"""
PHASE 10.3: Adaptive Weight Adjuster
Adjusts rule weights based on learning (NOT strategy change)

Philosophy: Edge amplify, logic intact
- Good edge → increase weight
- Bad edge → decrease weight
- NEVER change core rules
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from src.adaptive.learning_engine import FeatureBucket, LearningInsight


class RuleType(Enum):
    """Types of rules that can be weighted"""
    TIME_FILTER = "TIME_FILTER"               # Time-of-day filtering
    OI_CONVICTION = "OI_CONVICTION"           # OI strength requirement
    GREEKS_THRESHOLD = "GREEKS_THRESHOLD"     # Delta/Gamma/Theta limits
    BIAS_STRENGTH = "BIAS_STRENGTH"           # Bias strength requirement
    VOLATILITY_FILTER = "VOLATILITY_FILTER"   # Volatility-based filtering
    RISK_SIZING = "RISK_SIZING"               # Position sizing rules


@dataclass
class RuleWeight:
    """Weight for a specific rule"""
    rule_type: RuleType
    feature_bucket: Optional[FeatureBucket]  # If rule is bucket-specific
    
    # Weight (0.0 = disabled, 1.0 = normal, >1.0 = amplified)
    current_weight: float = 1.0
    base_weight: float = 1.0
    min_weight: float = 0.0
    max_weight: float = 2.0
    
    # Adjustment tracking
    last_adjusted: Optional[datetime] = None
    adjustment_reason: Optional[str] = None
    
    # Performance impact
    trades_affected: int = 0
    performance_delta: float = 0.0  # Win rate change when rule active
    
    def adjust_weight(self, delta: float, reason: str):
        """Adjust weight (with safety limits)"""
        new_weight = self.current_weight + delta
        self.current_weight = max(self.min_weight, min(self.max_weight, new_weight))
        self.last_adjusted = datetime.now()
        self.adjustment_reason = reason
    
    def reset_to_base(self):
        """Reset to baseline weight"""
        self.current_weight = self.base_weight
        self.last_adjusted = datetime.now()
        self.adjustment_reason = "Manual reset"
    
    def is_active(self) -> bool:
        """Check if rule is active (weight > 0)"""
        return self.current_weight > 0.0
    
    def get_multiplier(self) -> float:
        """Get multiplier for calculations"""
        return self.current_weight


@dataclass
class WeightAdjustment:
    """Record of a weight adjustment"""
    rule_type: RuleType
    bucket: Optional[FeatureBucket]
    old_weight: float
    new_weight: float
    reason: str
    impact: str  # "AMPLIFY", "RESTRICT", "BLOCK"
    timestamp: datetime


class AdaptiveWeightAdjuster:
    """
    Manages adaptive rule weights
    Adjusts based on learning insights (NOT random mutations)
    """
    
    def __init__(self):
        # Rule weights
        self.rule_weights: Dict[str, RuleWeight] = {}
        
        # Adjustment history
        self.adjustment_history: List[WeightAdjustment] = []
        
        # Safety limits
        self.max_daily_adjustments = 5
        self.min_adjustment_interval_hours = 24  # Daily only
        self.max_weight_change_per_day = 0.5
        
        self._initialize_default_weights()
    
    def _initialize_default_weights(self):
        """Create default rule weights"""
        # Time filters (one per bucket)
        for bucket in [FeatureBucket.TIME_OPENING, FeatureBucket.TIME_MORNING, 
                       FeatureBucket.TIME_LUNCH, FeatureBucket.TIME_AFTERNOON, 
                       FeatureBucket.TIME_CLOSING]:
            key = f"{RuleType.TIME_FILTER.value}_{bucket.value}"
            self.rule_weights[key] = RuleWeight(
                rule_type=RuleType.TIME_FILTER,
                feature_bucket=bucket,
                current_weight=1.0,
                base_weight=1.0
            )
        
        # OI conviction weights
        for bucket in [FeatureBucket.OI_STRONG, FeatureBucket.OI_MEDIUM, FeatureBucket.OI_WEAK]:
            key = f"{RuleType.OI_CONVICTION.value}_{bucket.value}"
            self.rule_weights[key] = RuleWeight(
                rule_type=RuleType.OI_CONVICTION,
                feature_bucket=bucket,
                current_weight=1.0,
                base_weight=1.0
            )
        
        # Greeks regime weights
        for bucket in [FeatureBucket.GREEKS_HIGH_GAMMA, FeatureBucket.GREEKS_HIGH_THETA]:
            key = f"{RuleType.GREEKS_THRESHOLD.value}_{bucket.value}"
            self.rule_weights[key] = RuleWeight(
                rule_type=RuleType.GREEKS_THRESHOLD,
                feature_bucket=bucket,
                current_weight=1.0,
                base_weight=1.0
            )
        
        # Volatility weights
        for bucket in [FeatureBucket.VOL_LOW, FeatureBucket.VOL_NORMAL, FeatureBucket.VOL_HIGH]:
            key = f"{RuleType.VOLATILITY_FILTER.value}_{bucket.value}"
            self.rule_weights[key] = RuleWeight(
                rule_type=RuleType.VOLATILITY_FILTER,
                feature_bucket=bucket,
                current_weight=1.0,
                base_weight=1.0
            )
    
    def apply_learning_insights(self, insights: List[LearningInsight]) -> List[WeightAdjustment]:
        """
        Apply learning insights to adjust weights
        This is the main adaptation mechanism
        """
        adjustments = []
        
        for insight in insights:
            adjustment = self._process_insight(insight)
            if adjustment:
                adjustments.append(adjustment)
        
        # Safety check: limit adjustments
        if len(adjustments) > self.max_daily_adjustments:
            # Keep highest confidence adjustments
            adjustments.sort(key=lambda x: abs(x.new_weight - x.old_weight), reverse=True)
            adjustments = adjustments[:self.max_daily_adjustments]
        
        self.adjustment_history.extend(adjustments)
        
        return adjustments
    
    def _process_insight(self, insight: LearningInsight) -> Optional[WeightAdjustment]:
        """
        Process a single learning insight
        Returns weight adjustment if applicable
        """
        # Determine rule type from bucket
        rule_type = self._get_rule_type_for_bucket(insight.bucket)
        if not rule_type:
            return None
        
        key = f"{rule_type.value}_{insight.bucket.value}"
        if key not in self.rule_weights:
            return None
        
        rule_weight = self.rule_weights[key]
        old_weight = rule_weight.current_weight
        
        # Calculate weight change based on insight
        if insight.insight_type == "AMPLIFY":
            # Increase weight for good edges
            delta = 0.3 * insight.confidence  # Max +0.3
            rule_weight.adjust_weight(delta, insight.reason)
        
        elif insight.insight_type == "RESTRICT":
            # Decrease weight for poor edges
            delta = -0.3 * insight.confidence  # Max -0.3
            rule_weight.adjust_weight(delta, insight.reason)
        
        elif insight.insight_type == "BLOCK":
            # Set weight to 0 (temporary block)
            delta = -rule_weight.current_weight
            rule_weight.adjust_weight(delta, insight.reason)
        
        else:  # NEUTRAL
            return None
        
        new_weight = rule_weight.current_weight
        
        # Create adjustment record
        return WeightAdjustment(
            rule_type=rule_type,
            bucket=insight.bucket,
            old_weight=old_weight,
            new_weight=new_weight,
            reason=insight.reason,
            impact=insight.insight_type,
            timestamp=datetime.now()
        )
    
    def _get_rule_type_for_bucket(self, bucket: FeatureBucket) -> Optional[RuleType]:
        """Map bucket to rule type"""
        bucket_value = bucket.value
        
        if bucket_value.startswith("TIME_"):
            return RuleType.TIME_FILTER
        elif bucket_value.startswith("OI_"):
            return RuleType.OI_CONVICTION
        elif bucket_value.startswith("GREEKS_"):
            return RuleType.GREEKS_THRESHOLD
        elif bucket_value.startswith("VOL_"):
            return RuleType.VOLATILITY_FILTER
        elif bucket_value.startswith("BIAS_"):
            return RuleType.BIAS_STRENGTH
        
        return None
    
    def get_weight_for_bucket(self, rule_type: RuleType, bucket: FeatureBucket) -> float:
        """Get current weight for a rule + bucket combination"""
        key = f"{rule_type.value}_{bucket.value}"
        if key in self.rule_weights:
            return self.rule_weights[key].current_weight
        return 1.0  # Default
    
    def should_allow_trade_in_bucket(self, bucket: FeatureBucket) -> bool:
        """
        Check if trading allowed in this bucket
        Used for time filters, volatility filters
        """
        # Check time filter
        time_key = f"{RuleType.TIME_FILTER.value}_{bucket.value}"
        if time_key in self.rule_weights:
            if not self.rule_weights[time_key].is_active():
                return False  # Time blocked
        
        # Check volatility filter
        vol_key = f"{RuleType.VOLATILITY_FILTER.value}_{bucket.value}"
        if vol_key in self.rule_weights:
            if not self.rule_weights[vol_key].is_active():
                return False  # Volatility blocked
        
        return True
    
    def get_oi_conviction_multiplier(self, bucket: FeatureBucket) -> float:
        """
        Get OI conviction weight multiplier
        Higher for STRONG, lower for WEAK if learning suggests
        """
        key = f"{RuleType.OI_CONVICTION.value}_{bucket.value}"
        if key in self.rule_weights:
            return self.rule_weights[key].get_multiplier()
        return 1.0
    
    def get_size_adjustment(self, buckets: List[FeatureBucket]) -> float:
        """
        Get position size adjustment based on active buckets
        Returns multiplier: 1.0 = normal, <1.0 = reduce, >1.0 = increase
        """
        # Start with base 1.0
        multiplier = 1.0
        
        # Check each bucket's weight
        for bucket in buckets:
            # Time bucket impact
            time_key = f"{RuleType.TIME_FILTER.value}_{bucket.value}"
            if time_key in self.rule_weights:
                time_weight = self.rule_weights[time_key].current_weight
                if time_weight < 0.5:  # Low weight = reduce size
                    multiplier *= 0.7
            
            # Volatility impact
            vol_key = f"{RuleType.VOLATILITY_FILTER.value}_{bucket.value}"
            if vol_key in self.rule_weights:
                vol_weight = self.rule_weights[vol_key].current_weight
                if vol_weight < 0.5:  # High vol, low weight = reduce
                    multiplier *= 0.7
        
        return max(0.5, min(1.5, multiplier))  # Limit to 0.5x - 1.5x
    
    def get_recent_adjustments(self, hours: int = 24) -> List[WeightAdjustment]:
        """Get adjustments in last N hours"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [adj for adj in self.adjustment_history if adj.timestamp >= cutoff]
    
    def get_dashboard_summary(self) -> Dict:
        """Get summary for dashboard transparency"""
        # Active restrictions
        restrictions = []
        amplifications = []
        
        for key, weight in self.rule_weights.items():
            if weight.current_weight == 0.0:
                restrictions.append({
                    "rule": weight.rule_type.value,
                    "bucket": weight.feature_bucket.value if weight.feature_bucket else "ALL",
                    "reason": weight.adjustment_reason or "Learning-based block"
                })
            elif weight.current_weight > 1.2:
                amplifications.append({
                    "rule": weight.rule_type.value,
                    "bucket": weight.feature_bucket.value if weight.feature_bucket else "ALL",
                    "weight": weight.current_weight,
                    "reason": weight.adjustment_reason or "Learning-based amplification"
                })
        
        # Recent changes
        recent = self.get_recent_adjustments(hours=24)
        
        return {
            "active_restrictions": restrictions,
            "active_amplifications": amplifications,
            "recent_adjustments": [
                {
                    "rule": adj.rule_type.value,
                    "bucket": adj.bucket.value if adj.bucket else "ALL",
                    "change": f"{adj.old_weight:.2f} → {adj.new_weight:.2f}",
                    "impact": adj.impact,
                    "reason": adj.reason
                }
                for adj in recent[-5:]  # Last 5
            ],
            "total_adjustments_today": len(recent)
        }
    
    def reset_all_weights(self):
        """Reset all weights to baseline (emergency reset)"""
        for weight in self.rule_weights.values():
            weight.reset_to_base()
    
    def export_weights(self) -> Dict:
        """Export current weights for persistence"""
        return {
            key: {
                "rule_type": weight.rule_type.value,
                "bucket": weight.feature_bucket.value if weight.feature_bucket else None,
                "current_weight": weight.current_weight,
                "last_adjusted": weight.last_adjusted.isoformat() if weight.last_adjusted else None,
                "reason": weight.adjustment_reason
            }
            for key, weight in self.rule_weights.items()
        }
    
    def import_weights(self, weights_data: Dict):
        """Import weights from saved state"""
        for key, data in weights_data.items():
            if key in self.rule_weights:
                self.rule_weights[key].current_weight = data["current_weight"]
                if data.get("last_adjusted"):
                    self.rule_weights[key].last_adjusted = datetime.fromisoformat(data["last_adjusted"])
                self.rule_weights[key].adjustment_reason = data.get("reason")


from datetime import timedelta
