"""
PHASE 7 — COOLDOWN LOGIC

Psychology reset between trades
Win → quick back in
Loss → wait (avoid revenge)
High volatility → longer break
"""

from datetime import datetime, timedelta
from typing import Optional, Tuple
from enum import Enum
from src.utils.exit_models import CooldownReason, Phase7Config


class CooldownState(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    NEVER_STARTED = "never"


class CooldownLogicEngine:
    """
    Post-trade cooldown management
    
    Trader psychology:
    - Win: Confidence up, quick re-entry OK
    - Loss: Emotions high, need cooling
    - Big move: Volatility up, take break
    - System stress: Multiple losses, longer break
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
        self.last_trade_exit_time: Optional[datetime] = None
        self.last_trade_pnl: float = 0.0
        self.cooldown_start: Optional[datetime] = None
        self.cooldown_duration: int = 0
        self.cooldown_reason: Optional[CooldownReason] = None
        self.consecutive_losses: int = 0
    
    # ====================================================================
    # STEP 1: DETERMINE COOLDOWN PERIOD
    # ====================================================================
    
    def calculate_cooldown_period(
        self,
        exit_pnl: float,
        volatility_index: float,
        consecutive_losses_count: int = 0,
        market_condition: str = "normal",
    ) -> Tuple[int, CooldownReason, str]:
        """
        Calculate cooldown time based on trade outcome
        
        Returns: (cooldown_seconds, reason, explanation)
        """
        
        # Base: 30 seconds
        base_cooldown = 30
        
        # ---- PROFITABLE TRADE ----
        if exit_pnl > 0:
            # Win = confidence up, quick re-entry
            cooldown = int(base_cooldown * 0.5)  # 15 seconds
            return cooldown, CooldownReason.PROFITABLE_TRADE, \
                   f"Win! Quick re-entry in {cooldown}s"
        
        # ---- LOSING TRADE ----
        else:
            # Loss = emotions high, need reset
            base_loss = int(base_cooldown * 2.0)  # 60 seconds
            
            # Add penalty for consecutive losses
            if consecutive_losses_count > 0:
                loss_penalty = consecutive_losses_count * 30
                base_loss += loss_penalty
                reason = CooldownReason.LOSING_TRADE
                explanation = f"Loss #{consecutive_losses_count + 1}: cooldown {base_loss}s"
            else:
                reason = CooldownReason.LOSING_TRADE
                explanation = f"First loss: reset in {base_loss}s"
            
            return base_loss, reason, explanation
        
    def calculate_volatility_cooldown(
        self,
        volatility_index: float,
    ) -> Tuple[int, str]:
        """
        Additional cooldown for high volatility
        """
        
        base = 30
        
        # Low vol: 30s (normal)
        if volatility_index < 15:
            return base, "Low volatility"
        
        # Normal vol: 30s
        elif volatility_index < 20:
            return base, "Normal volatility"
        
        # High vol: 60s
        elif volatility_index < 25:
            return int(base * 2), "High volatility - extended cooldown"
        
        # Extreme vol: 120s
        else:
            return int(base * 4), f"Extreme volatility ({volatility_index:.1f}) - long break"
    
    def calculate_system_stress_cooldown(
        self,
        num_consecutive_losses: int,
        num_consecutive_wins: int,
    ) -> Tuple[int, CooldownReason, str]:
        """
        Additional cooldown for system stress
        
        - 3+ losses: emotional overload
        - After big wins: greed management
        """
        
        # Consecutive losses = emotional overload
        if num_consecutive_losses >= 3:
            stress_cooldown = 180  # 3 minutes
            return stress_cooldown, CooldownReason.SYSTEM_STRESS, \
                   f"3+ losses: psychological reset in {stress_cooldown}s"
        
        # Back-to-back wins (>5) = greed management
        if num_consecutive_wins > 5:
            stress_cooldown = 120  # 2 minutes
            return stress_cooldown, CooldownReason.SYSTEM_STRESS, \
                   f"Greed check: {num_consecutive_wins} wins, cool down {stress_cooldown}s"
        
        return 0, CooldownReason.PROFITABLE_TRADE, "Normal operation"
    
    # ====================================================================
    # STEP 2: START & MONITOR COOLDOWN
    # ====================================================================
    
    def start_cooldown(
        self,
        exit_pnl: float,
        volatility_index: float,
        current_time: datetime,
        consecutive_losses: int = 0,
        market_condition: str = "normal",
    ) -> Tuple[bool, str]:
        """
        Start cooldown period after trade exit
        """
        
        # Calculate base cooldown
        base_cooldown, base_reason, base_msg = self.calculate_cooldown_period(
            exit_pnl, volatility_index, consecutive_losses, market_condition
        )
        
        # Calculate vol adjustment
        vol_cooldown, vol_msg = self.calculate_volatility_cooldown(volatility_index)
        
        # Calculate stress adjustment
        stress_cooldown, stress_reason, stress_msg = \
            self.calculate_system_stress_cooldown(consecutive_losses, 0)
        
        # Use maximum
        final_cooldown = max(base_cooldown, vol_cooldown, stress_cooldown)
        
        # Store cooldown
        self.cooldown_start = current_time
        self.cooldown_duration = final_cooldown
        self.last_trade_pnl = exit_pnl
        self.last_trade_exit_time = current_time
        
        if consecutive_losses > 0:
            self.consecutive_losses = consecutive_losses
        
        reason = stress_reason if stress_cooldown > 0 else base_reason
        self.cooldown_reason = reason
        
        msg = f"Cooldown started: {final_cooldown}s | {base_msg} | {stress_msg}"
        return True, msg
    
    # ====================================================================
    # STEP 3: CHECK IF COOLDOWN ACTIVE
    # ====================================================================
    
    def is_in_cooldown(self, current_time: datetime) -> Tuple[bool, int, str]:
        """
        Check if currently in cooldown period
        Returns: (in_cooldown, time_remaining_secs, reason)
        """
        
        if self.cooldown_start is None:
            return False, 0, "Cooldown never started"
        
        elapsed = (current_time - self.cooldown_start).total_seconds()
        remaining = self.cooldown_duration - elapsed
        
        if remaining > 0:
            return True, int(remaining), \
                   f"In cooldown: {int(remaining)}s remaining (reason: {self.cooldown_reason.value})"
        else:
            return False, 0, "Cooldown expired"
    
    def get_cooldown_status(self, current_time: datetime) -> Tuple[CooldownState, int, str]:
        """
        Get detailed cooldown status
        """
        
        if self.cooldown_start is None:
            return CooldownState.NEVER_STARTED, 0, "No cooldown initiated"
        
        elapsed = (current_time - self.cooldown_start).total_seconds()
        
        if elapsed < self.cooldown_duration:
            remaining = int(self.cooldown_duration - elapsed)
            percent = (elapsed / self.cooldown_duration) * 100
            return CooldownState.ACTIVE, remaining, \
                   f"Cooldown active: {remaining}s ({percent:.0f}% complete)"
        else:
            return CooldownState.EXPIRED, 0, "Cooldown expired"
    
    # ====================================================================
    # STEP 4: RESET COOLDOWN
    # ====================================================================
    
    def reset_cooldown(self, reason: str = "Manual reset") -> str:
        """
        Reset cooldown (typically when re-entering trade)
        """
        
        self.cooldown_start = None
        self.cooldown_duration = 0
        self.cooldown_reason = None
        return f"Cooldown reset: {reason}"
    
    def can_trade_now(self, current_time: datetime) -> Tuple[bool, str]:
        """
        Simple check: can we trade now?
        """
        
        in_cooldown, remaining, msg = self.is_in_cooldown(current_time)
        
        if in_cooldown:
            return False, f"Still cooling: {remaining}s remaining"
        
        return True, "Cooldown over - ready to trade"
    
    # ====================================================================
    # STEP 5: MARKET CONDITION MODIFIER
    # ====================================================================
    
    def adjust_for_market_condition(
        self,
        current_cooldown: int,
        market_condition: str,
    ) -> int:
        """
        Adjust cooldown for market conditions
        """
        
        # High vol: extend cooldown
        if market_condition == "high_volatility":
            return int(current_cooldown * 1.5)
        
        # Trending: relax cooldown (profit-friendly)
        elif market_condition == "strong_trend":
            return int(current_cooldown * 0.7)
        
        # Choppy: extend cooldown (avoid chop)
        elif market_condition == "choppy":
            return int(current_cooldown * 1.8)
        
        # Normal
        else:
            return current_cooldown
