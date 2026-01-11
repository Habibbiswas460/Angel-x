"""
PHASE 7 — PARTIAL EXIT ENGINE

Lock profit on first impulse
Rest runs with tight SL
Free-trade mindset
"""

from datetime import datetime
from typing import Optional, Tuple
from src.utils.exit_models import (
    PartialExitState, PartialExitSignal, Phase7Config
)


class PartialExitEngine:
    """
    Partial profit taking strategy:
    
    Theory:
    - First impulse = 60-70% move is done
    - Take 60% quantity at first target
    - Run remaining 40% with tight SL
    - Zero emotion on remaining portion
    
    Psychology:
    - Locks profit (reduces regret)
    - Lets winner run (captures big move)
    - Shifts to mechanical mode
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
    
    # ====================================================================
    # STEP 1: CHECK PARTIAL EXIT ELIGIBILITY
    # ====================================================================
    
    def check_partial_exit_eligibility(
        self,
        entry_price: float,
        current_price: float,
        current_gamma: float,
        gamma_prev: float,
        volume_current: int,
        volume_prev: int,
        option_type: str,
    ) -> Tuple[bool, Optional[PartialExitSignal], str]:
        """
        Check if first impulse is done → eligible for partial exit
        """
        
        # Calculate profit
        profit_percent = self._calculate_profit_percent(
            entry_price, current_price, option_type
        )
        
        # Rule 1: Profit threshold
        if profit_percent < self.config.partial_exit_profit_percent:
            return False, None, f"Profit {profit_percent:.2f}% < threshold"
        
        # Rule 2: Gamma flattening (structure exhaustion)
        if gamma_prev > 0.01 and current_gamma < 0.008:
            return True, PartialExitSignal.GAMMA_FLATTENING, "Gamma flattening - take partial"
        
        # Rule 3: First impulse done (price move slowing)
        move_size = abs(current_price - entry_price)
        if move_size > 2.0 and current_gamma < 0.01:
            return True, PartialExitSignal.FIRST_IMPULSE_DONE, "First impulse complete"
        
        # Rule 4: Volume drop (momentum fading)
        if volume_prev > 0 and volume_current < volume_prev * 0.5:
            return True, PartialExitSignal.VOLUME_DROP, "Volume dropping - take profit"
        
        # Rule 5: Profit threshold hit
        if profit_percent > 1.0:
            return True, PartialExitSignal.PROFIT_THRESHOLD, "Hit 1% profit target"
        
        return False, None, "Not eligible for partial exit"
    
    # ====================================================================
    # STEP 2: CALCULATE PARTIAL EXIT SIZES
    # ====================================================================
    
    def calculate_partial_exit_sizes(
        self,
        total_quantity: int,
        entry_price: float,
        current_price: float,
        current_delta: float,
    ) -> Tuple[int, int, float, float, str]:
        """
        Calculate how much to exit vs keep running
        
        Returns: (exit_qty, remaining_qty, exit_price, new_sl, reasoning)
        """
        
        # Calculate exit quantity (60% of total)
        exit_qty = max(1, int(total_quantity * self.config.partial_exit_quantity_percent))
        remaining_qty = total_quantity - exit_qty
        
        # Exit at current price
        exit_price = current_price
        
        # For remaining: tight SL (5-10 pts behind)
        # Calculate based on delta weakness
        if abs(current_delta) > 0.6:
            new_sl = current_price - 8.0  # Tight
            reasoning = f"Exit {exit_qty}@{exit_price:.1f}, keep {remaining_qty} with tight SL {new_sl:.1f}"
        else:
            new_sl = current_price - 5.0  # Very tight
            reasoning = f"Delta weak, exit {exit_qty}@{exit_price:.1f}, tight SL {new_sl:.1f}"
        
        return exit_qty, remaining_qty, exit_price, new_sl, reasoning
    
    # ====================================================================
    # STEP 3: CALCULATE PARTIAL EXIT PROFIT
    # ====================================================================
    
    def calculate_exit_pnl(
        self,
        quantity: int,
        entry_price: float,
        exit_price: float,
    ) -> float:
        """Calculate P&L from exit"""
        point_diff = exit_price - entry_price
        return point_diff * quantity * 100  # 1 point = ₹100 per contract
    
    # ====================================================================
    # STEP 4: REMAINING POSITION MANAGEMENT
    # ====================================================================
    
    def get_remaining_position_rules(
        self,
        remaining_qty: int,
        entry_price: float,
        profit_locked_from_partial: float,
    ) -> dict:
        """
        Rules for remaining position (free-trade)
        """
        
        return {
            "quantity": remaining_qty,
            "entry_price": entry_price,
            "mentality": "Free trade - rest is house money",
            "sl_type": "tight trailing",
            "exit_targets": ["target hit", "reversal", "time limit"],
            "psychology": "No emotion, mechanical exits",
            "profit_locked": profit_locked_from_partial,
            "rules": [
                "Exit on any reversal signal",
                "Exit on exhaustion detection",
                "Exit on time limit",
                "Trail SL aggressively",
            ]
        }
    
    # ====================================================================
    # HELPER METHODS
    # ====================================================================
    
    def _calculate_profit_percent(
        self,
        entry_price: float,
        current_price: float,
        option_type: str,
    ) -> float:
        """Calculate profit percentage"""
        if entry_price == 0:
            return 0.0
        
        if option_type == "CE":
            # CE profit = price up
            change = current_price - entry_price
        else:
            # PE profit = price down
            change = entry_price - current_price
        
        return (change / entry_price) * 100
    
    # ====================================================================
    # DIAGNOSTICS
    # ====================================================================
    
    def get_partial_exit_status(
        self,
        state: PartialExitState,
    ) -> dict:
        """Get partial exit status"""
        
        return {
            "is_eligible": state.is_eligible,
            "first_exit_taken": state.first_exit_taken,
            "exit_quantity": state.first_exit_quantity,
            "exit_price": state.first_exit_price,
            "exit_pnl": state.first_exit_pnl,
            "remaining_qty": state.remaining_quantity,
            "remaining_pnl": state.remaining_pnl,
            "signal": state.signal_reason.value if state.signal_reason else None,
            "confidence": state.confidence,
        }
