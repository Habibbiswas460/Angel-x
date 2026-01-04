"""
PHASE 4 — FRESH POSITION DETECTOR
"Very Powerful" - Identify Smart Money Entry Points

Detect:
- Sudden OI jump + volume surge (fresh entry)
- First-time activity at strike (new institutional entry)
- Strike migration (ATM zone shift - smart money repositioning)
- Position strength assessment

This is where the SCALPING EDGE lives 🔥

Author: Angel-X Brain Layer
Date: January 4, 2026
Status: Production-Ready
"""

import logging
from typing import Dict, Optional, Tuple, List
from collections import deque
from datetime import datetime, timedelta

from .smart_money_models import (
    FreshPositionSignal,
    SmartMoneyConfig,
)


logger = logging.getLogger(__name__)


class FreshPositionDetector:
    """
    Detect fresh institutional positions entering the market
    
    High-conviction scalping edge based on:
    1. Sudden OI jump (10%+ increase in single snapshot)
    2. Volume surge (2x+ average)
    3. First-time activity (strike never had OI before)
    4. Strike migration (institutional repositioning)
    
    Psychology: Fresh positions = conviction = volatility
    """
    
    def __init__(self, config: Optional[SmartMoneyConfig] = None):
        """Initialize detector"""
        self.config = config or SmartMoneyConfig()
        
        # Track strike activity history
        self.strike_activity_first_seen: Dict[Tuple[float, str], datetime] = {}
        self.strike_max_oi_seen: Dict[Tuple[float, str], int] = {}
        self.strike_creation_time: Dict[Tuple[float, str], datetime] = {}
        
        # Track position strength over time
        self.fresh_position_decay: Dict[Tuple[float, str], float] = {}
        
        # ATM migration tracking
        self.atm_history: deque = deque(maxlen=20)
        
        # Metrics
        self.fresh_positions_detected = 0
        self.high_conviction_positions = 0
        self.migration_detected_count = 0
        self.snapshots_analyzed = 0
    
    def detect_fresh_position(
        self,
        strike: float,
        option_type: str,
        current_oi: int,
        previous_oi: Optional[int],
        current_volume: int,
        previous_volume: Optional[int],
        avg_volume: float,
    ) -> Optional[FreshPositionSignal]:
        """
        Detect if fresh position being established
        
        Returns: FreshPositionSignal if fresh position detected, else None
        """
        
        self.snapshots_analyzed += 1
        key = (strike, option_type)
        
        # Calculate changes
        oi_jump = self._calculate_oi_jump(current_oi, previous_oi)
        volume_surge = self._calculate_volume_surge(current_volume, previous_volume, avg_volume)
        
        # Initialize tracking
        if key not in self.strike_activity_first_seen:
            self.strike_activity_first_seen[key] = datetime.now()
            self.strike_max_oi_seen[key] = current_oi
            self.strike_creation_time[key] = datetime.now()
        
        # Update max OI
        if current_oi > self.strike_max_oi_seen[key]:
            self.strike_max_oi_seen[key] = current_oi
        
        # Check fresh position criteria
        is_fresh = False
        entry_type = ""
        strength = 0.0
        
        # Criterion 1: Sudden OI jump + volume surge
        if (oi_jump >= self.config.fresh_position_oi_jump and
            volume_surge >= self.config.fresh_position_volume_surge):
            
            is_fresh = True
            entry_type = "aggressive_entry"
            strength = min((oi_jump + volume_surge) / 2, 1.0)
            self.fresh_positions_detected += 1
        
        # Criterion 2: First-time activity (OI from 0 to significant)
        if (previous_oi is None or previous_oi < self.config.first_time_oi_threshold) and \
           current_oi >= self.config.first_time_oi_threshold:
            
            is_fresh = True
            entry_type = "first_entry"
            strength = min(current_oi / (self.config.first_time_oi_threshold * 5), 1.0)
            self.fresh_positions_detected += 1
        
        # Criterion 3: Strike becoming active (high volume burst)
        if volume_surge >= self.config.fresh_position_volume_surge and \
           current_oi >= self.config.first_time_oi_threshold:
            
            is_fresh = True
            entry_type = "adjustment"
            strength = min(volume_surge / self.config.fresh_position_volume_surge, 1.0)
        
        if not is_fresh:
            return None
        
        # Calculate expected volatility
        expected_volatility = self._estimate_expected_volatility(
            oi_jump=oi_jump,
            volume_surge=volume_surge,
            current_oi=current_oi,
        )
        
        # Determine confidence
        confidence = self._calculate_confidence(
            oi_jump=oi_jump,
            volume_surge=volume_surge,
            entry_type=entry_type,
        )
        
        signal = FreshPositionSignal(
            is_fresh=True,
            confidence=confidence,
            oi_jump_magnitude=oi_jump,
            volume_surge_magnitude=volume_surge,
            entry_type=entry_type,
            strength=strength,
            expected_volatility=expected_volatility,
            timestamp=datetime.now(),
        )
        
        if confidence > 0.7:
            self.high_conviction_positions += 1
        
        logger.debug(
            f"Fresh position detected at {strike} {option_type}: "
            f"{entry_type} (confidence={confidence:.2f})"
        )
        
        return signal
    
    def detect_strike_migration(
        self,
        current_atm_strike: float,
        previous_atm_strike: Optional[float],
    ) -> Optional[Dict]:
        """
        Detect if smart money is repositioning (ATM zone shifting)
        
        When ATM moves significantly, smart money often repositions
        This is a repositioning signal
        
        Returns: {
            "migrating": bool,
            "direction": "upward" | "downward",
            "magnitude": float,
            "impact": "high" | "medium" | "low",
        } or None
        """
        
        if previous_atm_strike is None:
            self.atm_history.append(current_atm_strike)
            return None
        
        # Calculate ATM shift
        shift = current_atm_strike - previous_atm_strike
        shift_pct = shift / previous_atm_strike if previous_atm_strike != 0 else 0
        
        self.atm_history.append(current_atm_strike)
        
        # Check if significant migration
        if abs(shift_pct) > 0.01:  # >1% ATM shift
            
            self.migration_detected_count += 1
            
            direction = "upward" if shift > 0 else "downward"
            
            # Assess impact
            if abs(shift_pct) > 0.05:
                impact = "high"
            elif abs(shift_pct) > 0.02:
                impact = "medium"
            else:
                impact = "low"
            
            return {
                "migrating": True,
                "direction": direction,
                "magnitude": abs(shift),
                "magnitude_pct": abs(shift_pct),
                "impact": impact,
            }
        
        return None
    
    def get_fresh_position_decay(
        self,
        strike: float,
        option_type: str,
        seconds_elapsed: int,
    ) -> float:
        """
        Get decay factor for fresh position signal over time
        
        Fresh positions lose conviction as time passes
        Returns: 0-1, where 1.0 = full strength, 0.0 = decayed
        """
        
        key = (strike, option_type)
        
        # Check if position still fresh
        if key not in self.strike_activity_first_seen:
            return 0.0
        
        # Exponential decay
        decay_rate = self.config.fresh_position_decay_rate
        decay = decay_rate ** (seconds_elapsed / 60)  # Decay per minute
        
        return max(decay, 0.0)
    
    def is_position_still_fresh(
        self,
        strike: float,
        option_type: str,
        max_age_seconds: int = 300,  # 5 minutes default
    ) -> bool:
        """Check if position signal is still valid"""
        
        key = (strike, option_type)
        
        if key not in self.strike_activity_first_seen:
            return False
        
        age = (datetime.now() - self.strike_activity_first_seen[key]).total_seconds()
        
        if age > max_age_seconds:
            return False
        
        decay = self.get_fresh_position_decay(strike, option_type, int(age))
        
        return decay > 0.3
    
    def get_fresh_positions_in_chain(
        self,
        max_age_seconds: int = 300,
    ) -> List[Tuple[Tuple[float, str], Dict]]:
        """
        Get all currently fresh positions in the chain
        
        Returns: [((strike, option_type), signal_info), ...]
        """
        
        fresh = []
        now = datetime.now()
        
        for key, first_seen_time in self.strike_activity_first_seen.items():
            age = (now - first_seen_time).total_seconds()
            
            if age > max_age_seconds:
                continue
            
            decay = self.get_fresh_position_decay(
                key[0],
                key[1],
                int(age),
            )
            
            if decay > 0.3:
                fresh.append((
                    key,
                    {
                        "age_seconds": int(age),
                        "decay_factor": decay,
                        "max_oi_seen": self.strike_max_oi_seen.get(key, 0),
                    },
                ))
        
        return sorted(fresh, key=lambda x: x[1]["age_seconds"])
    
    def get_primary_fresh_entry(
        self,
        max_age_seconds: int = 300,
    ) -> Optional[Tuple[float, str]]:
        """
        Get single strike with freshest/strongest position
        
        Use this for focused scalping on one setup at a time
        """
        
        fresh_list = self.get_fresh_positions_in_chain(max_age_seconds)
        
        if not fresh_list:
            return None
        
        # Return youngest (freshest)
        return fresh_list[0][0]
    
    def reset(self):
        """Reset all state"""
        self.strike_activity_first_seen.clear()
        self.strike_max_oi_seen.clear()
        self.strike_creation_time.clear()
        self.fresh_position_decay.clear()
        self.atm_history.clear()
        self.fresh_positions_detected = 0
        self.high_conviction_positions = 0
        self.migration_detected_count = 0
        self.snapshots_analyzed = 0
    
    # ========================================================================
    # PRIVATE HELPERS
    # ========================================================================
    
    def _calculate_oi_jump(
        self,
        current_oi: int,
        previous_oi: Optional[int],
    ) -> float:
        """Calculate OI jump as percentage (0-1 for normal, >1 for extreme)"""
        
        if previous_oi is None or previous_oi == 0:
            # Assume baseline of 1000
            baseline = 1000
            if current_oi > baseline:
                return (current_oi - baseline) / baseline
            else:
                return 0.0
        
        return (current_oi - previous_oi) / previous_oi
    
    def _calculate_volume_surge(
        self,
        current_volume: int,
        previous_volume: Optional[int],
        avg_volume: float,
    ) -> float:
        """Calculate volume surge as ratio (1.0 = no change)"""
        
        if current_volume == 0:
            return 0.0
        
        if previous_volume is not None and previous_volume > 0:
            return current_volume / previous_volume
        elif avg_volume > 0:
            return current_volume / avg_volume
        else:
            return 1.0
    
    def _estimate_expected_volatility(
        self,
        oi_jump: float,
        volume_surge: float,
        current_oi: int,
    ) -> float:
        """
        Estimate expected volatility from position entry
        
        Higher OI jump + higher volume = more volatility expected
        Returns: 0-1
        """
        
        # Normalize inputs
        oi_factor = min(oi_jump, 1.0)  # Cap at 100% change
        vol_factor = min((volume_surge - 1.0) / 2.0, 1.0)  # Normalize surge
        
        # Size factor
        size_factor = min(current_oi / 5000, 1.0)  # Normalize OI size
        
        # Average all factors
        expected_vol = (oi_factor + vol_factor + size_factor) / 3
        
        return min(expected_vol, 1.0)
    
    def _calculate_confidence(
        self,
        oi_jump: float,
        volume_surge: float,
        entry_type: str,
    ) -> float:
        """
        Calculate confidence in fresh position detection
        Returns: 0-1
        """
        
        base = 0.5
        
        # OI jump contribution (max +0.3)
        oi_component = min(oi_jump / 0.3, 1.0) * 0.3
        
        # Volume surge contribution (max +0.3)
        vol_component = min((volume_surge - 1.0) / 2.0, 1.0) * 0.3
        
        # Entry type boost (max +0.1)
        type_bonus = {
            "aggressive_entry": 0.1,
            "first_entry": 0.1,
            "adjustment": 0.05,
        }.get(entry_type, 0.0)
        
        confidence = base + oi_component + vol_component + type_bonus
        
        return min(confidence, 1.0)
    
    def get_metrics(self) -> Dict:
        """Get detector metrics"""
        
        return {
            "snapshots_analyzed": self.snapshots_analyzed,
            "fresh_positions_detected": self.fresh_positions_detected,
            "high_conviction_positions": self.high_conviction_positions,
            "migrations_detected": self.migration_detected_count,
            "strikes_tracked": len(self.strike_activity_first_seen),
            "detection_rate": (
                self.fresh_positions_detected / max(self.snapshots_analyzed, 1) * 100
            ),
        }
