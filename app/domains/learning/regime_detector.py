"""
PHASE 10.2: Market Regime Detector
Identifies market character: Trending / Choppy / High-Vol / Event-Driven

Same strategy, different posture:
- Choppy → fewer trades
- High vol → lower size
- Trending → allow runners
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import statistics


class MarketRegime(Enum):
    """Market character classification"""
    TRENDING_BULLISH = "TRENDING_BULLISH"   # Strong uptrend
    TRENDING_BEARISH = "TRENDING_BEARISH"   # Strong downtrend
    CHOPPY = "CHOPPY"                       # Range-bound, whipsaws
    HIGH_VOLATILITY = "HIGH_VOLATILITY"     # Explosive moves
    LOW_VOLATILITY = "LOW_VOLATILITY"       # Quiet, slow
    EVENT_DRIVEN = "EVENT_DRIVEN"           # News/event impact
    NORMAL = "NORMAL"                        # Standard conditions


class RegimeIndicator(Enum):
    """Indicators for regime detection"""
    TREND_STRENGTH = "trend_strength"       # ADX-like
    VOLATILITY = "volatility"               # ATR, VIX
    CHOPPINESS = "choppiness"               # Range / Movement ratio
    MOMENTUM = "momentum"                    # Rate of change
    BREADTH = "breadth"                      # Option chain uniformity


@dataclass
class RegimeSignals:
    """Raw signals for regime classification"""
    # Price action
    price_range_pct: float           # Daily range as % of price
    higher_highs: bool               # Making new highs
    lower_lows: bool                 # Making new lows
    
    # Volatility
    vix: float
    atr_pct: float                   # ATR as % of price
    
    # Momentum
    rate_of_change_5min: float       # % change in 5 min
    rate_of_change_15min: float      # % change in 15 min
    
    # Option chain signals
    oi_imbalance: float              # CE vs PE OI imbalance
    iv_expansion: bool               # IV increasing
    
    # Volume
    volume_surge: bool               # Volume > avg
    
    timestamp: datetime


@dataclass
class RegimeClassification:
    """Market regime classification with confidence"""
    regime: MarketRegime
    confidence: float                # 0.0-1.0
    sub_characteristics: List[str]   # Additional traits
    
    # Adaptation recommendations
    recommended_trade_frequency: str  # "NORMAL", "REDUCED", "MINIMAL"
    recommended_position_size: str    # "NORMAL", "REDUCED", "MINIMAL"
    recommended_holding_style: str    # "QUICK", "NORMAL", "RUNNER"
    
    # Supporting data
    signals: RegimeSignals
    timestamp: datetime
    
    def get_posture_description(self) -> str:
        """Human-readable posture"""
        return (f"{self.regime.value}: "
                f"Freq={self.recommended_trade_frequency}, "
                f"Size={self.recommended_position_size}, "
                f"Style={self.recommended_holding_style}")


class MarketRegimeDetector:
    """
    Detects current market regime
    Updates every 5-15 minutes during market hours
    """
    
    def __init__(self):
        self.current_regime: Optional[RegimeClassification] = None
        self.regime_history: List[RegimeClassification] = []
        
        # Calibration thresholds
        self.trending_threshold = 0.70      # Trend strength
        self.choppy_threshold = 0.30        # Low directional movement
        self.high_vol_vix = 25.0           # VIX threshold
        self.low_vol_vix = 15.0
        self.event_volume_multiplier = 2.0
    
    def detect_regime(self, signals: RegimeSignals) -> RegimeClassification:
        """
        Main regime detection logic
        Returns classification with adaptation recommendations
        """
        regime = MarketRegime.NORMAL
        confidence = 0.5
        sub_chars = []
        
        # 1. Check for HIGH VOLATILITY (priority)
        if signals.vix > self.high_vol_vix or signals.atr_pct > 2.0:
            regime = MarketRegime.HIGH_VOLATILITY
            confidence = min(signals.vix / 30.0, 0.95)
            sub_chars.append("Wide swings")
            
            if abs(signals.rate_of_change_5min) > 0.5:
                sub_chars.append("Fast moves")
        
        # 2. Check for EVENT DRIVEN
        elif signals.volume_surge and signals.iv_expansion:
            regime = MarketRegime.EVENT_DRIVEN
            confidence = 0.80
            sub_chars.append("News impact")
        
        # 3. Check for TRENDING
        elif signals.higher_highs and not signals.lower_lows:
            regime = MarketRegime.TRENDING_BULLISH
            confidence = 0.75 if abs(signals.oi_imbalance) > 0.3 else 0.60
            sub_chars.append("Sustained direction")
            
            if signals.rate_of_change_15min > 0.3:
                sub_chars.append("Strong momentum")
        
        elif signals.lower_lows and not signals.higher_highs:
            regime = MarketRegime.TRENDING_BEARISH
            confidence = 0.75 if abs(signals.oi_imbalance) > 0.3 else 0.60
            sub_chars.append("Sustained direction")
            
            if signals.rate_of_change_15min < -0.3:
                sub_chars.append("Strong momentum")
        
        # 4. Check for CHOPPY
        elif signals.price_range_pct < 0.5 and abs(signals.rate_of_change_15min) < 0.2:
            regime = MarketRegime.CHOPPY
            confidence = 0.70
            sub_chars.append("Range-bound")
            
            if signals.higher_highs and signals.lower_lows:
                sub_chars.append("Whipsaw risk")
        
        # 5. Check for LOW VOLATILITY
        elif signals.vix < self.low_vol_vix and signals.atr_pct < 0.8:
            regime = MarketRegime.LOW_VOLATILITY
            confidence = 0.65
            sub_chars.append("Quiet")
        
        # Determine adaptation
        trade_freq, position_size, holding_style = self._get_adaptations(regime, signals)
        
        classification = RegimeClassification(
            regime=regime,
            confidence=confidence,
            sub_characteristics=sub_chars,
            recommended_trade_frequency=trade_freq,
            recommended_position_size=position_size,
            recommended_holding_style=holding_style,
            signals=signals,
            timestamp=datetime.now()
        )
        
        self.current_regime = classification
        self.regime_history.append(classification)
        
        # Keep last 100 regime classifications
        if len(self.regime_history) > 100:
            self.regime_history = self.regime_history[-100:]
        
        return classification
    
    def _get_adaptations(self, regime: MarketRegime, signals: RegimeSignals) -> tuple:
        """
        Determine adaptation recommendations based on regime
        Returns: (trade_frequency, position_size, holding_style)
        """
        # Default
        freq = "NORMAL"
        size = "NORMAL"
        style = "NORMAL"
        
        if regime == MarketRegime.HIGH_VOLATILITY:
            freq = "REDUCED"      # Fewer trades
            size = "REDUCED"      # Smaller size
            style = "QUICK"       # Fast exits
        
        elif regime == MarketRegime.CHOPPY:
            freq = "MINIMAL"      # Very selective
            size = "REDUCED"      # Smaller risk
            style = "QUICK"       # Don't overstay
        
        elif regime == MarketRegime.TRENDING_BULLISH or regime == MarketRegime.TRENDING_BEARISH:
            freq = "NORMAL"
            size = "NORMAL"
            style = "RUNNER"      # Let winners run
        
        elif regime == MarketRegime.EVENT_DRIVEN:
            freq = "MINIMAL"      # Wait for clarity
            size = "MINIMAL"      # Very small
            style = "QUICK"       # Fast in/out
        
        elif regime == MarketRegime.LOW_VOLATILITY:
            freq = "REDUCED"      # Fewer opportunities
            size = "NORMAL"
            style = "NORMAL"
        
        return freq, size, style
    
    def is_regime_stable(self, lookback_minutes: int = 30) -> bool:
        """
        Check if regime has been consistent
        Stable regime = higher confidence in adaptations
        """
        if len(self.regime_history) < 3:
            return False
        
        cutoff_time = datetime.now() - timedelta(minutes=lookback_minutes)
        recent_regimes = [r for r in self.regime_history if r.timestamp >= cutoff_time]
        
        if len(recent_regimes) < 2:
            return False
        
        # Check if same regime
        primary_regime = recent_regimes[-1].regime
        same_regime_count = sum(1 for r in recent_regimes if r.regime == primary_regime)
        
        return same_regime_count / len(recent_regimes) >= 0.70  # 70% consistency
    
    def get_regime_change_alert(self) -> Optional[str]:
        """
        Detect if regime just changed (important for adaptation)
        """
        if len(self.regime_history) < 2:
            return None
        
        current = self.regime_history[-1]
        previous = self.regime_history[-2]
        
        if current.regime != previous.regime:
            return (f"🔄 Regime changed: {previous.regime.value} → {current.regime.value} "
                   f"(Adapt: {current.get_posture_description()})")
        
        return None
    
    def get_current_posture(self) -> Dict:
        """Get current regime and recommendations"""
        if not self.current_regime:
            return {
                "regime": "UNKNOWN",
                "confidence": 0.0,
                "recommendations": {
                    "trade_frequency": "NORMAL",
                    "position_size": "NORMAL",
                    "holding_style": "NORMAL"
                }
            }
        
        return {
            "regime": self.current_regime.regime.value,
            "confidence": self.current_regime.confidence,
            "characteristics": self.current_regime.sub_characteristics,
            "recommendations": {
                "trade_frequency": self.current_regime.recommended_trade_frequency,
                "position_size": self.current_regime.recommended_position_size,
                "holding_style": self.current_regime.recommended_holding_style
            },
            "stable": self.is_regime_stable(),
            "description": self.current_regime.get_posture_description()
        }
    
    def should_reduce_trading(self) -> bool:
        """Quick check: should we be more cautious?"""
        if not self.current_regime:
            return False
        
        cautious_regimes = [
            MarketRegime.HIGH_VOLATILITY,
            MarketRegime.CHOPPY,
            MarketRegime.EVENT_DRIVEN
        ]
        
        return self.current_regime.regime in cautious_regimes
    
    def should_allow_runners(self) -> bool:
        """Quick check: should we let winners run?"""
        if not self.current_regime:
            return False
        
        return self.current_regime.recommended_holding_style == "RUNNER"
    
    def get_size_multiplier(self) -> float:
        """
        Get position size multiplier based on regime
        1.0 = normal, <1.0 = reduce, >1.0 = increase (rare)
        """
        if not self.current_regime:
            return 1.0
        
        size_map = {
            "NORMAL": 1.0,
            "REDUCED": 0.7,
            "MINIMAL": 0.5
        }
        
        return size_map.get(self.current_regime.recommended_position_size, 1.0)
    
    def get_frequency_multiplier(self) -> float:
        """
        Get trade frequency multiplier
        1.0 = normal, <1.0 = be more selective
        """
        if not self.current_regime:
            return 1.0
        
        freq_map = {
            "NORMAL": 1.0,
            "REDUCED": 0.7,
            "MINIMAL": 0.5
        }
        
        return freq_map.get(self.current_regime.recommended_trade_frequency, 1.0)
    
    def create_signals_from_market_data(self, market_data: Dict) -> RegimeSignals:
        """
        Helper to create RegimeSignals from market data
        (This would use real market data in production)
        """
        return RegimeSignals(
            price_range_pct=market_data.get('range_pct', 1.0),
            higher_highs=market_data.get('higher_highs', False),
            lower_lows=market_data.get('lower_lows', False),
            vix=market_data.get('vix', 18.0),
            atr_pct=market_data.get('atr_pct', 1.0),
            rate_of_change_5min=market_data.get('roc_5m', 0.0),
            rate_of_change_15min=market_data.get('roc_15m', 0.0),
            oi_imbalance=market_data.get('oi_imbalance', 0.0),
            iv_expansion=market_data.get('iv_expanding', False),
            volume_surge=market_data.get('volume_surge', False),
            timestamp=datetime.now()
        )
