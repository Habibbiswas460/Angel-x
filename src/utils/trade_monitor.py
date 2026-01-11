"""
PHASE 6 — TRADE MONITORING + RISK MANAGEMENT ENGINE

Real-time monitoring during active trade:
- Greeks reversal detection
- OI unwinding
- Volume dry-up
- Time decay pressure
- Force exit triggers
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Tuple, Optional, List
from src.utils.trade_models import (
    ActiveTrade, TradeMonitorUpdate, ExitReason,
    Phase6Config, RiskLimitStatus
)


# ============================================================================
# TRADE MONITORING ENGINE
# ============================================================================

class TradeMonitoringEngine:
    """Real-time monitoring of active trades"""
    
    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()
        self.active_trades: dict = {}
        self.monitoring_alerts: list = []
    
    def update_trade_monitoring(
        self,
        trade: ActiveTrade,
        update: TradeMonitorUpdate,
    ) -> List[Tuple[bool, str]]:  # (should_exit, reason)
        """
        Update trade monitoring and check for exit triggers
        Returns: list of (should_exit, reason) tuples
        """
        
        alerts = []
        
        # Update current data
        trade.current_ltp = update.current_ltp
        trade.delta_current = update.delta_ce or update.delta_pe  # Use CE or PE delta
        trade.gamma_current = update.gamma_ce or update.gamma_pe  # Use CE or PE gamma
        trade.theta_current = update.theta_ce or update.theta_pe  # Use CE or PE theta
        
        # Check for exit triggers
        
        # 1. Delta flip
        if self._check_delta_flip(trade):
            alerts.append((True, "Delta flip detected → Exit"))
        
        # 2. Gamma exhaustion
        if update.gamma_exhausted and self.config.gamma_exhaustion_exit:
            alerts.append((True, "Gamma exhaustion → Exit"))
        
        # 3. Theta spike
        if update.theta_dangerous and self.config.theta_spike_exit:
            alerts.append((True, "Theta spike → Exit"))
        
        # 4. Spread widened
        if update.spread_wide:
            alerts.append((False, "⚠️ Spread widened (monitor)"))
        
        # 5. Profit target hit
        if trade.current_ltp is not None:
            if self._check_target_hit(trade):
                alerts.append((True, "Profit target hit → Exit"))
        
        # 6. Stop-loss hit
        if trade.current_ltp is not None:
            if self._check_sl_hit(trade):
                alerts.append((True, "Stop-loss hit → Exit"))
        
        # 7. Trailing SL activation
        if trade.current_ltp is not None:
            if self._check_trail_activation(trade):
                alerts.append((False, "Trailing SL activated"))
        
        return alerts
    
    def _check_delta_flip(self, trade: ActiveTrade) -> bool:
        """Check if delta has flipped direction"""
        
        if (trade.delta_at_entry is None or 
            trade.delta_current is None):
            return False
        
        # Bullish (positive delta) → check if became negative
        if trade.delta_at_entry > 0.5:
            return trade.delta_current < 0.3  # Flipped to bearish
        
        # Bearish (negative delta) → check if became positive
        elif trade.delta_at_entry < -0.5:
            return trade.delta_current > -0.3  # Flipped to bullish
        
        return False
    
    def _check_target_hit(self, trade: ActiveTrade) -> bool:
        """Check if profit target reached"""
        
        if trade.current_ltp is None or trade.target_level is None:
            return False
        
        # For CE: target is ABOVE entry (price going up is profit)
        if trade.option_type == "CE":
            return trade.current_ltp >= trade.target_level.price
        else:  # PE: target is BELOW entry (price going down is profit)
            return trade.current_ltp <= trade.target_level.price
    
    def _check_sl_hit(self, trade: ActiveTrade) -> bool:
        """Check if stop-loss hit"""
        
        if trade.current_ltp is None or trade.sl_level is None:
            return False
        
        # For CE: SL is below entry
        if trade.option_type == "CE":
            return trade.current_ltp <= trade.sl_level.price
        else:  # PE: SL is above entry
            return trade.current_ltp >= trade.sl_level.price
    
    def _check_trail_activation(self, trade: ActiveTrade) -> bool:
        """Check if trailing SL should activate"""
        
        if trade.current_ltp is None or trade.entry_price is None:
            return False
        
        # Check if profit threshold reached
        profit_points = abs(trade.current_ltp - trade.entry_price)
        trail_threshold = trade.entry_price * self.config.trail_activation_percent / 100
        
        if profit_points >= trail_threshold:
            # Activate trailing SL if not already active
            if trade.trail_sl is None:
                from src.utils.trade_models import TradeLevel
                
                # Calculate trail SL
                if trade.option_type == "CE":
                    trail_price = trade.current_ltp + self.config.trail_distance_points
                else:
                    trail_price = trade.current_ltp - self.config.trail_distance_points
                
                trade.trail_sl = TradeLevel(
                    price=trail_price,
                    level_type="TRAIL",
                    reason="Trailing SL activated",
                )
                return True  # SL activated
        
        return False
    
    def update_max_profit(self, trade: ActiveTrade):
        """Update max unrealized profit"""
        
        current_pnl = trade.pnl_unrealized()
        if current_pnl > trade.max_profit:
            trade.max_profit = current_pnl


# ============================================================================
# RISK CONTROL ENGINE
# ============================================================================

class RiskControlEngine:
    """Enforce risk limits and prevent over-trading"""
    
    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()
        self.daily_trades: List[dict] = []
        self.risk_limits = RiskLimitStatus()
    
    def on_trade_exit(
        self,
        pnl: float,
        exit_reason: ExitReason,
        exit_time: datetime,
    ):
        """Called when trade exits"""
        
        # Record trade
        self.daily_trades.append({
            "pnl": pnl,
            "reason": exit_reason,
            "time": exit_time,
        })
        
        # Update risk limits
        if pnl < 0:  # Loss
            self.risk_limits.on_sl_hit(exit_time)
            self.risk_limits.daily_loss += abs(pnl)
        else:  # Profit
            self.risk_limits.on_profit()
            self.risk_limits.trades_today += 1
        
        self.risk_limits.daily_pnl += pnl
    
    def check_daily_loss_limit(self) -> Tuple[bool, str]:
        """Check if daily loss limit breached"""
        
        if self.risk_limits.daily_loss >= self.config.daily_loss_limit:
            return False, f"Daily loss limit (₹{self.config.daily_loss_limit}) reached"
        
        return True, "Daily loss limit OK"
    
    def check_consecutive_losses(self) -> Tuple[bool, str]:
        """Check consecutive loss limit"""
        
        if self.risk_limits.consecutive_losses >= self.config.consecutive_loss_limit:
            return False, f"Consecutive loss limit ({self.config.consecutive_loss_limit}) reached"
        
        return True, "Consecutive losses OK"
    
    def check_max_trades(self) -> Tuple[bool, str]:
        """Check max trades per day"""
        
        if self.risk_limits.trades_today >= self.config.max_trades_per_day:
            return False, f"Max trades per day ({self.config.max_trades_per_day}) reached"
        
        return True, "Can still trade today"
    
    def get_cooldown_status(self, current_time: datetime) -> Tuple[bool, str]:
        """Check if in cooldown period after SL"""
        
        if self.risk_limits.last_sl_time is None:
            return True, "No SL in cooldown"
        
        elapsed = (current_time - self.risk_limits.last_sl_time).total_seconds() / 60
        
        if elapsed < self.config.cooldown_minutes_after_sl:
            remaining = self.config.cooldown_minutes_after_sl - elapsed
            return False, f"In cooldown: {remaining:.0f} minutes remaining"
        
        return True, "Cooldown expired"


# ============================================================================
# FORCE EXIT DETECTOR
# ============================================================================

class ForceExitDetector:
    """Detect conditions that require forced exit"""
    
    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()
    
    def check_force_exit_conditions(
        self,
        trade: ActiveTrade,
        current_time: datetime,
        data_fresh: bool = True,
        spread_points: float = 0,
    ) -> Tuple[bool, Optional[ExitReason], str]:
        """
        Check if trade should be force-exited
        Returns: (should_exit, exit_reason, message)
        """
        
        # Check 1: Data feed freeze
        if not data_fresh and self.config.force_exit_on_data_freeze:
            return True, ExitReason.SYSTEM_ERROR, "Data feed frozen → Force exit"
        
        # Check 2: Spread too wide
        if spread_points > self.config.max_spread_points:
            if self.config.force_exit_on_spread_spike:
                return True, ExitReason.FORCED_EXIT, (
                    f"Spread too wide ({spread_points}pts) → Force exit"
                )
        
        # Check 3: Market close time
        if current_time.hour >= 15 and current_time.minute >= 15:
            return True, ExitReason.MARKET_CLOSE, "Market closing (15:15) → Force exit"
        
        # Check 4: Hard exit time
        if current_time.time() >= self.config.force_exit_time:
            return True, ExitReason.TIME_DECAY, "Force exit time → Exit for theta"
        
        return False, None, "No force exit needed"


# ============================================================================
# POSITION UPDATE TRACKER
# ============================================================================

class PositionUpdateTracker:
    """Track position updates and changes"""
    
    def __init__(self):
        self.updates: List[TradeMonitorUpdate] = []
        self.greeks_history: List[dict] = []
    
    def record_update(self, update: TradeMonitorUpdate):
        """Record monitoring update"""
        self.updates.append(update)
    
    def record_greeks(
        self,
        delta: Optional[float],
        gamma: Optional[float],
        theta: Optional[float],
    ):
        """Record Greeks snapshot"""
        self.greeks_history.append({
            "time": datetime.now(),
            "delta": delta,
            "gamma": gamma,
            "theta": theta,
        })
    
    def get_latest_update(self) -> Optional[TradeMonitorUpdate]:
        """Get latest monitoring update"""
        return self.updates[-1] if self.updates else None
    
    def get_greeks_trend(self) -> dict:
        """Analyze Greeks trend"""
        
        if len(self.greeks_history) < 2:
            return {"trend": "INSUFFICIENT_DATA"}
        
        latest = self.greeks_history[-1]
        prev = self.greeks_history[-2]
        
        return {
            "delta_change": (latest.get("delta") or 0) - (prev.get("delta") or 0),
            "gamma_change": (latest.get("gamma") or 0) - (prev.get("gamma") or 0),
            "theta_change": (latest.get("theta") or 0) - (prev.get("theta") or 0),
            "latest": latest,
        }
