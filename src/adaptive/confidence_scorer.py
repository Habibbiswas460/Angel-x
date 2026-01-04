"""
PHASE 10.4: Confidence Scorer (Meta-Brain)
Scores every signal based on historical success + current regime

Low confidence → No trade
Medium → Normal risk
High → Full plan

Philosophy: Emotionless decision-making
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from src.adaptive.learning_engine import FeatureBucket, BucketPerformance
from src.adaptive.regime_detector import MarketRegime


class ConfidenceLevel(Enum):
    """Signal confidence classification"""
    VERY_LOW = "VERY_LOW"      # <30% - Block
    LOW = "LOW"                # 30-50% - Cautious
    MEDIUM = "MEDIUM"          # 50-70% - Normal
    HIGH = "HIGH"              # 70-85% - Confident
    VERY_HIGH = "VERY_HIGH"    # >85% - Maximum confidence


@dataclass
class SignalConfidence:
    """Confidence assessment for a trading signal"""
    confidence_score: float  # 0.0-1.0
    confidence_level: ConfidenceLevel
    
    # Contributing factors
    historical_success_score: float       # Based on similar setups
    regime_match_score: float             # Current regime alignment
    recent_performance_score: float       # Recent drawdown state
    sample_size_score: float              # Statistical confidence
    
    # Recommendations
    should_trade: bool
    recommended_size_pct: float           # % of normal size (0.0-1.5)
    confidence_explanation: str
    
    timestamp: datetime


class ConfidenceScorer:
    """
    Meta-brain that scores signal quality
    Prevents overtrading in unfavorable conditions
    """
    
    def __init__(self):
        # Thresholds
        self.min_confidence_to_trade = 0.40        # 40%
        self.high_confidence_threshold = 0.70      # 70%
        self.min_sample_size = 15                  # Need 15+ similar trades
        
        # Drawdown adjustment
        self.recent_loss_penalty = 0.10            # -10% per recent loss
        self.max_drawdown_penalty = 0.30           # Max -30%
    
    def score_signal(self,
                    signal_buckets: List[FeatureBucket],
                    bucket_performance: Dict[FeatureBucket, BucketPerformance],
                    current_regime: MarketRegime,
                    recent_trades: List[Dict]) -> SignalConfidence:
        """
        Main scoring function
        Returns confidence assessment with trade recommendation
        """
        # 1. Historical success score
        hist_score = self._calculate_historical_score(signal_buckets, bucket_performance)
        
        # 2. Regime match score
        regime_score = self._calculate_regime_score(signal_buckets, current_regime)
        
        # 3. Recent performance score (drawdown adjustment)
        recent_score = self._calculate_recent_performance_score(recent_trades)
        
        # 4. Sample size score (statistical confidence)
        sample_score = self._calculate_sample_size_score(signal_buckets, bucket_performance)
        
        # Weighted combination
        confidence_score = (
            hist_score * 0.40 +           # 40% weight on history
            regime_score * 0.25 +         # 25% on regime match
            recent_score * 0.20 +         # 20% on recent performance
            sample_score * 0.15           # 15% on sample adequacy
        )
        
        # Classify confidence level
        conf_level = self._classify_confidence(confidence_score)
        
        # Trading decision
        should_trade = confidence_score >= self.min_confidence_to_trade
        
        # Size recommendation
        size_pct = self._calculate_size_recommendation(confidence_score, conf_level)
        
        # Explanation
        explanation = self._generate_explanation(
            confidence_score, hist_score, regime_score, 
            recent_score, sample_score
        )
        
        return SignalConfidence(
            confidence_score=confidence_score,
            confidence_level=conf_level,
            historical_success_score=hist_score,
            regime_match_score=regime_score,
            recent_performance_score=recent_score,
            sample_size_score=sample_score,
            should_trade=should_trade,
            recommended_size_pct=size_pct,
            confidence_explanation=explanation,
            timestamp=datetime.now()
        )
    
    def _calculate_historical_score(self,
                                    buckets: List[FeatureBucket],
                                    bucket_perf: Dict[FeatureBucket, BucketPerformance]) -> float:
        """
        Score based on historical performance of similar setups
        """
        bucket_scores = []
        
        for bucket in buckets:
            if bucket in bucket_perf:
                perf = bucket_perf[bucket]
                if perf.total_trades >= self.min_sample_size:
                    bucket_scores.append(perf.win_rate)
        
        if not bucket_scores:
            return 0.50  # Neutral (no data)
        
        # Average win rate across buckets
        return sum(bucket_scores) / len(bucket_scores)
    
    def _calculate_regime_score(self,
                                buckets: List[FeatureBucket],
                                current_regime: MarketRegime) -> float:
        """
        Score based on current market regime alignment
        """
        # Check if signal aligns with regime
        
        # Trending regimes favor normal conditions
        if current_regime in [MarketRegime.TRENDING_BULLISH, MarketRegime.TRENDING_BEARISH]:
            return 0.75  # Good for most setups
        
        # Choppy regime - lower confidence
        elif current_regime == MarketRegime.CHOPPY:
            return 0.30  # Difficult conditions
        
        # High volatility - cautious
        elif current_regime == MarketRegime.HIGH_VOLATILITY:
            # Check if we have high-vol bucket
            if FeatureBucket.VOL_HIGH in buckets:
                return 0.40  # Acknowledged risk
            return 0.25  # Unexpected high vol
        
        # Event-driven - very cautious
        elif current_regime == MarketRegime.EVENT_DRIVEN:
            return 0.20  # Wait for clarity
        
        # Low vol - okay but fewer opportunities
        elif current_regime == MarketRegime.LOW_VOLATILITY:
            return 0.60
        
        # Normal regime
        else:
            return 0.70
    
    def _calculate_recent_performance_score(self, recent_trades: List[Dict]) -> float:
        """
        Adjust confidence based on recent performance
        Lower after losses (prevents revenge trading)
        """
        if not recent_trades:
            return 0.70  # Neutral
        
        # Look at last 5 trades
        last_5 = recent_trades[-5:]
        
        # Count consecutive losses
        consecutive_losses = 0
        for trade in reversed(last_5):
            if not trade.get('won', False):
                consecutive_losses += 1
            else:
                break
        
        # Penalty for consecutive losses
        penalty = min(consecutive_losses * self.recent_loss_penalty, self.max_drawdown_penalty)
        
        base_score = 0.70
        return max(0.30, base_score - penalty)  # Floor at 30%
    
    def _calculate_sample_size_score(self,
                                     buckets: List[FeatureBucket],
                                     bucket_perf: Dict[FeatureBucket, BucketPerformance]) -> float:
        """
        Score based on statistical confidence (sample size)
        """
        adequate_samples = 0
        total_buckets = len(buckets)
        
        for bucket in buckets:
            if bucket in bucket_perf:
                if bucket_perf[bucket].sample_size_adequate:
                    adequate_samples += 1
        
        if total_buckets == 0:
            return 0.50
        
        # % of buckets with adequate data
        return adequate_samples / total_buckets
    
    def _classify_confidence(self, score: float) -> ConfidenceLevel:
        """Classify confidence score into level"""
        if score < 0.30:
            return ConfidenceLevel.VERY_LOW
        elif score < 0.50:
            return ConfidenceLevel.LOW
        elif score < 0.70:
            return ConfidenceLevel.MEDIUM
        elif score < 0.85:
            return ConfidenceLevel.HIGH
        else:
            return ConfidenceLevel.VERY_HIGH
    
    def _calculate_size_recommendation(self, score: float, level: ConfidenceLevel) -> float:
        """
        Recommend position size as % of normal
        """
        if level == ConfidenceLevel.VERY_LOW:
            return 0.0  # No trade
        elif level == ConfidenceLevel.LOW:
            return 0.5  # Half size
        elif level == ConfidenceLevel.MEDIUM:
            return 0.8  # Slightly reduced
        elif level == ConfidenceLevel.HIGH:
            return 1.0  # Full size
        else:  # VERY_HIGH
            return 1.2  # Slightly increased (rare)
    
    def _generate_explanation(self, total: float, hist: float, regime: float, 
                             recent: float, sample: float) -> str:
        """Generate human-readable explanation"""
        parts = []
        
        # Overall
        parts.append(f"Confidence: {total:.1%}")
        
        # Breakdown
        if hist < 0.50:
            parts.append(f"⚠️ Historical: {hist:.1%} (weak)")
        else:
            parts.append(f"✅ Historical: {hist:.1%}")
        
        if regime < 0.50:
            parts.append(f"⚠️ Regime: {regime:.1%} (unfavorable)")
        else:
            parts.append(f"✅ Regime: {regime:.1%}")
        
        if recent < 0.60:
            parts.append(f"⚠️ Recent: {recent:.1%} (drawdown)")
        
        if sample < 0.50:
            parts.append(f"⚠️ Sample: {sample:.1%} (limited data)")
        
        return " | ".join(parts)
    
    def should_block_signal(self, confidence: SignalConfidence) -> bool:
        """Quick check: should this signal be blocked?"""
        return confidence.confidence_level == ConfidenceLevel.VERY_LOW or not confidence.should_trade
    
    def get_confidence_summary(self, confidence: SignalConfidence) -> Dict:
        """Get summary for logging/dashboard"""
        return {
            "confidence_score": confidence.confidence_score,
            "confidence_level": confidence.confidence_level.value,
            "should_trade": confidence.should_trade,
            "recommended_size": f"{confidence.recommended_size_pct:.0%}",
            "explanation": confidence.confidence_explanation,
            "breakdown": {
                "historical": confidence.historical_success_score,
                "regime": confidence.regime_match_score,
                "recent": confidence.recent_performance_score,
                "sample": confidence.sample_size_score
            }
        }
