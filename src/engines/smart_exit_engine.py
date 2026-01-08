"""
Advanced Smart Exit Engine with Trailing Stops & Profit Laddering
Replaces the basic exit_trade logic with sophisticated exit management
"""

from dataclasses import dataclass
from typing import Optional, List
from enum import Enum
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ExitTrigger(Enum):
    """Exit trigger types"""
    HARD_SL = "hard_sl"
    TRAILING_SL = "trailing_sl"
    PROFIT_TARGET = "profit_target"
    PROFIT_LADDER = "profit_ladder"
    TIME_BASED = "time_based"
    DELTA_WEAKNESS = "delta_weakness"
    GAMMA_ROLLOVER = "gamma_rollover"
    IV_CRUSH = "iv_crush"
    OI_MISMATCH = "oi_mismatch"
    EXPIRY_RUSH = "expiry_rush"
    MANUAL = "manual"


@dataclass
class ExitConfiguration:
    """Smart exit configuration"""
    # Trailing stop
    use_trailing_stop: bool = True
    trailing_stop_percent: float = 2.0  # Trail by 2% of peak
    
    # Profit laddering (take profits incrementally)
    use_profit_ladder: bool = True
    ladder_rungs: List[float] = None  # [(target%, qty_percent), ...]
    
    # Time-based exits
    max_hold_time_seconds: int = 600  # Max 10 minutes
    exit_before_expiry_minutes: int = 5  # Exit 5 min before expiry
    
    # Greeks-based exits
    delta_weakness_threshold: float = 0.15  # Exit if delta drops 15%
    gamma_rollover_threshold: float = 0.8  # Exit if gamma drops to 80% of entry
    iv_crush_threshold: float = 5.0  # Exit if IV drops >5%
    
    def __post_init__(self):
        """Set default ladder rungs"""
        if self.ladder_rungs is None:
            self.ladder_rungs = [
                (1.0, 0.25),   # 25% at 1x profit
                (2.0, 0.50),   # 50% at 2x profit
                (3.0, 0.25),   # 25% at 3x profit
            ]


@dataclass
class ExitSnapshot:
    """Snapshot of position at exit decision"""
    trigger: ExitTrigger
    exit_price: float
    exit_time: datetime
    delta_at_exit: float
    gamma_at_exit: float
    theta_at_exit: float
    iv_at_exit: float
    holding_seconds: int
    pnl_percent: float
    
    # Trail info
    peak_price: Optional[float] = None
    trail_distance: Optional[float] = None
    
    # Ladder info
    partial_exit: bool = False
    qty_exited: int = 0
    qty_remaining: int = 0


