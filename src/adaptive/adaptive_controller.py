"""
PHASE 10.7: Adaptive Controller (Master Brain)
Orchestrates all adaptive learning components

Components:
1. Learning Engine - Analyzes history
2. Regime Detector - Classifies market
3. Weight Adjuster - Adapts rules
4. Confidence Scorer - Scores signals
5. Pattern Detector - Finds loss patterns
6. Safety Guard - Enforces constraints

Flow:
Market Data → Regime → Signal → Confidence → Decision → Learn → Adapt
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
import json

from src.adaptive.learning_engine import (
    LearningEngine, TradeFeatures, FeatureBucket, LearningInsight
)
from src.adaptive.regime_detector import (
    MarketRegimeDetector, RegimeSignals, RegimeClassification, MarketRegime
)
from src.adaptive.weight_adjuster import (
    AdaptiveWeightAdjuster, RuleType, WeightAdjustment
)
from src.adaptive.confidence_scorer import (
    ConfidenceScorer, SignalConfidence, ConfidenceLevel
)
from src.adaptive.pattern_detector import (
    LossPatternDetector, LossPattern, PatternBlock
)
from src.adaptive.safety_guard import (
    SafetyGuardSystem, SafetyCheck, LearningProposal
)


@dataclass
class AdaptiveDecision:
    """Complete adaptive decision for a trade signal"""
    # Signal evaluation
    signal_buckets: List[FeatureBucket]
    confidence: SignalConfidence
    current_regime: RegimeClassification
    
    # Decision
    should_trade: bool
    block_reason: Optional[str]
    recommended_size: float           # Multiplier
    recommended_frequency: float      # Multiplier
    
    # Transparency
    decision_explanation: str
    contributing_factors: Dict
    
    timestamp: datetime


class AdaptiveController:
    """
    Master controller for adaptive learning system
    Coordinates all components with safety
    """
    
    def __init__(self, config: Optional[Dict] = None):
        # Initialize all components
        self.learning_engine = LearningEngine()
        self.regime_detector = MarketRegimeDetector()
        self.weight_adjuster = AdaptiveWeightAdjuster()
        self.confidence_scorer = ConfidenceScorer()
        self.pattern_detector = LossPatternDetector()
        self.safety_guard = SafetyGuardSystem()
        
        # Configuration
        self.config = config or {}
        self.enabled = self.config.get('adaptive_enabled', True)
        
        # State
        self.last_daily_learning: Optional[datetime] = None
        self.learning_active = False
    
    def evaluate_signal(self,
                       market_data: Dict,
                       signal_data: Dict,
                       recent_trades: List[Dict]) -> AdaptiveDecision:
        """
        Main signal evaluation function
        Combines all adaptive components to make decision
        
        Args:
            market_data: Current market state
            signal_data: Trading signal details
            recent_trades: Recent trade history
            
        Returns:
            AdaptiveDecision with trade recommendation
        """
        if not self.enabled:
            # Fallback to normal operation
            return self._create_default_decision(signal_data)
        
        # 1. Detect market regime
        regime_signals = self.regime_detector.create_signals_from_market_data(market_data)
        regime = self.regime_detector.detect_regime(regime_signals)
        
        # 2. Extract signal buckets
        buckets = self._extract_signal_buckets(signal_data)
        
        # 3. Check for pattern blocks
        blocked, block_reason = self._check_pattern_blocks(buckets)
        if blocked:
            return self._create_blocked_decision(buckets, regime, block_reason)
        
        # 4. Score signal confidence
        confidence = self.confidence_scorer.score_signal(
            signal_buckets=buckets,
            bucket_performance=self.learning_engine.bucket_performance,
            current_regime=regime.regime,
            recent_trades=recent_trades
        )
        
        # 5. Apply adaptive weights
        size_multiplier = self._calculate_size_multiplier(buckets, regime, confidence)
        freq_multiplier = self._calculate_frequency_multiplier(buckets, regime)
        
        # 6. Make decision
        should_trade = confidence.should_trade and not blocked
        
        # 7. Generate explanation
        explanation = self._generate_decision_explanation(
            confidence, regime, buckets, size_multiplier, freq_multiplier
        )
        
        return AdaptiveDecision(
            signal_buckets=buckets,
            confidence=confidence,
            current_regime=regime,
            should_trade=should_trade,
            block_reason=block_reason,
            recommended_size=size_multiplier,
            recommended_frequency=freq_multiplier,
            decision_explanation=explanation,
            contributing_factors={
                "regime": regime.regime.value,
                "confidence": confidence.confidence_score,
                "historical_win_rate": confidence.historical_success_score,
                "regime_match": confidence.regime_match_score
            },
            timestamp=datetime.now()
        )
    
    def _extract_signal_buckets(self, signal_data: Dict) -> List[FeatureBucket]:
        """Extract feature buckets from signal"""
        buckets = []
        
        # Time bucket
        signal_time = signal_data.get('time', datetime.now())
        time_bucket = self.learning_engine.get_bucket_for_time(signal_time)
        buckets.append(time_bucket)
        
        # Bias bucket
        bias_strength = signal_data.get('bias_strength', 0.5)
        bias_bucket = self.learning_engine.get_bucket_for_bias(bias_strength)
        buckets.append(bias_bucket)
        
        # Greeks bucket
        gamma = signal_data.get('gamma', 0.03)
        theta = signal_data.get('theta', -30)
        greeks_bucket = self.learning_engine.get_bucket_for_greeks(gamma, theta)
        buckets.append(greeks_bucket)
        
        # OI bucket
        oi_conviction = signal_data.get('oi_conviction', 'MEDIUM')
        oi_bucket = self.learning_engine.get_bucket_for_oi(oi_conviction)
        buckets.append(oi_bucket)
        
        # Volatility bucket
        vix = signal_data.get('vix', 18.0)
        vol_bucket = self.learning_engine.get_bucket_for_volatility(vix)
        buckets.append(vol_bucket)
        
        return buckets
    
    def _check_pattern_blocks(self, buckets: List[FeatureBucket]) -> tuple:
        """Check if any bucket is blocked due to loss patterns"""
        for bucket in buckets:
            blocked, reason = self.pattern_detector.is_bucket_blocked(bucket)
            if blocked:
                return True, reason
        
        return False, None
    
    def _calculate_size_multiplier(self,
                                   buckets: List[FeatureBucket],
                                   regime: RegimeClassification,
                                   confidence: SignalConfidence) -> float:
        """
        Calculate position size multiplier
        Combines regime + confidence + adaptive weights
        """
        # Start with confidence-based size
        base_multiplier = confidence.recommended_size_pct
        
        # Regime adjustment
        regime_multiplier = self.regime_detector.get_size_multiplier()
        
        # Adaptive weight adjustment
        weight_multiplier = self.weight_adjuster.get_size_adjustment(buckets)
        
        # Combined
        final = base_multiplier * regime_multiplier * weight_multiplier
        
        return max(0.0, min(1.5, final))  # Cap at 0-150%
    
    def _calculate_frequency_multiplier(self,
                                        buckets: List[FeatureBucket],
                                        regime: RegimeClassification) -> float:
        """
        Calculate trade frequency multiplier
        How selective should we be?
        """
        # Regime-based frequency
        regime_freq = self.regime_detector.get_frequency_multiplier()
        
        # Weight-based (time filter impact)
        time_bucket = next((b for b in buckets if b.value.startswith("TIME_")), None)
        weight_freq = 1.0
        
        if time_bucket:
            time_weight = self.weight_adjuster.get_weight_for_bucket(
                RuleType.TIME_FILTER, time_bucket
            )
            weight_freq = time_weight
        
        return regime_freq * weight_freq
    
    def _generate_decision_explanation(self,
                                       confidence: SignalConfidence,
                                       regime: RegimeClassification,
                                       buckets: List[FeatureBucket],
                                       size_mult: float,
                                       freq_mult: float) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        # Confidence
        parts.append(f"Confidence: {confidence.confidence_level.value} ({confidence.confidence_score:.1%})")
        
        # Regime
        parts.append(f"Regime: {regime.regime.value}")
        parts.append(f"Posture: {regime.recommended_trade_frequency}")
        
        # Size recommendation
        if size_mult < 0.7:
            parts.append(f"⚠️ Reduced size ({size_mult:.0%})")
        elif size_mult > 1.1:
            parts.append(f"✅ Increased size ({size_mult:.0%})")
        
        # Frequency
        if freq_mult < 0.7:
            parts.append(f"⚠️ Be selective (freq: {freq_mult:.0%})")
        
        return " | ".join(parts)
    
    def _create_default_decision(self, signal_data: Dict) -> AdaptiveDecision:
        """Fallback decision when adaptive disabled"""
        buckets = self._extract_signal_buckets(signal_data)
        
        return AdaptiveDecision(
            signal_buckets=buckets,
            confidence=None,
            current_regime=None,
            should_trade=True,
            block_reason=None,
            recommended_size=1.0,
            recommended_frequency=1.0,
            decision_explanation="Adaptive learning disabled - using defaults",
            contributing_factors={},
            timestamp=datetime.now()
        )
    
    def _create_blocked_decision(self,
                                buckets: List[FeatureBucket],
                                regime: RegimeClassification,
                                reason: str) -> AdaptiveDecision:
        """Create decision for blocked signal"""
        return AdaptiveDecision(
            signal_buckets=buckets,
            confidence=None,
            current_regime=regime,
            should_trade=False,
            block_reason=reason,
            recommended_size=0.0,
            recommended_frequency=0.0,
            decision_explanation=f"🚫 BLOCKED: {reason}",
            contributing_factors={"block_reason": reason},
            timestamp=datetime.now()
        )
    
    def record_trade_outcome(self, trade_result: Dict):
        """
        Record trade outcome for learning
        Called after trade completion
        """
        # Create TradeFeatures from result
        features = TradeFeatures(
            time_bucket=self.learning_engine.get_bucket_for_time(trade_result.get('entry_time', datetime.now())),
            bias_bucket=self.learning_engine.get_bucket_for_bias(trade_result.get('bias_strength', 0.5)),
            greeks_bucket=self.learning_engine.get_bucket_for_greeks(
                trade_result.get('gamma', 0.03), 
                trade_result.get('theta', -30)
            ),
            oi_bucket=self.learning_engine.get_bucket_for_oi(trade_result.get('oi_conviction', 'MEDIUM')),
            vol_bucket=self.learning_engine.get_bucket_for_volatility(trade_result.get('vix', 18.0)),
            entry_delta=trade_result.get('entry_delta', 0.5),
            entry_theta=trade_result.get('entry_theta', -30),
            entry_gamma=trade_result.get('entry_gamma', 0.03),
            exit_reason=trade_result.get('exit_reason', 'UNKNOWN'),
            holding_minutes=trade_result.get('holding_minutes', 30),
            won=trade_result.get('won', False),
            pnl=trade_result.get('pnl', 0.0),
            timestamp=trade_result.get('exit_time', datetime.now())
        )
        
        # Ingest into learning engine
        self.learning_engine.ingest_trade(features)
    
    def run_daily_learning(self) -> Dict:
        """
        Run daily learning cycle (EOD)
        Analyzes patterns and proposes adaptations
        
        Returns summary of learning
        """
        # Safety check
        safety_check = self.safety_guard.check_learning_allowed()
        if not safety_check.passed:
            return {
                "success": False,
                "reason": safety_check.reason,
                "recommendation": safety_check.recommendation
            }
        
        # 1. Analyze patterns
        insights = self.learning_engine.analyze_patterns()
        
        # 2. Detect loss patterns
        loss_patterns = self.pattern_detector.analyze_trade_history(
            self.learning_engine.trade_history
        )
        
        # 3. Propose weight adjustments
        proposals = []
        for insight in insights:
            proposal = self.safety_guard.propose_learning_update(
                proposal_type="WEIGHT_ADJUSTMENT",
                details={
                    "insight": {
                        "type": insight.insight_type,
                        "bucket": insight.bucket.value,
                        "reason": insight.reason
                    }
                },
                confidence=insight.confidence
            )
            proposals.append(proposal)
        
        # 4. Auto-review proposals
        self.safety_guard.auto_review_proposals()
        
        # 5. Apply approved proposals
        approved = [p for p in self.safety_guard.approved_proposals 
                   if p.approved_at and 
                   (datetime.now() - p.approved_at).days == 0]
        
        for proposal in approved:
            # Apply weight adjustment
            # (Would extract insight and call weight_adjuster.apply_learning_insights)
            pass
        
        self.last_daily_learning = datetime.now()
        
        return {
            "success": True,
            "insights_generated": len(insights),
            "loss_patterns_detected": len(loss_patterns),
            "proposals_created": len(proposals),
            "proposals_approved": len(approved),
            "timestamp": self.last_daily_learning
        }
    
    def get_adaptive_status(self) -> Dict:
        """Get complete adaptive system status for dashboard"""
        return {
            "enabled": self.enabled,
            "last_daily_learning": self.last_daily_learning,
            
            # Learning engine
            "learning": self.learning_engine.get_summary(),
            
            # Regime
            "regime": self.regime_detector.get_current_posture(),
            
            # Weight adjustments
            "weights": self.weight_adjuster.get_dashboard_summary(),
            
            # Pattern detection
            "patterns": self.pattern_detector.get_pattern_summary(),
            
            # Safety
            "safety": self.safety_guard.get_safety_status()
        }
    
    def emergency_reset(self):
        """Emergency reset all adaptive learning"""
        self.weight_adjuster.reset_all_weights()
        self.safety_guard.emergency_reset()
        print("🚨 ADAPTIVE SYSTEM RESET TO BASELINE")
    
    def export_state(self, filepath: str):
        """Export adaptive state for persistence"""
        state = {
            "last_daily_learning": self.last_daily_learning.isoformat() if self.last_daily_learning else None,
            "weights": self.weight_adjuster.export_weights(),
            "learning_summary": self.learning_engine.get_summary(),
            "timestamp": datetime.now().isoformat()
        }
        
        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2)
    
    def import_state(self, filepath: str):
        """Import adaptive state from file"""
        with open(filepath, 'r') as f:
            state = json.load(f)
        
        if state.get("last_daily_learning"):
            self.last_daily_learning = datetime.fromisoformat(state["last_daily_learning"])
        
        if state.get("weights"):
            self.weight_adjuster.import_weights(state["weights"])
