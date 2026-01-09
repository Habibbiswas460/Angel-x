"""
Compatibility shim: use the canonical `src.core.risk_manager` implementation.
Keeps all risk limits, veto logic, and Greeks checks centralized.
"""

from src.core.risk_manager import RiskManager, GreeksLimits

__all__ = ["RiskManager", "GreeksLimits"]
    
    def get_remaining_loss_capacity(self):
        """Get remaining loss capacity before hitting limit"""
        with self.risk_lock:
            return max(0, self.max_daily_loss + self.daily_pnl)
