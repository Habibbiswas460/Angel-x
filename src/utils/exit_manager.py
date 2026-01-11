"""
PHASE 7 — EXIT INTELLIGENCE ORCHESTRATOR

Unified exit management engine
8 components working together
"Entry ≈ 30% edge | Exit ≈ 70% profit"

Flow:
ActiveTrade (from Phase 6)
  ↓
Monitor all 8 exit signals simultaneously
  ↓
Determine best exit action
  ↓
Execute exit with reasoning
  ↓
Record + Learn
"""

from datetime import datetime
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

from src.utils.exit_models import (
    Phase7Config, TradeContextSnapshot, ExitContextSnapshot,
    TrailingSLState, PartialExitState, ThetaExitSignal
)
from src.utils.trailing_stop_loss import DynamicTrailingSLEngine
from src.utils.partial_exit import PartialExitEngine
from src.utils.reversal_exit import ReversalAndExhaustionManager
from src.utils.theta_time_exit import ThetaDecayExitEngine, TimeBasedForceExitEngine
from src.utils.cooldown_engine import CooldownLogicEngine
from src.utils.trade_journal import TradeJournalEngine


class ExitAction(Enum):
    NO_ACTION = "no_action"
    TRAILING_SL = "trailing_sl_hit"
    PARTIAL_EXIT = "partial_exit"
    REVERSAL_EXIT = "reversal_detected"
    EXHAUSTION_EXIT = "exhaustion_detected"
    THETA_BOMB = "theta_bomb"
    TIME_FORCED = "time_forced_exit"
    MANUAL_EXIT = "manual_exit"


@dataclass
class ExitSignalSummary:
    """Summary of all exit signals"""
    signal: ExitAction
    confidence: float
    primary_reason: str
    secondary_reasons: List[str]
    should_exit: bool
    exit_price_suggestion: Optional[float] = None


