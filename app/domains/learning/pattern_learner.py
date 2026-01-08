"""
PHASE 10.1: Learning Engine
Angel-X learns from its own trading history (NOT external data)

Learning Sources:
- Trade outcomes (Win/Loss)
- Exit reasons
- Greeks state at entry & exit
- OI + Volume conviction
- Time-of-day performance
- Volatility regime

Philosophy: Learning = Filter & Control (NOT prediction)
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict
import statistics


class FeatureBucket(Enum):
    """Human-readable feature categories"""
    # Time buckets
    TIME_OPENING = "OPENING"      # 9:15-10:00
    TIME_MORNING = "MORNING"      # 10:00-11:30
    TIME_LUNCH = "LUNCH"          # 11:30-14:00
    TIME_AFTERNOON = "AFTERNOON"  # 14:00-15:00
    TIME_CLOSING = "CLOSING"      # 15:00-15:30
    
    # Bias strength
    BIAS_LOW = "BIAS_LOW"         # 0.0-0.3
    BIAS_MEDIUM = "BIAS_MEDIUM"   # 0.3-0.7
    BIAS_HIGH = "BIAS_HIGH"       # 0.7-1.0
    
    # Greeks regime
    GREEKS_HIGH_GAMMA = "HIGH_GAMMA"      # Gamma > 0.05
    GREEKS_HIGH_THETA = "HIGH_THETA"      # |Theta| > 50
    GREEKS_NEUTRAL = "GREEKS_NEUTRAL"     # Normal
    
    # OI conviction
    OI_STRONG = "OI_STRONG"       # HIGH conviction
    OI_MEDIUM = "OI_MEDIUM"       # MEDIUM conviction
    OI_WEAK = "OI_WEAK"           # LOW conviction
    
    # Volatility
    VOL_LOW = "VOL_LOW"           # VIX < 15
    VOL_NORMAL = "VOL_NORMAL"     # 15-25
    VOL_HIGH = "VOL_HIGH"         # > 25


@dataclass
class TradeFeatures:
    """Features extracted from a trade"""
    time_bucket: FeatureBucket
    bias_bucket: FeatureBucket
    greeks_bucket: FeatureBucket
    oi_bucket: FeatureBucket
    vol_bucket: FeatureBucket
    
    # Raw values
    entry_delta: float
    entry_theta: float
    entry_gamma: float
    exit_reason: str
    holding_minutes: int
    
    # Outcome
    won: bool
    pnl: float
    timestamp: datetime


@dataclass
class BucketPerformance:
    """Performance metrics for a feature bucket"""
    bucket: FeatureBucket
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0
    win_rate: float = 0.0
    
    # Trend tracking
    recent_wins: int = 0      # Last 10 trades
    recent_losses: int = 0
    recent_win_rate: float = 0.0
    
    # Confidence
    sample_size_adequate: bool = False  # Need 20+ trades
    performance_stable: bool = True
    
    def calculate_metrics(self):
        """Update calculated fields"""
        if self.total_trades > 0:
            self.win_rate = self.wins / self.total_trades
            self.avg_pnl = self.total_pnl / self.total_trades
            self.sample_size_adequate = self.total_trades >= 20
        
        if (self.recent_wins + self.recent_losses) > 0:
            self.recent_win_rate = self.recent_wins / (self.recent_wins + self.recent_losses)
            
            # Performance stable if recent ≈ overall
            if self.total_trades >= 20:
                diff = abs(self.recent_win_rate - self.win_rate)
                self.performance_stable = diff < 0.20  # Within 20%


@dataclass
class LearningInsight:
    """Actionable insight from learning"""
    insight_type: str  # AMPLIFY, RESTRICT, BLOCK, NEUTRAL
    bucket: FeatureBucket
    reason: str
    confidence: float  # 0.0-1.0
    recommendation: str
    supporting_data: Dict
    timestamp: datetime


class LearningEngine:
    """
    Core learning engine
    Analyzes trade history to identify patterns
    Provides explainable insights (NOT black-box)
    """
    
    def __init__(self, min_sample_size: int = 20):
        self.min_sample_size = min_sample_size
        
        # Historical trade features
        self.trade_history: List[TradeFeatures] = []
        
        # Performance by bucket
        self.bucket_performance: Dict[FeatureBucket, BucketPerformance] = {}
        for bucket in FeatureBucket:
            self.bucket_performance[bucket] = BucketPerformance(bucket=bucket)
        
        # Combined bucket performance (e.g., TIME_MORNING + OI_STRONG)
        self.combo_performance: Dict[Tuple[FeatureBucket, ...], BucketPerformance] = {}
        
        # Learning insights
        self.insights: List[LearningInsight] = []
        
        # Last learning update
        self.last_update: Optional[datetime] = None
    
    def ingest_trade(self, trade_features: TradeFeatures):
        """
        Add new trade to learning history
        Does NOT immediately update rules (safety guard)
        """
        self.trade_history.append(trade_features)
        
        # Update bucket counts
        buckets = [
            trade_features.time_bucket,
            trade_features.bias_bucket,
            trade_features.greeks_bucket,
            trade_features.oi_bucket,
            trade_features.vol_bucket
        ]
        
        for bucket in buckets:
            perf = self.bucket_performance[bucket]
            perf.total_trades += 1
            
            if trade_features.won:
                perf.wins += 1
            else:
                perf.losses += 1
            
            perf.total_pnl += trade_features.pnl
            
            # Update recent (last 10)
            recent_trades = [t for t in self.trade_history[-10:] 
                           if bucket in self._get_trade_buckets(t)]
            perf.recent_wins = sum(1 for t in recent_trades if t.won)
            perf.recent_losses = len(recent_trades) - perf.recent_wins
            
            perf.calculate_metrics()
        
        # Also track combinations
        self._update_combo_performance(trade_features)
    
    def _get_trade_buckets(self, trade: TradeFeatures) -> List[FeatureBucket]:
        """Get all buckets for a trade"""
        return [
            trade.time_bucket,
            trade.bias_bucket,
            trade.greeks_bucket,
            trade.oi_bucket,
            trade.vol_bucket
        ]
    
    def _update_combo_performance(self, trade: TradeFeatures):
        """Track performance of bucket combinations"""
        # Important combos
        combos = [
            (trade.time_bucket, trade.oi_bucket),
            (trade.time_bucket, trade.greeks_bucket),
            (trade.bias_bucket, trade.oi_bucket),
            (trade.greeks_bucket, trade.oi_bucket)
        ]
        
        for combo in combos:
            if combo not in self.combo_performance:
                self.combo_performance[combo] = BucketPerformance(bucket=combo[0])
            
            perf = self.combo_performance[combo]
            perf.total_trades += 1
            
            if trade.won:
                perf.wins += 1
            else:
                perf.losses += 1
            
            perf.total_pnl += trade.pnl
            perf.calculate_metrics()
    
    def analyze_patterns(self) -> List[LearningInsight]:
        """
        Analyze all patterns and generate insights
        Called daily (NOT intraday for safety)
        """
        insights = []
        
        # 1. Time bucket analysis
        insights.extend(self._analyze_time_buckets())
        
        # 2. OI conviction analysis
        insights.extend(self._analyze_oi_conviction())
        
        # 3. Greeks regime analysis
        insights.extend(self._analyze_greeks_regime())
        
        # 4. Volatility analysis
        insights.extend(self._analyze_volatility())
        
        # 5. Combination analysis
        insights.extend(self._analyze_combinations())
        
        self.insights = insights
        self.last_update = datetime.now()
        
        return insights
    
    def _analyze_time_buckets(self) -> List[LearningInsight]:
        """Analyze time-of-day performance"""
        insights = []
        
        time_buckets = [
            FeatureBucket.TIME_OPENING,
            FeatureBucket.TIME_MORNING,
            FeatureBucket.TIME_LUNCH,
            FeatureBucket.TIME_AFTERNOON,
            FeatureBucket.TIME_CLOSING
        ]
        
        # Find best and worst
        valid_buckets = [(b, self.bucket_performance[b]) 
                        for b in time_buckets 
                        if self.bucket_performance[b].sample_size_adequate]
        
        if not valid_buckets:
            return insights
        
        valid_buckets.sort(key=lambda x: x[1].win_rate, reverse=True)
        
        # Best time bucket
        best_bucket, best_perf = valid_buckets[0]
        if best_perf.win_rate >= 0.65:  # 65%+ win rate
            insights.append(LearningInsight(
                insight_type="AMPLIFY",
                bucket=best_bucket,
                reason=f"{best_perf.win_rate:.1%} win rate in {best_bucket.value}",
                confidence=min(best_perf.win_rate, 0.95),
                recommendation=f"Prioritize trades during {best_bucket.value}",
                supporting_data={
                    "trades": best_perf.total_trades,
                    "win_rate": best_perf.win_rate,
                    "avg_pnl": best_perf.avg_pnl
                },
                timestamp=datetime.now()
            ))
        
        # Worst time bucket
        worst_bucket, worst_perf = valid_buckets[-1]
        if worst_perf.win_rate <= 0.35:  # 35% or worse
            insights.append(LearningInsight(
                insight_type="RESTRICT",
                bucket=worst_bucket,
                reason=f"Only {worst_perf.win_rate:.1%} win rate in {worst_bucket.value}",
                confidence=1.0 - worst_perf.win_rate,
                recommendation=f"Avoid or reduce trades during {worst_bucket.value}",
                supporting_data={
                    "trades": worst_perf.total_trades,
                    "win_rate": worst_perf.win_rate,
                    "avg_pnl": worst_perf.avg_pnl
                },
                timestamp=datetime.now()
            ))
        
        return insights
    
    def _analyze_oi_conviction(self) -> List[LearningInsight]:
        """Analyze OI conviction effectiveness"""
        insights = []
        
        oi_buckets = [
            FeatureBucket.OI_STRONG,
            FeatureBucket.OI_MEDIUM,
            FeatureBucket.OI_WEAK
        ]
        
        strong_perf = self.bucket_performance[FeatureBucket.OI_STRONG]
        weak_perf = self.bucket_performance[FeatureBucket.OI_WEAK]
        
        # If HIGH conviction working well
        if strong_perf.sample_size_adequate and strong_perf.win_rate >= 0.70:
            insights.append(LearningInsight(
                insight_type="AMPLIFY",
                bucket=FeatureBucket.OI_STRONG,
                reason=f"HIGH OI conviction: {strong_perf.win_rate:.1%} win rate",
                confidence=strong_perf.win_rate,
                recommendation="Prioritize HIGH OI conviction setups",
                supporting_data={
                    "trades": strong_perf.total_trades,
                    "win_rate": strong_perf.win_rate,
                    "avg_pnl": strong_perf.avg_pnl
                },
                timestamp=datetime.now()
            ))
        
        # If LOW conviction failing
        if weak_perf.sample_size_adequate and weak_perf.win_rate <= 0.40:
            insights.append(LearningInsight(
                insight_type="BLOCK",
                bucket=FeatureBucket.OI_WEAK,
                reason=f"LOW OI conviction: {weak_perf.win_rate:.1%} win rate",
                confidence=1.0 - weak_perf.win_rate,
                recommendation="Block trades with LOW OI conviction",
                supporting_data={
                    "trades": weak_perf.total_trades,
                    "win_rate": weak_perf.win_rate,
                    "avg_pnl": weak_perf.avg_pnl
                },
                timestamp=datetime.now()
            ))
        
        return insights
    
    def _analyze_greeks_regime(self) -> List[LearningInsight]:
        """Analyze Greeks regime performance"""
        insights = []
        
        high_gamma = self.bucket_performance[FeatureBucket.GREEKS_HIGH_GAMMA]
        high_theta = self.bucket_performance[FeatureBucket.GREEKS_HIGH_THETA]
        
        # High Gamma quick trades
        if high_gamma.sample_size_adequate:
            if high_gamma.win_rate >= 0.65:
                insights.append(LearningInsight(
                    insight_type="AMPLIFY",
                    bucket=FeatureBucket.GREEKS_HIGH_GAMMA,
                    reason=f"High Gamma trades: {high_gamma.win_rate:.1%} win rate",
                    confidence=high_gamma.win_rate,
                    recommendation="Favor high Gamma quick scalps",
                    supporting_data={
                        "trades": high_gamma.total_trades,
                        "win_rate": high_gamma.win_rate
                    },
                    timestamp=datetime.now()
                ))
            elif high_gamma.win_rate <= 0.40:
                insights.append(LearningInsight(
                    insight_type="RESTRICT",
                    bucket=FeatureBucket.GREEKS_HIGH_GAMMA,
                    reason=f"High Gamma failing: {high_gamma.win_rate:.1%}",
                    confidence=1.0 - high_gamma.win_rate,
                    recommendation="Reduce high Gamma exposure",
                    supporting_data={
                        "trades": high_gamma.total_trades,
                        "win_rate": high_gamma.win_rate
                    },
                    timestamp=datetime.now()
                ))
        
        # High Theta decay trades
        if high_theta.sample_size_adequate and high_theta.win_rate >= 0.65:
            insights.append(LearningInsight(
                insight_type="AMPLIFY",
                bucket=FeatureBucket.GREEKS_HIGH_THETA,
                reason=f"Theta decay effective: {high_theta.win_rate:.1%}",
                confidence=high_theta.win_rate,
                recommendation="Hold for theta decay when applicable",
                supporting_data={
                    "trades": high_theta.total_trades,
                    "win_rate": high_theta.win_rate
                },
                timestamp=datetime.now()
            ))
        
        return insights
    
    def _analyze_volatility(self) -> List[LearningInsight]:
        """Analyze volatility regime impact"""
        insights = []
        
        high_vol = self.bucket_performance[FeatureBucket.VOL_HIGH]
        
        if high_vol.sample_size_adequate and high_vol.win_rate <= 0.40:
            insights.append(LearningInsight(
                insight_type="RESTRICT",
                bucket=FeatureBucket.VOL_HIGH,
                reason=f"High volatility: {high_vol.win_rate:.1%} win rate",
                confidence=1.0 - high_vol.win_rate,
                recommendation="Reduce trades or size in high volatility",
                supporting_data={
                    "trades": high_vol.total_trades,
                    "win_rate": high_vol.win_rate
                },
                timestamp=datetime.now()
            ))
        
        return insights
    
    def _analyze_combinations(self) -> List[LearningInsight]:
        """Analyze powerful bucket combinations"""
        insights = []
        
        # Find high-performing combos
        strong_combos = [
            (combo, perf) for combo, perf in self.combo_performance.items()
            if perf.sample_size_adequate and perf.win_rate >= 0.70
        ]
        
        for combo, perf in strong_combos[:3]:  # Top 3
            bucket_names = " + ".join([b.value for b in combo])
            insights.append(LearningInsight(
                insight_type="AMPLIFY",
                bucket=combo[0],  # Primary bucket
                reason=f"Strong combo: {bucket_names} ({perf.win_rate:.1%})",
                confidence=perf.win_rate,
                recommendation=f"Prioritize setups matching: {bucket_names}",
                supporting_data={
                    "combo": bucket_names,
                    "trades": perf.total_trades,
                    "win_rate": perf.win_rate
                },
                timestamp=datetime.now()
            ))
        
        return insights
    
    def get_bucket_for_time(self, time: datetime) -> FeatureBucket:
        """Classify time into bucket"""
        hour = time.hour
        minute = time.minute
        
        if hour == 9 and minute >= 15:
            return FeatureBucket.TIME_OPENING
        elif hour == 10 or (hour == 11 and minute < 30):
            return FeatureBucket.TIME_MORNING
        elif (hour == 11 and minute >= 30) or hour == 12 or hour == 13:
            return FeatureBucket.TIME_LUNCH
        elif hour == 14:
            return FeatureBucket.TIME_AFTERNOON
        elif hour == 15 and minute < 30:
            return FeatureBucket.TIME_CLOSING
        else:
            return FeatureBucket.TIME_AFTERNOON
    
    def get_bucket_for_bias(self, bias_strength: float) -> FeatureBucket:
        """Classify bias strength into bucket"""
        if bias_strength < 0.3:
            return FeatureBucket.BIAS_LOW
        elif bias_strength < 0.7:
            return FeatureBucket.BIAS_MEDIUM
        else:
            return FeatureBucket.BIAS_HIGH
    
    def get_bucket_for_greeks(self, gamma: float, theta: float) -> FeatureBucket:
        """Classify Greeks into regime"""
        if gamma > 0.05:
            return FeatureBucket.GREEKS_HIGH_GAMMA
        elif abs(theta) > 50:
            return FeatureBucket.GREEKS_HIGH_THETA
        else:
            return FeatureBucket.GREEKS_NEUTRAL
    
    def get_bucket_for_oi(self, conviction: str) -> FeatureBucket:
        """Classify OI conviction into bucket"""
        if conviction == "HIGH":
            return FeatureBucket.OI_STRONG
        elif conviction == "MEDIUM":
            return FeatureBucket.OI_MEDIUM
        else:
            return FeatureBucket.OI_WEAK
    
    def get_bucket_for_volatility(self, vix: float) -> FeatureBucket:
        """Classify volatility into bucket"""
        if vix < 15:
            return FeatureBucket.VOL_LOW
        elif vix <= 25:
            return FeatureBucket.VOL_NORMAL
        else:
            return FeatureBucket.VOL_HIGH
    
    def get_summary(self) -> Dict:
        """Get learning summary for dashboard"""
        return {
            "total_trades_learned": len(self.trade_history),
            "last_update": self.last_update,
            "insights_count": len(self.insights),
            "insights": [
                {
                    "type": insight.insight_type,
                    "bucket": insight.bucket.value,
                    "recommendation": insight.recommendation,
                    "confidence": insight.confidence
                }
                for insight in self.insights
            ],
            "bucket_performance": {
                bucket.value: {
                    "trades": perf.total_trades,
                    "win_rate": perf.win_rate,
                    "adequate_sample": perf.sample_size_adequate
                }
                for bucket, perf in self.bucket_performance.items()
                if perf.total_trades > 0
            }
        }
