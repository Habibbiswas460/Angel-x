"""
PHASE 7 — DYNAMIC TRAILING SL ENGINE

Greeks-based trailing logic
Profit protection without fixed TP
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from src.utils.exit_models import (
    TrailingSLState, TrailTrigger, Phase7Config
)


class DynamicTrailingSLEngine:
    """
    Intelligent trailing SL based on structure (not just price)
    
    Philosophy:
    - Trail when momentum continues (delta strong)
    - Trail aggressively when gamma peaks (structure exhaustion coming)
    - Relax when momentum dies (tighten for safety)
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
    
    # ====================================================================
    # STEP 1: TRAIL ACTIVATION
    # ====================================================================
    
    def check_trail_activation(
        self,
        entry_price: float,
        current_price: float,
        entry_delta: float,
        current_delta: float,
        profit_percent: float,
    ) -> Tuple[bool, Optional[TrailTrigger], str]:
        """
        Check if should activate trailing SL
        Returns: (should_activate, trigger_reason, message)
        """
        
        # Rule 1: Profit threshold
        if profit_percent < self.config.trail_activation_profit_percent:
            return False, None, f"Profit {profit_percent:.2f}% < threshold"
        
        # Rule 2: Delta strong & continuing
        delta_strengthening = abs(current_delta) > abs(entry_delta)
        if delta_strengthening and abs(current_delta) > 0.6:
            return True, TrailTrigger.DELTA_STRONG, "Delta strong & continuing"
        
        # Rule 3: Already profitable + delta positive
        if profit_percent > 0.3 and abs(current_delta) > 0.5:
            return True, TrailTrigger.MOMENTUM_ACCELERATING, "Momentum accelerating"
        
        return False, None, "Not ready to trail"
    
    # ====================================================================
    # STEP 2: TRAIL CALCULATION (WHERE TO SET SL)
    # ====================================================================
    
    def calculate_trail_sl(
        self,
        current_price: float,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        option_type: str,
        trail_trigger: TrailTrigger,
    ) -> float:
        """
        Calculate where trailing SL should be
        
        Logic:
        - For CE: SL = current - trail_distance
        - For PE: SL = current + trail_distance
        
        But adjust trail_distance based on Greeks structure
        """
        
        base_trail = self.config.trail_distance_points
        
        # Adjust trail distance based on trigger
        if trail_trigger == TrailTrigger.GAMMA_PEAK:
            # Gamma at peak = reversal likely → tighten trail
            if current_gamma > 0.015:
                adjusted_trail = max(5.0, base_trail * 0.7)  # Tighter
            else:
                adjusted_trail = base_trail
        
        elif trail_trigger == TrailTrigger.MOMENTUM_DECELERATING:
            # Momentum dying → aggressive trail
            adjusted_trail = max(5.0, base_trail * 0.6)  # Much tighter
        
        elif trail_trigger == TrailTrigger.MOMENTUM_ACCELERATING:
            # Momentum strong → wider trail
            adjusted_trail = base_trail * 1.2  # Wider
        
        else:
            adjusted_trail = base_trail
        
        # Calculate SL based on option type
        if option_type == "CE":
            # For CE: current price - trail
            trail_sl = current_price - adjusted_trail
        else:  # PE
            # For PE: current price + trail
            trail_sl = current_price + adjusted_trail
        
        return trail_sl
    
    # ====================================================================
    # STEP 3: TRAIL UPDATE (MOVEMENT)
    # ====================================================================
    
    def update_trail(
        self,
        current_trail_state: TrailingSLState,
        current_price: float,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        option_type: str,
    ) -> Tuple[TrailingSLState, bool, str]:
        """
        Update trailing SL position
        Returns: (updated_state, moved, reason)
        """
        
        if not current_trail_state.trail_activated():
            return current_trail_state, False, "Trail not active"
        
        # Calculate new trail SL
        new_trail_sl = self.calculate_trail_sl(
            current_price=current_price,
            current_delta=current_delta,
            current_gamma=current_gamma,
            current_theta=current_theta,
            option_type=option_type,
            trail_trigger=current_trail_state.trail_trigger or TrailTrigger.DELTA_STRONG,
        )
        
        old_trail_sl = current_trail_state.current_trail_sl
        
        # Determine movement
        if option_type == "CE":
            # For CE: trail can only go UP (profit protection)
            if new_trail_sl > old_trail_sl:
                moved = True
                reason = f"Trail moved UP: {old_trail_sl:.1f} → {new_trail_sl:.1f}"
                current_trail_state.times_tightened += 1
            else:
                moved = False
                reason = "SL would move down (not allowed)"
        else:  # PE
            # For PE: trail can only go DOWN
            if new_trail_sl < old_trail_sl:
                moved = True
                reason = f"Trail moved DOWN: {old_trail_sl:.1f} → {new_trail_sl:.1f}"
                current_trail_state.times_tightened += 1
            else:
                moved = False
                reason = "SL would move up (not allowed)"
        
        if moved:
            current_trail_state.current_trail_sl = new_trail_sl
            current_trail_state.last_updated = datetime.now()
            
            # Track max profit locked
            if current_trail_state.activation_price is not None:
                profit_locked = abs(current_trail_state.activation_price - new_trail_sl)
                current_trail_state.max_trail_gained = max(
                    current_trail_state.max_trail_gained,
                    profit_locked
                )
        
        return current_trail_state, moved, reason
    
    # ====================================================================
    # STEP 4: TRAIL TIGHTENING (EMERGENCY)
    # ====================================================================
    
    def should_tighten_aggressive(
        self,
        current_gamma: float,
        gamma_prev: float,
        volume_current: int,
        volume_prev: int,
        current_delta: float,
    ) -> Tuple[bool, str]:
        """
        Emergency tightening: market showing exhaustion signs
        """
        
        # Sign 1: Gamma collapsing
        if gamma_prev > 0.015 and current_gamma < 0.005:
            return True, "Gamma collapse - tighten"
        
        # Sign 2: Volume spike then dry
        if volume_current > volume_prev * 2 and volume_current > 10000:
            return True, "Volume climax - tighten"
        
        # Sign 3: Delta weakening
        if abs(current_delta) < 0.3:
            return True, "Delta weak - tighten"
        
        return False, "No emergency tightening needed"
    
    # ====================================================================
    # STEP 5: CHECK TRAIL HIT
    # ====================================================================
    
    def check_trail_hit(
        self,
        current_price: float,
        current_trail_state: TrailingSLState,
        option_type: str,
    ) -> Tuple[bool, str]:
        """
        Check if trailing SL has been hit
        """
        
        if not current_trail_state.trail_activated():
            return False, "Trail not active"
        
        trail_sl = current_trail_state.current_trail_sl
        
        if option_type == "CE":
            # For CE: exit if price <= trail SL
            hit = current_price <= trail_sl
            reason = f"CE price {current_price:.1f} <= trail SL {trail_sl:.1f}"
        else:  # PE
            # For PE: exit if price >= trail SL
            hit = current_price >= trail_sl
            reason = f"PE price {current_price:.1f} >= trail SL {trail_sl:.1f}"
        
        return hit, reason if hit else "Trail SL not hit"
    
    # ====================================================================
    # DIAGNOSTICS
    # ====================================================================
    
    def get_trail_status(
        self,
        trail_state: TrailingSLState,
    ) -> dict:
        """Get trailing SL diagnostics"""
        
        return {
            "is_active": trail_state.is_active,
            "activation_time": trail_state.activation_time,
            "current_trail_sl": trail_state.current_trail_sl,
            "trail_distance": trail_state.trail_distance_points,
            "times_tightened": trail_state.times_tightened,
            "max_profit_locked": trail_state.max_trail_gained,
            "trigger": trail_state.trail_trigger.value if trail_state.trail_trigger else None,
            "reason": trail_state.reason,
        }