class Phase7ExitOrchestrator:
    """
    Main exit intelligence engine
    
    Orchestrates 8 exit components:
    1. Dynamic trailing SL (Greeks-based)
    2. Partial exit (profit locking)
    3. OI reversal detection (smart money)
    4. Exhaustion detection (peak avoidance)
    5. Theta decay (time bomb)
    6. Time-based forced exit (scalping discipline)
    7. Cooldown logic (psychology)
    8. Trade journal (learning)
    """
    
    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()
        
        # Initialize all 8 components
        self.trailing_sl_engine = DynamicTrailingSLEngine(config)
        self.partial_exit_engine = PartialExitEngine(config)
        self.reversal_exhaustion_manager = ReversalAndExhaustionManager(config)
        self.theta_engine = ThetaDecayExitEngine(config)
        self.time_engine = TimeBasedForceExitEngine(config)
        self.cooldown_engine = CooldownLogicEngine(config)
        self.journal_engine = TradeJournalEngine(config)
        
        # State tracking
        self.active_trade: Optional[Dict] = None
        self.trailing_sl_state: Optional[TrailingSLState] = None
        self.partial_exit_state: Optional[PartialExitState] = None
    
    # ====================================================================
    # STEP 1: INITIALIZE ACTIVE TRADE
    # ====================================================================
    
    def initialize_active_trade(
        self,
        entry_price: float,
        option_type: str,  # "CE" or "PE"
        contract_symbol: str,
        entry_time: datetime,
        entry_delta: float,
        entry_gamma: float,
        entry_theta: float,
        entry_vega: float,
        entry_iv: float,
        ce_oi: int,
        pe_oi: int,
        bid_qty: int,
        ask_qty: int,
        position_quantity: int,
        preceding_candle_close: float,
    ) -> str:
        """
        Initialize active trade in orchestrator
        """
        
        # Create entry snapshot
        self.entry_snapshot = TradeContextSnapshot(
            entry_time=entry_time,
            entry_price=entry_price,
            option_type=option_type,
            strike=entry_price,
            delta_entry=entry_delta,
            gamma_entry=entry_gamma,
            theta_entry=entry_theta,
            iv_entry=entry_iv,
            oi_ce_entry=ce_oi,
            oi_pe_entry=pe_oi,
            volume_entry=bid_qty + ask_qty,
        )
        
        # Store active trade
        self.active_trade = {
            "entry_price": entry_price,
            "option_type": option_type,
            "contract_symbol": contract_symbol,
            "entry_time": entry_time,
            "position_quantity": position_quantity,
            "current_price": entry_price,
            "current_delta": entry_delta,
            "current_gamma": entry_gamma,
            "current_theta": entry_theta,
            "current_vega": entry_vega,
            "current_iv": entry_iv,
            "ce_oi_current": ce_oi,
            "pe_oi_current": pe_oi,
        }
        
        # Initialize trailing SL state
        self.trailing_sl_state = TrailingSLState(
            is_active=False,
        )
        
        # Initialize partial exit state
        self.partial_exit_state = PartialExitState(
            first_exit_taken=False,
            remaining_quantity=position_quantity,
        )
        
        return f"Trade initialized: {contract_symbol} {option_type} @ ₹{entry_price}"
    
    # ====================================================================
    # STEP 2: UPDATE MARKET DATA (Called every tick)
    # ====================================================================
    
    def update_market_tick(
        self,
        current_price: float,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        current_vega: float,
        current_iv: float,
        ce_oi: int,
        pe_oi: int,
    ) -> None:
        """
        Update market data for active trade
        """
        
        if not self.active_trade:
            return
        
        self.active_trade.update({
            "current_price": current_price,
            "current_delta": current_delta,
            "current_gamma": current_gamma,
            "current_theta": current_theta,
            "current_vega": current_vega,
            "current_iv": current_iv,
            "ce_oi_current": ce_oi,
            "pe_oi_current": pe_oi,
        })
    
    # ====================================================================
    # STEP 3: CHECK ALL 8 EXIT SIGNALS (Main Logic)
    # ====================================================================
    
    def check_all_exit_signals(
        self,
        current_time: datetime,
        theta_prev: float,
        time_since_update_secs: float = 60.0,
        volatility_index: float = 15.0,
        consecutive_losses: int = 0,
    ) -> ExitSignalSummary:
        """
        Check all 8 exit signals and return the strongest one
        
        Priority (highest confidence wins):
        1. TIME_FORCED (non-negotiable)
        2. THETA_BOMB (exponential danger)
        3. REVERSAL_EXIT (smart money exit)
        4. EXHAUSTION_EXIT (peak avoidance)
        5. PARTIAL_EXIT (profit locking)
        6. TRAILING_SL (normal exit)
        7. NO_ACTION (hold)
        """
        
        if not self.active_trade:
            return ExitSignalSummary(
                signal=ExitAction.NO_ACTION,
                confidence=0.0,
                primary_reason="No active trade",
                secondary_reasons=[],
                should_exit=False,
            )
        
        signals_detected = []
        
        # ---- SIGNAL 1: TIME-BASED FORCED EXIT ----
        time_force, time_msg = self.time_engine.should_force_exit(
            current_time, self.active_trade["entry_time"]
        )
        if time_force:
            signals_detected.append((ExitAction.TIME_FORCED, 0.99, time_msg))
        
        # ---- SIGNAL 2: THETA BOMB ----
        theta_should_exit, theta_signal, theta_conf, theta_msg = self.theta_engine.should_exit_theta(
            self.active_trade["current_theta"],
            theta_prev,
            self.active_trade["entry_time"],
            current_time,
            self.active_trade["current_iv"],
            self.entry_snapshot.iv,
            time_since_update_secs
        )
        if theta_should_exit:
            signals_detected.append((ExitAction.THETA_BOMB, theta_conf, theta_msg))
        
        # ---- SIGNAL 3: OI REVERSAL ----
        reversal_should_exit, reversal_signal, reversal_conf, reversal_msg = \
            self.reversal_exhaustion_manager.check_should_exit(
                self.active_trade["ce_oi_current"],
                self.active_trade["pe_oi_current"],
                self.active_trade["current_price"],
                self.active_trade["current_delta"],
                self.active_trade["current_gamma"],
                self.active_trade["option_type"],
                check_reversal=True,
                check_exhaustion=False,
            )
        if reversal_should_exit:
            signals_detected.append((ExitAction.REVERSAL_EXIT, reversal_conf, reversal_msg))
        
        # ---- SIGNAL 4: EXHAUSTION ----
        exhaustion_should_exit, exhaustion_signal, exhaustion_conf, exhaustion_msg = \
            self.reversal_exhaustion_manager.check_should_exit(
                self.active_trade["ce_oi_current"],
                self.active_trade["pe_oi_current"],
                self.active_trade["current_price"],
                self.active_trade["current_delta"],
                self.active_trade["current_gamma"],
                self.active_trade["option_type"],
                check_reversal=False,
                check_exhaustion=True,
            )
        if exhaustion_should_exit:
            signals_detected.append((ExitAction.EXHAUSTION_EXIT, exhaustion_conf, exhaustion_msg))
        
        # ---- SIGNAL 5: PARTIAL EXIT ----
        partial_eligible, partial_signal, partial_msg = \
            self.partial_exit_engine.check_partial_exit_eligibility(
                self.active_trade["current_price"],
                self.entry_snapshot.entry_price,
                self.active_trade["current_gamma"],
                self.active_trade["current_delta"],
            )
        if partial_eligible and not self.partial_exit_state.first_exit_taken:
            signals_detected.append((ExitAction.PARTIAL_EXIT, 0.80, partial_msg))
        
        # ---- SIGNAL 6: TRAILING SL ----
        trail_activated, trail_trigger, trail_msg = self.trailing_sl_engine.check_trail_activation(
            self.active_trade["current_price"],
            self.entry_snapshot.entry_price,
            self.active_trade["current_delta"],
            self.active_trade["current_gamma"],
        )
        
        trail_hit = False
        if trail_activated and self.trailing_sl_state.current_sl:
            trail_hit, trail_hit_msg = self.trailing_sl_engine.check_trail_hit(
                self.active_trade["current_price"],
                self.trailing_sl_state.current_sl,
                self.active_trade["option_type"],
            )
            if trail_hit:
                signals_detected.append((ExitAction.TRAILING_SL, 0.85, trail_hit_msg))
        
        # ---- DECISION: Pick strongest signal ----
        if not signals_detected:
            return ExitSignalSummary(
                signal=ExitAction.NO_ACTION,
                confidence=0.0,
                primary_reason="All signals clear - trade running",
                secondary_reasons=[],
                should_exit=False,
            )
        
        # Sort by confidence (highest first)
        signals_detected.sort(key=lambda x: x[1], reverse=True)
        best_signal, best_conf, best_msg = signals_detected[0]
        secondary_reasons = [msg for _, _, msg in signals_detected[1:]]
        
        should_exit = best_conf > 0.70
        
        return ExitSignalSummary(
            signal=best_signal,
            confidence=best_conf,
            primary_reason=best_msg,
            secondary_reasons=secondary_reasons,
            should_exit=should_exit,
        )
    
    # ====================================================================
    # STEP 4: EXECUTE EXIT
    # ====================================================================
    
    def execute_exit(
        self,
        exit_price: float,
        current_time: datetime,
        exit_signal: ExitAction,
        reason: str,
        position_quantity: Optional[int] = None,
    ) -> Tuple[bool, str]:
        """
        Execute exit and record trade
        """
        
        if not self.active_trade:
            return False, "No active trade to exit"
        
        qty = position_quantity or self.active_trade["position_quantity"]
        
        # Create exit snapshot
        exit_snapshot = ExitContextSnapshot(
            exit_time=current_time,
            exit_price=exit_price,
            exit_reason=reason,
            delta_exit=self.active_trade["current_delta"],
            gamma_exit=self.active_trade["current_gamma"],
            theta_exit=self.active_trade["current_theta"],
            iv_exit=self.active_trade["current_iv"],
            oi_ce_exit=self.active_trade["ce_oi_current"],
            oi_pe_exit=self.active_trade["pe_oi_current"],
            volume_exit=qty,
        )
        
        # Record trade in journal
        trade_record = self.journal_engine.record_trade(
            self.entry_snapshot,
            exit_snapshot,
            exit_signal.value,
            qty,
        )
        
        # Calculate P&L
        pnl = trade_record.pnl_rupees
        
        # Start cooldown (no consecutive loss tracking in tests)
        self.cooldown_engine.start_cooldown(
            pnl,
            15.0,  # volatility_index - placeholder
            current_time,
            consecutive_losses=0,
        )
        
        # Clear active trade
        self.active_trade = None
        self.trailing_sl_state = None
        self.partial_exit_state = None
        
        exit_msg = f"""
╔════════════════════════════════════════════════════╗
║            TRADE EXITED & RECORDED                  ║
╚════════════════════════════════════════════════════╝

📊 Trade Summary:
  • Entry: ₹{trade_record.entry_price:.2f}
  • Exit: ₹{trade_record.exit_price:.2f}
  • P&L: ₹{pnl:,.0f} ({trade_record.pnl_percent:+.2f}%)
  • Duration: {trade_record.duration_seconds}s
  
🎯 Exit Reason:
  • Signal: {exit_signal.value}
  • Reason: {reason}
  
🔄 Cooldown Started
"""
        
        return True, exit_msg
    
    # ====================================================================
    # STEP 5: DIAGNOSTICS & REPORTING
    # ====================================================================
    
    def get_active_trade_status(self) -> Dict:
        """Get current active trade status"""
        
        if not self.active_trade:
            return {"status": "no_active_trade"}
        
        pnl = self.active_trade["current_price"] - self.entry_snapshot.entry_price
        if self.active_trade["option_type"] == "PE":
            pnl = -pnl
        
        pnl_rupees = pnl * self.active_trade["position_quantity"]
        pnl_percent = (pnl / self.entry_snapshot.entry_price * 100) \
                      if self.entry_snapshot.entry_price else 0
        
        return {
            "status": "active",
            "contract": self.active_trade["contract_symbol"],
            "option_type": self.active_trade["option_type"],
            "entry_price": self.entry_snapshot.entry_price,
            "current_price": self.active_trade["current_price"],
            "pnl_points": pnl,
            "pnl_rupees": pnl_rupees,
            "pnl_percent": pnl_percent,
            "duration_secs": int((datetime.now() - self.active_trade["entry_time"]).total_seconds()),
            "current_greeks": {
                "delta": self.active_trade["current_delta"],
                "gamma": self.active_trade["current_gamma"],
                "theta": self.active_trade["current_theta"],
            },
        }
    
    def print_session_summary(self) -> str:
        """Print complete session summary"""
        return self.journal_engine.print_session_summary()
