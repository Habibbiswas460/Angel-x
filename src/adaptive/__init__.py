"""
Angel-X Adaptive Learning Module
Phase 10 - Self-correcting, market-aware adaptive system
"""

from src.adaptive.adaptive_controller import AdaptiveController, AdaptiveDecision
from src.adaptive.learning_engine import LearningEngine, FeatureBucket, LearningInsight
from src.adaptive.regime_detector import MarketRegimeDetector, MarketRegime, RegimeClassification
from src.adaptive.weight_adjuster import AdaptiveWeightAdjuster, RuleType
from src.adaptive.confidence_scorer import ConfidenceScorer, ConfidenceLevel, SignalConfidence
from src.adaptive.pattern_detector import LossPatternDetector, PatternType, LossPattern
from src.adaptive.safety_guard import SafetyGuardSystem, SafetyCheck

__all__ = [
    # Main Controller
    "AdaptiveController",
    "AdaptiveDecision",
    # Learning
    "LearningEngine",
    "FeatureBucket",
    "LearningInsight",
    # Regime Detection
    "MarketRegimeDetector",
    "MarketRegime",
    "RegimeClassification",
    # Weight Management
    "AdaptiveWeightAdjuster",
    "RuleType",
    # Confidence Scoring
    "ConfidenceScorer",
    "ConfidenceLevel",
    "SignalConfidence",
    # Pattern Detection
    "LossPatternDetector",
    "PatternType",
    "LossPattern",
    # Safety
    "SafetyGuardSystem",
    "SafetyCheck",
]
