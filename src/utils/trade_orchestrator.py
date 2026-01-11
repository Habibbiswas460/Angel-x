"""
PHASE 6 — MAIN ORCHESTRATOR ENGINE

Complete order execution + risk management pipeline
Safe execution layer for real trading
"""

from datetime import datetime
from typing import Optional, List, Tuple, Dict
from src.utils.trade_models import (
    Phase6Config, RiskLimitStatus, ActiveTrade, ClosedTrade,
    TradeMonitorUpdate, ExitReason, OrderPlacementRequest,
    TradeResult, TradeLevel
)
from src.utils.position_sizer import (
    PreOrderSafetyGate, PositionSizingEngine,
    StopLossCalculationEngine, TargetCalculationEngine,
    OrderPreparationEngine
)
from src.utils.order_executor import (
    BrokerInterface, AtomicOrderPlacementEngine
)
from src.utils.trade_monitor import (
    TradeMonitoringEngine, RiskControlEngine,
    ForceExitDetector, PositionUpdateTracker
)
from src.utils.emergency_exit import (
    KillSwitchEngine, KillSwitchReason, EmergencyExitManager,
    HealthCheckEngine, CircuitBreaker
)


# ============================================================================
# MAIN ORCHESTRATOR
# ============================================================================

class OrderExecutionAndRiskEngine:
    """
    Complete Phase 6 orchestrator
    Execution Signal (from Phase 5) → Real Trade (monitored + risk-controlled)
    """
    
    def __init__(self, config: Optional[Phase6Config] = None):
        self.config = config or Phase6Config()
        
        # Core components
        self.safety_gate = PreOrderSafetyGate(config)
        self.sizing_engine = PositionSizingEngine(config)
        self.sl_engine = StopLossCalculationEngine(config)
        self.target_engine = TargetCalculationEngine(config)
        self.order_prep = OrderPreparationEngine(config)
        
        # Order placement
        self.broker = BrokerInterface(config)
        self.atomic_placement = AtomicOrderPlacementEngine(self.broker, config)
        
        # Monitoring & risk
        self.monitoring = TradeMonitoringEngine(config)
        self.risk_control = RiskControlEngine(config)
        self.force_exit_detector = ForceExitDetector(config)
        
        # Emergency
        self.kill_switch = KillSwitchEngine()
        self.emergency_exit = EmergencyExitManager()
        self.health_check = HealthCheckEngine()
        self.circuit_breaker = CircuitBreaker(failure_threshold=3)
        
        # State
        self.active_trades: Dict[str, ActiveTrade] = {}
        self.closed_trades: List[ClosedTrade] = []
        self.position_trackers: Dict[str, PositionUpdateTracker] = {}
        
        # Metrics
        self.total_trades = 0
        self.total_pnl = 0.0
    
    # ====================================================================
    # STEP 1: PRE-ORDER CHECKS
    # ====================================================================
    
    def verify_can_trade(
        self,
        current_time: datetime,
        market_open: bool = True,
        trade_allowed: bool = True,
    ) -> Tuple[bool, str, list]:
        """Pre-trade safety checks"""
        
        return self.safety_gate.can_place_order(
            current_time=current_time,
            risk_limits=self.risk_control.risk_limits,
            active_positions=len(self.active_trades),
            market_open=market_open,
            trade_allowed=trade_allowed,
        )
    
    # ====================================================================
    # STEP 2: PREPARE ORDER (with all calculations)
    # ====================================================================
    
    def prepare_execution_order(
        self,
        entry_price: float,
        option_type: str,
        delta_ce: Optional[float] = None,
        delta_pe: Optional[float] = None,
        gamma_ce: Optional[float] = None,
        gamma_pe: Optional[float] = None,
        current_iv: float = 0.2,
    ) -> dict:
        """
        Prepare complete order with all calculations
        Returns: dict with quantity, SL, target
        """
        
        return self.order_prep.prepare_order(
            entry_price=entry_price,
            option_type=option_type,
            delta_ce=delta_ce,
            delta_pe=delta_pe,
            gamma_ce=gamma_ce,
            gamma_pe=gamma_pe,
            current_iv=current_iv,
        )
    
    # ====================================================================
    # STEP 3: PLACE ATOMIC ORDER
    # ====================================================================
    
    def place_order(
        self,
        symbol: str,
        option_type: str,
        strike: float,
        entry_price: float,
        prepared_order: dict,
    ) -> Tuple[bool, Optional[str], str]:
        """
        Place buy + SL order atomically
        Returns: (success, trade_id, message)
        """
        
        # Extract prepared calculations
        quantity = prepared_order.get("quantity", 1)
        sl_price = prepared_order.get("sl_price", entry_price * 0.98)
        target_price = prepared_order.get("target_price", entry_price * 1.01)
        
        # Place atomic order
        response = self.atomic_placement.place_atomic_order(
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            entry_price=entry_price,
            sl_price=sl_price,
            target_price=target_price,
        )
        
        if not response.success or response.linked_orders is None:
            self.circuit_breaker.record_failure(
                f"Order placement failed: {response.error_message}"
            )
            return False, None, response.error_message or "Unknown error"
        
        # Create active trade record
        import uuid
        trade_id = str(uuid.uuid4())[:8]
        
        # Create trade levels
        entry_level = TradeLevel(
            price=entry_price,
            level_type="ENTRY",
            reason="Market entry",
            delta_at_level=prepared_order.get("delta_entry"),
        )
        
        sl_level = TradeLevel(
            price=sl_price,
            level_type="SL",
            reason="Stop-loss level",
        )
        
        target_level = TradeLevel(
            price=target_price,
            level_type="TARGET",
            reason="Profit target",
        )
        
        active_trade = ActiveTrade(
            trade_id=trade_id,
            symbol=symbol,
            option_type=option_type,
            strike=strike,
            quantity=quantity,
            entry_price=entry_price,
            entry_time=datetime.now(),
            linked_orders=response.linked_orders,
            entry_level=entry_level,
            sl_level=sl_level,
            target_level=target_level,
            risk_amount=prepared_order.get("actual_risk", 0),
            reward_amount=abs(target_price - entry_price) * quantity * 100,
            risk_reward_ratio=prepared_order.get("risk_reward_ratio", 0),
            delta_at_entry=prepared_order.get("delta_entry"),
            gamma_at_entry=prepared_order.get("gamma_entry"),
        )
        
        self.active_trades[trade_id] = active_trade
        self.position_trackers[trade_id] = PositionUpdateTracker()
        self.total_trades += 1
        
        self.circuit_breaker.record_success()
        
        return True, trade_id, f"✓ Trade {trade_id} placed atomically"
    
    # ====================================================================
    # STEP 4: MONITOR TRADE
    # ====================================================================
    
    def update_trade(
        self,
        trade_id: str,
        update: TradeMonitorUpdate,
    ) -> List[Tuple[bool, str]]:
        """
        Update trade monitoring
        Returns: list of (should_exit, reason)
        """
        
        if trade_id not in self.active_trades:
            return [(False, "Trade not found")]
        
        trade = self.active_trades[trade_id]
        
        # Record update
        self.position_trackers[trade_id].record_update(update)
        
        # Monitor
        alerts = self.monitoring.update_trade_monitoring(trade, update)
        
        # Update max profit
        self.monitoring.update_max_profit(trade)
        
        return alerts
    
    # ====================================================================
    # STEP 5: EXIT TRADE (normal)
    # ====================================================================
    
    def exit_trade(
        self,
        trade_id: str,
        exit_price: float,
        exit_reason: ExitReason,
    ) -> Tuple[bool, ClosedTrade]:
        """
        Exit a trade normally (target/SL/manual)
        Returns: (success, closed_trade_record)
        """
        
        if trade_id not in self.active_trades:
            return False, None
        
        trade = self.active_trades[trade_id]
        
        # Create closed trade record
        duration_secs = int(
            (datetime.now() - trade.entry_time).total_seconds()
        )
        
        point_diff = exit_price - trade.entry_price
        pnl = point_diff * trade.quantity * 100
        
        if pnl > 0:
            result = TradeResult.PROFIT
        elif pnl < 0:
            result = TradeResult.LOSS
        else:
            result = TradeResult.BREAKEVEN
        
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
            exit_reason=exit_reason,
            pnl=pnl,
            pnl_percent=(pnl / (trade.risk_amount or 1)) * 100 if trade.risk_amount else 0,
            result=result,
            duration_seconds=duration_secs,
            max_unrealized_pnl=trade.max_profit,
            risk_amount=trade.risk_amount,
        )
        
        # Update state
        self.closed_trades.append(closed)
        del self.active_trades[trade_id]
        
        # Update risk control
        self.risk_control.on_trade_exit(
            pnl=pnl,
            exit_reason=exit_reason,
            exit_time=datetime.now(),
        )
        
        self.total_pnl += pnl
        
        return True, closed
    
    # ====================================================================
    # STEP 6: EMERGENCY EXIT (all positions)
    # ====================================================================
    
    def activate_kill_switch(
        self,
        reason: KillSwitchReason,
        details: str = "",
    ) -> Tuple[int, float, List[ClosedTrade]]:
        """
        Activate kill switch - exit ALL positions
        Returns: (num_exited, total_pnl, closed_trades)
        """
        
        alert = self.kill_switch.activate(
            reason=reason,
            details=details,
            active_trades=self.active_trades,
        )
        
        # Exit all trades at last known prices
        current_ltp = {
            tid: trade.current_ltp or trade.entry_price
            for tid, trade in self.active_trades.items()
        }
        
        num, total_pnl, closed = self.emergency_exit.exit_all_trades(
            active_trades=self.active_trades.copy(),
            current_ltp=current_ltp,
            reason=ExitReason.KILL_SWITCH,
            exit_reason_text=f"Kill switch: {reason.value}",
        )
        
        # Move all trades to closed
        self.closed_trades.extend(closed)
        self.active_trades.clear()
        self.total_pnl += total_pnl
        
        return num, total_pnl, closed
    
    # ====================================================================
    # DIAGNOSTICS & REPORTING
    # ====================================================================
    
    def get_active_trades_summary(self) -> dict:
        """Summary of active trades"""
        
        total_pnl = 0.0
        total_risk = 0.0
        
        for trade in self.active_trades.values():
            total_pnl += trade.pnl_unrealized()
            total_risk += trade.risk_amount
        
        return {
            "active_count": len(self.active_trades),
            "total_unrealized_pnl": total_pnl,
            "total_risk_exposed": total_risk,
            "trades": {
                tid: {
                    "symbol": t.symbol,
                    "option_type": t.option_type,
                    "quantity": t.quantity,
                    "entry_price": t.entry_price,
                    "current_ltp": t.current_ltp,
                    "unrealized_pnl": t.pnl_unrealized(),
                }
                for tid, t in self.active_trades.items()
            }
        }
    
    def get_closed_trades_summary(self) -> dict:
        """Summary of closed trades"""
        
        if not self.closed_trades:
            return {
                "total_trades": 0,
                "winners": 0,
                "losers": 0,
                "total_pnl": 0.0,
                "avg_profit": 0.0,
            }
        
        winners = sum(1 for t in self.closed_trades if t.pnl > 0)
        losers = sum(1 for t in self.closed_trades if t.pnl < 0)
        total_profit = sum(t.pnl for t in self.closed_trades if t.pnl > 0)
        total_loss = sum(abs(t.pnl) for t in self.closed_trades if t.pnl < 0)
        
        return {
            "total_trades": len(self.closed_trades),
            "winners": winners,
            "losers": losers,
            "total_pnl": self.total_pnl,
            "win_rate": winners / len(self.closed_trades) if self.closed_trades else 0,
            "total_profit": total_profit,
            "total_loss": total_loss,
            "avg_pnl": self.total_pnl / len(self.closed_trades) if self.closed_trades else 0,
        }
    
    def get_risk_status(self) -> dict:
        """Risk management status"""
        
        can_trade, risk_msg = self.risk_control.risk_limits.can_trade(datetime.now())
        
        return {
            "can_trade": can_trade,
            "reason": risk_msg,
            "trades_today": self.risk_control.risk_limits.trades_today,
            "losses_today": self.risk_control.risk_limits.losses_today,
            "consecutive_losses": self.risk_control.risk_limits.consecutive_losses,
            "daily_pnl": self.risk_control.risk_limits.daily_pnl,
            "daily_loss": self.risk_control.risk_limits.daily_loss,
            "trading_locked": self.risk_control.risk_limits.trading_locked,
        }
    
    def get_system_health(self) -> dict:
        """Overall system health"""
        
        status, warnings = self.health_check.check_system_health()
        
        return {
            "status": status,
            "warnings": warnings,
            "broker_connected": self.health_check.broker_connected,
            "data_feed_active": self.health_check.data_feed_active,
            "kill_switch_active": self.kill_switch.is_active(),
            "circuit_breaker": self.circuit_breaker.get_status(),
        }
    
    def reset_daily_limits(self):
        """Reset daily limits (call at market open)"""
        self.risk_control.risk_limits = RiskLimitStatus()
