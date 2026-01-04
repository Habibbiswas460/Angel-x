"""
PHASE 4 — OI BUILD-UP CLASSIFIER
Institutional State Detection

Classify each strike into 4 institutional states:
- LONG_BUILD_UP: Price ↑ | OI ↑ | Vol ↑ (High conviction)
- SHORT_BUILD_UP: Price ↓ | OI ↑ | Vol ↑ (High conviction)
- SHORT_COVERING: Price ↑ | OI ↓ | Vol ↑
- LONG_UNWINDING: Price ↓ | OI ↓ | Vol ↑

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from collections import deque

from .smart_money_models import (
    OiBuildUpType,
    VolumeState,
    StrikeLevelIntelligence,
    SmartMoneyConfig,
    OiVolumeHistory,
    validate_buildup_type,
    is_high_conviction_buildup,
)


logger = logging.getLogger(__name__)


class OiBuildUpClassifier:
    """
    Classifies strikes into institutional build-up states
    
    Core Logic:
    Price ↑ + OI ↑ + Volume ↑ = Long Build-Up (Bullish conviction)
    Price ↓ + OI ↑ + Volume ↑ = Short Build-Up (Bearish conviction)
    Price ↑ + OI ↓ + Volume ↑ = Short Covering (Mixed signal)
    Price ↓ + OI ↓ + Volume ↑ = Long Unwinding (Mixed signal)
    
    Strategy: Trade only HIGH_CONVICTION states (first two)
    """
    
    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize classifier with configuration"""
        self.config = config or SmartMoneyConfig()
        self.strike_history: Dict[Tuple[float, str], OiVolumeHistory] = {}
        self.classification_history: Dict[Tuple[float, str], deque] = {}
        
        # Metrics
        self.classifications_made = 0
        self.long_buildup_count = 0
        self.short_buildup_count = 0
        self.short_covering_count = 0
        self.long_unwinding_count = 0
        self.neutral_count = 0
    
    def classify_strike(
        self,
        strike: float,
        option_type: str,
        current_price: float,
        previous_price: Optional[float],
        current_oi: int,
        previous_oi: Optional[int],
        current_volume: int,
        previous_volume: Optional[int],
    ) -> Tuple[OiBuildUpType, float]:
        """
        Classify a single strike's build-up type
        
        Returns: (buildup_type, confidence)
        confidence = 0-1, higher = more certain
        """
        
        # Calculate changes
        price_change = self._calculate_price_change(current_price, previous_price)
        oi_change = self._calculate_oi_change(current_oi, previous_oi)
        volume_change = self._calculate_volume_change(current_volume, previous_volume)
        
        # Store in history
        key = (strike, option_type)
        if key not in self.strike_history:
            self.strike_history[key] = OiVolumeHistory(
                strike=strike,
                option_type=option_type,
            )
        
        self.strike_history[key].add_snapshot(current_oi, current_volume, current_price)
        
        # Classify
        buildup_type = validate_buildup_type(
            price_change=price_change,
            oi_change=oi_change,
            volume_change=volume_change,
            config=self.config,
        )
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            price_change=price_change,
            oi_change=oi_change,
            volume_change=volume_change,
            buildup_type=buildup_type,
        )
        
        # Update metrics
        self._update_metrics(buildup_type)
        
        # Store in history
        if key not in self.classification_history:
            self.classification_history[key] = deque(maxlen=20)
        self.classification_history[key].append({
            "type": buildup_type,
            "confidence": confidence,
            "timestamp": datetime.now(),
        })
        
        logger.debug(
            f"Strike {strike} {option_type}: {buildup_type.value} "
            f"(confidence={confidence:.2f})"
        )
        
        return buildup_type, confidence
    
    def get_strike_classification(
        self,
        strike: float,
        option_type: str,
    ) -> Optional[Tuple[OiBuildUpType, float]]:
        """Get current classification for strike"""
        key = (strike, option_type)
        if key not in self.classification_history:
            return None
        
        history = self.classification_history[key]
        if not history:
            return None
        
        latest = history[-1]
        return latest["type"], latest["confidence"]
    
    def get_high_conviction_strikes(self) -> Dict[Tuple[float, str], float]:
        """
        Get all strikes currently in high conviction build-up
        
        Returns: {(strike, option_type): confidence, ...}
        """
        high_conviction = {}
        
        for (strike, option_type), history in self.classification_history.items():
            if not history:
                continue
            
            latest = history[-1]
            if is_high_conviction_buildup(latest["type"]):
                high_conviction[(strike, option_type)] = latest["confidence"]
        
        return high_conviction
    
    def get_buildup_dominance(self) -> Dict[str, int]:
        """
        Get count of each build-up type across all strikes
        
        Returns: {
            "long_buildup": count,
            "short_buildup": count,
            "short_covering": count,
            "long_unwinding": count,
            "neutral": count,
        }
        """
        return {
            "long_buildup": self.long_buildup_count,
            "short_buildup": self.short_buildup_count,
            "short_covering": self.short_covering_count,
            "long_unwinding": self.long_unwinding_count,
            "neutral": self.neutral_count,
        }
    
    def get_primary_buildup_type(self) -> Optional[OiBuildUpType]:
        """
        Determine dominant build-up type across chain
        
        Returns: Most common type, or None if no clear dominance
        """
        if not self.classification_history:
            return None
        
        type_counts = {}
        for history in self.classification_history.values():
            if history:
                latest_type = history[-1]["type"]
                type_counts[latest_type] = type_counts.get(latest_type, 0) + 1
        
        if not type_counts:
            return None
        
        # Get most common
        dominant_type = max(type_counts, key=type_counts.get)
        
        # Check if it's actually dominant (>30% of strikes)
        total_classified = sum(type_counts.values())
        if type_counts[dominant_type] / total_classified > 0.3:
            return dominant_type
        
        return None
    
    def get_strike_history_trend(
        self,
        strike: float,
        option_type: str,
    ) -> Optional[str]:
        """
        Analyze historical trend for a strike
        
        Returns: "consistent", "changing", "unstable", None
        """
        key = (strike, option_type)
        if key not in self.classification_history:
            return None
        
        history = self.classification_history[key]
        if len(history) < 3:
            return None
        
        # Get last 3 classifications
        recent = [h["type"] for h in list(history)[-3:]]
        
        # Check consistency
        if recent[0] == recent[1] == recent[2]:
            return "consistent"
        elif recent[-1] != recent[0]:
            return "changing"
        else:
            return "unstable"
    
    def reset(self):
        """Reset all state"""
        self.strike_history.clear()
        self.classification_history.clear()
        self.classifications_made = 0
        self.long_buildup_count = 0
        self.short_buildup_count = 0
        self.short_covering_count = 0
        self.long_unwinding_count = 0
        self.neutral_count = 0
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _calculate_price_change(
        self,
        current: float,
        previous: Optional[float],
    ) -> float:
        """Calculate price change as percentage"""
        if previous is None or previous == 0:
            return 0.0
        return (current - previous) / previous
    
    def _calculate_oi_change(
        self,
        current: int,
        previous: Optional[int],
    ) -> float:
        """Calculate OI change as percentage"""
        if previous is None or previous == 0:
            return 0.0
        return (current - previous) / previous
    
    def _calculate_volume_change(
        self,
        current: int,
        previous: Optional[int],
    ) -> float:
        """Calculate volume change as ratio"""
        if previous is None or previous == 0:
            return 1.0
        return current / previous
    
    def _calculate_confidence(
        self,
        price_change: float,
        oi_change: float,
        volume_change: float,
        buildup_type: OiBuildUpType,
    ) -> float:
        """
        Calculate confidence in classification (0-1)
        
        Higher confidence when:
        - Price, OI, Volume all move together
        - Movements are large
        - Direction is unambiguous
        """
        
        if buildup_type == OiBuildUpType.NEUTRAL:
            return 0.3
        
        if buildup_type == OiBuildUpType.INSUFFICIENT_DATA:
            return 0.0
        
        # Base confidence from movement alignment
        base = 0.5
        
        # Price movement strength (max +0.2)
        price_strength = min(abs(price_change), 0.1) / 0.1 * 0.2
        
        # OI movement strength (max +0.2)
        oi_strength = min(abs(oi_change), 0.15) / 0.15 * 0.2
        
        # Volume confirmation (max +0.2)
        volume_strength = min(abs(volume_change - 1.0), 1.0) / 1.0 * 0.2
        
        confidence = base + price_strength + oi_strength + volume_strength
        return min(confidence, 1.0)
    
    def _update_metrics(self, buildup_type: OiBuildUpType):
        """Update classification counts"""
        self.classifications_made += 1
        
        if buildup_type == OiBuildUpType.LONG_BUILD_UP:
            self.long_buildup_count += 1
        elif buildup_type == OiBuildUpType.SHORT_BUILD_UP:
            self.short_buildup_count += 1
        elif buildup_type == OiBuildUpType.SHORT_COVERING:
            self.short_covering_count += 1
        elif buildup_type == OiBuildUpType.LONG_UNWINDING:
            self.long_unwinding_count += 1
        else:
            self.neutral_count += 1
    
    def get_metrics(self) -> Dict:
        """Get classifier metrics"""
        total = self.classifications_made
        
        return {
            "total_classifications": total,
            "long_buildup": self.long_buildup_count,
            "short_buildup": self.short_buildup_count,
            "short_covering": self.short_covering_count,
            "long_unwinding": self.long_unwinding_count,
            "neutral": self.neutral_count,
            "high_conviction_percentage": (
                (self.long_buildup_count + self.short_buildup_count) / max(total, 1) * 100
            ),
        }
