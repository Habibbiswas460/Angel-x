"""
PHASE 6 — EMERGENCY EXIT + KILL-SWITCH ENGINE

Anytime, any reason: One signal → All positions exit
- Manual kill switch
- System errors
- Broker connection loss
- Sudden market events
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List, Tuple
from enum import Enum
from src.utils.trade_models import (
    ActiveTrade, ExitReason, ClosedTrade, TradeResult
)


# ============================================================================
# ENUMS
# ============================================================================

class KillSwitchReason(Enum):
    """Reasons to activate kill switch"""
    MANUAL = "MANUAL"                        # User pressed kill
    BROKER_ERROR = "BROKER_ERROR"            # Broker error detected
    DATA_FREEZE = "DATA_FREEZE"              # Data feed frozen
    SPREAD_EXPLOSION = "SPREAD_EXPLOSION"    # Bid-ask exploded
    CONNECTIVITY_LOSS = "CONNECTIVITY_LOSS"  # Lost broker connection
    SYSTEM_ERROR = "SYSTEM_ERROR"            # Technical error
    MARKET_EVENT = "MARKET_EVENT"            # Unusual market move
    EMERGENCY = "EMERGENCY"                  # Generic emergency


@dataclass
class KillSwitchAlert:
    """Kill switch activation alert"""
    reason: KillSwitchReason
    timestamp: datetime = field(default_factory=datetime.now)
    details: str = ""
    affected_trades: int = 0
    total_risk_closed: float = 0.0
    total_pnl_realized: float = 0.0


# ============================================================================
# KILL-SWITCH ENGINE
# ============================================================================

class KillSwitchEngine:
    """Master kill switch - exit ALL positions immediately"""
    
    def __init__(self):
        self.active = False
        self.last_activation: Optional[KillSwitchAlert] = None
        self.activation_history: List[KillSwitchAlert] = []
    
    def activate(
        self,
        reason: KillSwitchReason,
        details: str = "",
        active_trades: Optional[dict] = None,
    ) -> KillSwitchAlert:
        """
        Activate kill switch
        Exit all active trades immediately
        """
        
        affected = len(active_trades or {})
        
        # Calculate total risk - handle both dict and object formats
        total_risk = 0
        for t in (active_trades or {}).values():
            if isinstance(t, dict):
                total_risk += t.get("risk_amount", 0)
            else:
                # It's an object (ActiveTrade)
                total_risk += getattr(t, "risk_amount", 0)
        
        alert = KillSwitchAlert(
            reason=reason,
            details=details,
            affected_trades=affected,
            total_risk_closed=total_risk,
        )
        
        self.active = True
        self.last_activation = alert
        self.activation_history.append(alert)
        
        return alert
    
    def deactivate(self):
        """Deactivate kill switch (manual reset)"""
        self.active = False
    
    def is_active(self) -> bool:
        """Check if kill switch is active"""
        return self.active
    
    def get_history(self) -> List[KillSwitchAlert]:
        """Get kill switch history"""
        return self.activation_history


# ============================================================================
# EMERGENCY EXIT MANAGER
# ============================================================================

class EmergencyExitManager:
    """Manage emergency exits for all active trades"""
    
    def __init__(self):
        self.emergency_exits: List[dict] = []
        self.exit_times: dict = {}
    
    def exit_all_trades(
        self,
        active_trades: dict,
        current_ltp: dict,
        reason: ExitReason,
        exit_reason_text: str,
    ) -> Tuple[int, float, List[ClosedTrade]]:
        """
        Exit all active trades
        Returns: (num_exited, total_pnl, closed_trade_records)
        """
        
        closed_trades = []
        total_pnl = 0.0
        num_exited = 0
        
        for trade_id, trade in active_trades.items():
            # Get exit price
            exit_price = current_ltp.get(trade_id, trade.entry_price)
            
            # Calculate P&L
            point_diff = exit_price - trade.entry_price
            pnl = point_diff * trade.quantity * 100  # ₹
            
            # Determine result
            if pnl > 0:
                result = TradeResult.PROFIT
            elif pnl < 0:
                result = TradeResult.LOSS
            else:
                result = TradeResult.BREAKEVEN
            
            # Calculate duration
            duration_secs = int(
                (datetime.now() - trade.entry_time).total_seconds()
            )
            
            # Create closed trade record
            closed = ClosedTrade(
                trade_id=trade_id,
                symbol=trade.symbol,
                option_type=trade.option_type,
                strike=trade.strike,
                quantity=trade.quantity,
                entry_price=trade.entry_price,
                entry_time=trade.entry_time,
                exit_price=exit_price,
                exit_time=datetime.now(),
                exit_reason=reason,
                pnl=pnl,
                pnl_percent=(pnl / (trade.risk_amount or 1)) * 100,
                result=result,
                duration_seconds=duration_secs,
                risk_amount=trade.risk_amount,
            )
            
            closed_trades.append(closed)
            total_pnl += pnl
            num_exited += 1
            
            # Record exit
            self.emergency_exits.append({
                "trade_id": trade_id,
                "reason": exit_reason_text,
                "exit_price": exit_price,
                "pnl": pnl,
                "timestamp": datetime.now(),
            })
            
            self.exit_times[trade_id] = datetime.now()
        
        return num_exited, total_pnl, closed_trades
    
    def exit_single_trade(
        self,
        trade: ActiveTrade,
        exit_price: float,
        reason: ExitReason,
        reason_text: str,
    ) -> ClosedTrade:
        """Exit a single trade"""
        
        # Calculate P&L
        point_diff = exit_price - trade.entry_price
        pnl = point_diff * trade.quantity * 100
        
        # Determine result
        if pnl > 0:
            result = TradeResult.PROFIT
        elif pnl < 0:
            result = TradeResult.LOSS
        else:
            result = TradeResult.BREAKEVEN
        
        # Duration
        duration_secs = int(
            (datetime.now() - trade.entry_time).total_seconds()
        )
        
        # Create record
        closed = ClosedTrade(
            trade_id=trade.trade_id,
            symbol=trade.symbol,
            option_type=trade.option_type,
            strike=trade.strike,
            quantity=trade.quantity,
            entry_price=trade.entry_price,
            entry_time=trade.entry_time,
            exit_price=exit_price,
            exit_time=datetime.now(),
            exit_reason=reason,
            pnl=pnl,
            pnl_percent=(pnl / (trade.risk_amount or 1)) * 100,
            result=result,
            duration_seconds=duration_secs,
            max_unrealized_pnl=trade.max_profit,
            risk_amount=trade.risk_amount,
        )
        
        # Record
        self.emergency_exits.append({
            "trade_id": trade.trade_id,
            "reason": reason_text,
            "exit_price": exit_price,
            "pnl": pnl,
            "timestamp": datetime.now(),
        })
        
        self.exit_times[trade.trade_id] = datetime.now()
        
        return closed
    
    def get_emergency_exits(self) -> List[dict]:
        """Get all emergency exits"""
        return self.emergency_exits
    
    def get_exit_summary(self) -> dict:
        """Get summary of emergency exits"""
        
        total_trades = len(self.emergency_exits)
        total_pnl = sum(e.get("pnl", 0) for e in self.emergency_exits)
        winners = sum(1 for e in self.emergency_exits if e.get("pnl", 0) > 0)
        
        return {
            "total_emergency_exits": total_trades,
            "total_pnl": total_pnl,
            "winners": winners,
            "losers": total_trades - winners,
            "avg_exit_pnl": total_pnl / total_trades if total_trades > 0 else 0,
        }


# ============================================================================
# HEALTH CHECK ENGINE
# ============================================================================

class HealthCheckEngine:
    """Continuously check system health"""
    
    def __init__(self):
        self.last_data_update: Optional[datetime] = None
        self.broker_connected = True
        self.data_feed_active = True
        self.system_ok = True
    
    def update_data_timestamp(self):
        """Called when market data arrives"""
        self.last_data_update = datetime.now()
    
    def check_data_feed_health(self, timeout_seconds: int = 30) -> Tuple[bool, str]:
        """Check if data feed is alive"""
        
        if self.last_data_update is None:
            return False, "No data received yet"
        
        elapsed = (datetime.now() - self.last_data_update).total_seconds()
        
        if elapsed > timeout_seconds:
            return False, f"Data feed frozen ({elapsed:.0f}s)"
        
        return True, f"Data OK ({elapsed:.1f}s)"
    
    def set_broker_status(self, connected: bool):
        """Update broker connection status"""
        self.broker_connected = connected
    
    def check_system_health(self) -> Tuple[str, List[str]]:
        """
        Check overall system health
        Returns: (status="GREEN"|"YELLOW"|"RED", warnings)
        """
        
        warnings = []
        
        # Check data feed
        data_ok, data_msg = self.check_data_feed_health()
        if not data_ok:
            warnings.append(f"⚠️ {data_msg}")
        
        # Check broker
        if not self.broker_connected:
            warnings.append("⚠️ Broker disconnected")
        
        # Determine status
        if not data_ok or not self.broker_connected:
            status = "RED"
        elif len(warnings) > 0:
            status = "YELLOW"
        else:
            status = "GREEN"
        
        return status, warnings


# ============================================================================
# CIRCUIT BREAKER
# ============================================================================

class CircuitBreaker:
    """Circuit breaker pattern - stop trading on errors"""
    
    def __init__(self, failure_threshold: int = 3):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.is_broken = False
        self.failure_reasons: List[str] = []
    
    def record_failure(self, reason: str):
        """Record a failure"""
        self.failure_count += 1
        self.failure_reasons.append(reason)
        
        if self.failure_count >= self.failure_threshold:
            self.is_broken = True
    
    def record_success(self):
        """Record a success - reset counter"""
        self.failure_count = 0
        self.failure_reasons = []
        self.is_broken = False
    
    def can_trade(self) -> Tuple[bool, str]:
        """Check if circuit breaker allows trading"""
        
        if self.is_broken:
            return False, f"Circuit broken ({self.failure_count} failures)"
        
        return True, "Circuit OK"
    
    def reset(self):
        """Manual reset"""
        self.failure_count = 0
        self.failure_reasons = []
        self.is_broken = False
    
    def get_status(self) -> dict:
        """Get circuit breaker status"""
        return {
            "is_broken": self.is_broken,
            "failure_count": self.failure_count,
            "threshold": self.failure_threshold,
            "reasons": self.failure_reasons,
        }