class SmartExitEngine:
    """
    Advanced exit management with:
    - Trailing stops
    - Profit laddering
    - Time-based exits
    - Greeks-based exits
    - Expiry rush protection
    """
    
    def __init__(self, config: Optional[ExitConfiguration] = None):
        self.config = config or ExitConfiguration()
        self.peak_prices = {}  # track_id -> peak_price
        self.entry_times = {}  # track_id -> entry_time
        self.partial_exits = {}  # track_id -> [(time, qty, price), ...]
        
        logger.info(f"SmartExitEngine initialized")
        logger.info(f"  Trailing Stop: {self.config.use_trailing_stop} ({self.config.trailing_stop_percent}%)")
        logger.info(f"  Profit Ladder: {self.config.use_profit_ladder}")
        logger.info(f"  Max Hold: {self.config.max_hold_time_seconds}s")
    
    def update_trade_price(self, trade_id: str, current_price: float):
        """Update peak price for trailing stop"""
        if trade_id not in self.peak_prices:
            self.peak_prices[trade_id] = current_price
        else:
            self.peak_prices[trade_id] = max(self.peak_prices[trade_id], current_price)
    
    def check_exit_conditions(
        self,
        trade_id: str,
        current_price: float,
        current_delta: float,
        current_gamma: float,
        current_theta: float,
        current_iv: float,
        entry_price: float,
        entry_delta: float,
        entry_gamma: float,
        entry_iv: float,
        sl_price: float,
        target_price: float,
        entry_time: datetime,
        time_to_expiry_minutes: int = 30,
        quantity: int = 1,
        exited_qty: int = 0
    ) -> Optional[ExitSnapshot]:
        """
        Check all exit conditions and return exit snapshot if triggered
        
        Returns:
            ExitSnapshot if any condition is met, None otherwise
        """
        
        now = datetime.now()
        holding_seconds = int((now - entry_time).total_seconds())
        pnl_percent = ((current_price - entry_price) / entry_price * 100) if entry_price > 0 else 0
        
        # 1. Hard Stop Loss
        if current_price <= sl_price:
            return ExitSnapshot(
                trigger=ExitTrigger.HARD_SL,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 2. Profit Target Hit
        if current_price >= target_price:
            return ExitSnapshot(
                trigger=ExitTrigger.PROFIT_TARGET,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 3. Trailing Stop Loss
        if self.config.use_trailing_stop:
            trailing_exit = self._check_trailing_stop(
                trade_id, current_price, entry_price, current_delta, 
                current_gamma, current_theta, current_iv, holding_seconds, 
                pnl_percent, now
            )
            if trailing_exit:
                return trailing_exit
        
        # 4. Profit Laddering (partial exit)
        if self.config.use_profit_ladder and pnl_percent > 0:
            ladder_exit = self._check_profit_ladder(
                trade_id, pnl_percent, current_price, quantity, exited_qty,
                current_delta, current_gamma, current_theta, current_iv,
                holding_seconds, now
            )
            if ladder_exit:
                return ladder_exit
        
        # 5. Time-Based Exit
        if holding_seconds > self.config.max_hold_time_seconds:
            return ExitSnapshot(
                trigger=ExitTrigger.TIME_BASED,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 6. Delta Weakness (Greeks degradation)
        if entry_delta > 0:
            delta_decline_pct = abs((current_delta - entry_delta) / entry_delta * 100)
            if delta_decline_pct > self.config.delta_weakness_threshold * 100:
                return ExitSnapshot(
                    trigger=ExitTrigger.DELTA_WEAKNESS,
                    exit_price=current_price,
                    exit_time=now,
                    delta_at_exit=current_delta,
                    gamma_at_exit=current_gamma,
                    theta_at_exit=current_theta,
                    iv_at_exit=current_iv,
                    holding_seconds=holding_seconds,
                    pnl_percent=pnl_percent
                )
        
        # 7. Gamma Rollover (Greeks peak reached)
        if entry_gamma > 0:
            gamma_ratio = current_gamma / entry_gamma
            if gamma_ratio < self.config.gamma_rollover_threshold:
                return ExitSnapshot(
                    trigger=ExitTrigger.GAMMA_ROLLOVER,
                    exit_price=current_price,
                    exit_time=now,
                    delta_at_exit=current_delta,
                    gamma_at_exit=current_gamma,
                    theta_at_exit=current_theta,
                    iv_at_exit=current_iv,
                    holding_seconds=holding_seconds,
                    pnl_percent=pnl_percent
                )
        
        # 8. IV Crush Protection
        if entry_iv > 0:
            iv_drop = entry_iv - current_iv
            if iv_drop > self.config.iv_crush_threshold:
                return ExitSnapshot(
                    trigger=ExitTrigger.IV_CRUSH,
                    exit_price=current_price,
                    exit_time=now,
                    delta_at_exit=current_delta,
                    gamma_at_exit=current_gamma,
                    theta_at_exit=current_theta,
                    iv_at_exit=current_iv,
                    holding_seconds=holding_seconds,
                    pnl_percent=pnl_percent
                )
        
        # 9. Expiry Rush Protection
        if time_to_expiry_minutes <= self.config.exit_before_expiry_minutes:
            return ExitSnapshot(
                trigger=ExitTrigger.EXPIRY_RUSH,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 6. Expiry Rush (exit before final minutes)
        if time_to_expiry_minutes < self.config.exit_before_expiry_minutes:
            return ExitSnapshot(
                trigger=ExitTrigger.EXPIRY_RUSH,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 7. Delta Weakness
        if entry_delta != 0:
            delta_degradation = abs(current_delta) / abs(entry_delta)
            if delta_degradation < (1.0 - self.config.delta_weakness_threshold):
                return ExitSnapshot(
                    trigger=ExitTrigger.DELTA_WEAKNESS,
                    exit_price=current_price,
                    exit_time=now,
                    delta_at_exit=current_delta,
                    gamma_at_exit=current_gamma,
                    theta_at_exit=current_theta,
                    iv_at_exit=current_iv,
                    holding_seconds=holding_seconds,
                    pnl_percent=pnl_percent
                )
        
        # 8. Gamma Rollover
        if current_gamma < (entry_gamma * self.config.gamma_rollover_threshold):
            return ExitSnapshot(
                trigger=ExitTrigger.GAMMA_ROLLOVER,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=current_delta,
                gamma_at_exit=current_gamma,
                theta_at_exit=current_theta,
                iv_at_exit=current_iv,
                holding_seconds=holding_seconds,
                pnl_percent=pnl_percent
            )
        
        # 9. IV Crush
        if entry_iv > 0:
            iv_change_pct = ((entry_iv - current_iv) / entry_iv * 100)
            if iv_change_pct > self.config.iv_crush_threshold:
                return ExitSnapshot(
                    trigger=ExitTrigger.IV_CRUSH,
                    exit_price=current_price,
                    exit_time=now,
                    delta_at_exit=current_delta,
                    gamma_at_exit=current_gamma,
                    theta_at_exit=current_theta,
                    iv_at_exit=current_iv,
                    holding_seconds=holding_seconds,
                    pnl_percent=pnl_percent
                )
        
        return None
    
    def _check_trailing_stop(
        self, trade_id, current_price, entry_price, delta, gamma, theta, iv,
        holding_sec, pnl_pct, now
    ) -> Optional[ExitSnapshot]:
        """Check if trailing stop is triggered"""
        
        # Only use trailing stop after some profit
        if pnl_pct < 0.5:
            return None
        
        if trade_id not in self.peak_prices:
            self.peak_prices[trade_id] = current_price
            return None
        
        peak = self.peak_prices[trade_id]
        trail_distance = peak * (self.config.trailing_stop_percent / 100)
        
        if current_price < (peak - trail_distance):
            return ExitSnapshot(
                trigger=ExitTrigger.TRAILING_SL,
                exit_price=current_price,
                exit_time=now,
                delta_at_exit=delta,
                gamma_at_exit=gamma,
                theta_at_exit=theta,
                iv_at_exit=iv,
                holding_seconds=holding_sec,
                pnl_percent=pnl_pct,
                peak_price=peak,
                trail_distance=trail_distance
            )
        
        return None
    
    def _check_profit_ladder(
        self, trade_id, pnl_pct, current_price, quantity, exited_qty,
        delta, gamma, theta, iv, holding_sec, now
    ) -> Optional[ExitSnapshot]:
        """Check if any profit ladder rung is hit"""
        
        remaining_qty = quantity - exited_qty
        
        for target_pct, qty_fraction in self.config.ladder_rungs:
            if pnl_pct >= target_pct:
                qty_to_exit = int(quantity * qty_fraction)
                
                # Check if already exited at this rung
                if trade_id in self.partial_exits:
                    for prev_time, prev_qty, prev_price in self.partial_exits[trade_id]:
                        if abs(prev_qty - qty_to_exit) < 1:  # Already exited at this qty
                            continue
                
                if remaining_qty >= qty_to_exit:
                    return ExitSnapshot(
                        trigger=ExitTrigger.PROFIT_LADDER,
                        exit_price=current_price,
                        exit_time=now,
                        delta_at_exit=delta,
                        gamma_at_exit=gamma,
                        theta_at_exit=theta,
                        iv_at_exit=iv,
                        holding_seconds=holding_sec,
                        pnl_percent=pnl_pct,
                        partial_exit=True,
                        qty_exited=qty_to_exit,
                        qty_remaining=remaining_qty - qty_to_exit
                    )
        
        return None
    
    def record_partial_exit(self, trade_id: str, qty: int, exit_price: float):
        """Record a partial exit"""
        if trade_id not in self.partial_exits:
            self.partial_exits[trade_id] = []
        
        self.partial_exits[trade_id].append((datetime.now(), qty, exit_price))
        logger.info(f"Partial exit recorded: {trade_id} - Qty: {qty} @ ₹{exit_price:.2f}")
    
    def cleanup_trade(self, trade_id: str):
        """Clean up tracking data for closed trade"""
        self.peak_prices.pop(trade_id, None)
        self.entry_times.pop(trade_id, None)
        self.partial_exits.pop(trade_id, None)
