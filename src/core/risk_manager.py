"""
Risk Manager Module
Enforces risk limits and protects capital
Monitors daily loss, max trades, position limits, and circuit breakers
+ Advanced Greeks exposure limits with auto-hedging triggers
"""

from datetime import datetime, time
from threading import Lock
from typing import Dict, Optional, List
from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class GreeksLimits:
    """Portfolio-level Greeks exposure limits"""

    def __init__(self):
        # Delta limits (directional exposure)
        self.max_net_delta = getattr(config, "MAX_NET_DELTA", 100.0)  # Max 100 net delta
        self.max_gross_delta = getattr(config, "MAX_GROSS_DELTA", 200.0)  # Max 200 gross delta

        # Gamma limits (convexity risk)
        self.max_net_gamma = getattr(config, "MAX_NET_GAMMA", 5.0)
        self.max_gross_gamma = getattr(config, "MAX_GROSS_GAMMA", 10.0)

        # Theta limits (time decay)
        self.max_daily_theta = getattr(config, "MAX_DAILY_THETA", -500.0)  # Max ₹500/day decay

        # Vega limits (volatility exposure)
        self.max_net_vega = getattr(config, "MAX_NET_VEGA", 1000.0)

        # Auto-hedge triggers
        self.delta_hedge_trigger = getattr(config, "DELTA_HEDGE_TRIGGER", 80.0)  # Hedge at 80 delta
        self.gamma_hedge_trigger = getattr(config, "GAMMA_HEDGE_TRIGGER", 4.0)

        logger.info("Greeks limits initialized:")
        logger.info(f"  Max Net Delta: ±{self.max_net_delta}")
        logger.info(f"  Max Net Gamma: {self.max_net_gamma}")
        logger.info(f"  Max Daily Theta: {self.max_daily_theta}")
        logger.info(f"  Auto-hedge triggers: Δ={self.delta_hedge_trigger}, Γ={self.gamma_hedge_trigger}")


class RiskManager:
    """
    Institutional-grade risk management:
    - Daily loss limits
    - Daily profit targets
    - Maximum trades per day
    - Position size limits
    - Circuit breakers
    - Time-based restrictions
    + Advanced Greeks exposure limits
    + Auto-hedging triggers
    """

    def __init__(self):
        self.risk_lock = Lock()

        # Configuration
        self.max_daily_loss = config.MAX_DAILY_LOSS
        self.max_daily_profit = config.MAX_DAILY_PROFIT
        self.max_trades_per_day = config.MAX_TRADES_PER_DAY
        self.max_position_size = config.MAX_POSITION_SIZE

        # Daily tracking
        self.daily_pnl = 0.0
        self.trades_today = 0
        self.total_risk_exposure = 0.0
        self.losses_in_row = 0

        # Circuit breaker
        self.trading_halted = False
        self.halt_reason = None

        # Trade history
        self.trade_history = []

        # Greeks exposure tracking
        self.greeks_limits = GreeksLimits()
        self.current_net_delta = 0.0
        self.current_net_gamma = 0.0
        self.current_net_theta = 0.0
        self.current_net_vega = 0.0
        self.current_gross_delta = 0.0

        logger.info("RiskManager initialized")
        logger.info(
            f"Limits: Max Loss={self.max_daily_loss}, Max Profit={self.max_daily_profit}, Max Trades={self.max_trades_per_day}"
        )

    def update_portfolio_greeks(
        self, net_delta: float, net_gamma: float, net_theta: float, net_vega: float, gross_delta: Optional[float] = None
    ):
        """
        Update current portfolio Greeks exposure

        Args:
            net_delta: Net delta across all positions
            net_gamma: Net gamma
            net_theta: Net theta (daily decay)
            net_vega: Net vega
            gross_delta: Gross delta (sum of absolute deltas)
        """
        with self.risk_lock:
            self.current_net_delta = net_delta
            self.current_net_gamma = net_gamma
            self.current_net_theta = net_theta
            self.current_net_vega = net_vega
            self.current_gross_delta = gross_delta or abs(net_delta)

            # Check if hedging required
            hedge_needed = self._check_hedging_triggers()
            if hedge_needed:
                logger.warning(f"HEDGING REQUIRED: {hedge_needed}")

    def _check_hedging_triggers(self) -> Optional[str]:
        """
        Check if portfolio needs hedging

        Returns:
            Hedge reason if needed, None otherwise
        """
        # Delta hedge trigger
        if abs(self.current_net_delta) >= self.greeks_limits.delta_hedge_trigger:
            return f"Net delta {self.current_net_delta:.1f} exceeds trigger {self.greeks_limits.delta_hedge_trigger}"

        # Gamma hedge trigger
        if abs(self.current_net_gamma) >= self.greeks_limits.gamma_hedge_trigger:
            return f"Net gamma {self.current_net_gamma:.2f} exceeds trigger {self.greeks_limits.gamma_hedge_trigger}"

        # Theta check (excessive decay)
        if self.current_net_theta < self.greeks_limits.max_daily_theta:
            return f"Daily theta decay {self.current_net_theta:.2f} exceeds limit {self.greeks_limits.max_daily_theta}"

        return None

    def can_take_trade(
        self,
        trade_info: Dict,
        position_delta: Optional[float] = None,
        position_gamma: Optional[float] = None,
        position_theta: Optional[float] = None,
    ) -> tuple:
        """
        Check if new trade is allowed based on all risk criteria + Greeks limits

        Args:
            trade_info: Dict with trade details (size, risk, symbol, etc.)
            position_delta: Delta of new position
            position_gamma: Gamma of new position
            position_theta: Theta of new position

        Returns:
            tuple: (bool, str) - (allowed, reason)
        """
        with self.risk_lock:
            # Check if trading is halted
            if self.trading_halted:
                return False, f"Trading halted: {self.halt_reason}"

            # Check daily loss limit
            if self.daily_pnl <= -self.max_daily_loss:
                self._halt_trading("Daily loss limit reached")
                return False, "Daily loss limit reached"

            # Check daily profit target
            if self.max_daily_profit > 0 and self.daily_pnl >= self.max_daily_profit:
                self._halt_trading("Daily profit target achieved")
                return False, "Daily profit target achieved"

            # Check max trades per day
            if self.trades_today >= self.max_trades_per_day:
                return False, "Max trades per day reached"

            # Check position size
            position_size = trade_info.get("quantity", 0)
            if position_size > self.max_position_size:
                return False, f"Position size exceeds limit: {position_size} > {self.max_position_size}"

            # Check Greeks limits if provided
            if position_delta is not None:
                new_net_delta = self.current_net_delta + position_delta
                if abs(new_net_delta) > self.greeks_limits.max_net_delta:
                    return (
                        False,
                        f"Would exceed max net delta: {new_net_delta:.1f} > {self.greeks_limits.max_net_delta}",
                    )

                new_gross_delta = self.current_gross_delta + abs(position_delta)
                if new_gross_delta > self.greeks_limits.max_gross_delta:
                    return (
                        False,
                        f"Would exceed max gross delta: {new_gross_delta:.1f} > {self.greeks_limits.max_gross_delta}",
                    )

            if position_gamma is not None:
                new_net_gamma = self.current_net_gamma + position_gamma
                if abs(new_net_gamma) > self.greeks_limits.max_net_gamma:
                    return (
                        False,
                        f"Would exceed max net gamma: {new_net_gamma:.2f} > {self.greeks_limits.max_net_gamma}",
                    )

            if position_theta is not None:
                new_net_theta = self.current_net_theta + position_theta
                if new_net_theta < self.greeks_limits.max_daily_theta:
                    return (
                        False,
                        f"Would exceed max theta decay: {new_net_theta:.2f} < {self.greeks_limits.max_daily_theta}",
                    )

            # Check consecutive losses
            if self.losses_in_row >= 3:
                logger.warning(f"3 consecutive losses detected")
                # Optional: Reduce position size or halt

            # Check time restrictions
            if not self._within_trading_window():
                return False, "Outside trading hours"

            # Check risk exposure
            trade_risk = trade_info.get("risk_amount", 0)
            if self.total_risk_exposure + trade_risk > config.CAPITAL * 0.1:  # Max 10% exposure
                return False, "Total risk exposure too high"

            # All checks passed
            return True, "Trade allowed"

    def get_portfolio_greeks(self) -> Dict:
        """Get current portfolio Greeks exposure"""
        with self.risk_lock:
            return {
                "net_delta": self.current_net_delta,
                "net_gamma": self.current_net_gamma,
                "net_theta": self.current_net_theta,
                "net_vega": self.current_net_vega,
                "gross_delta": self.current_gross_delta,
                "delta_utilization": abs(self.current_net_delta) / self.greeks_limits.max_net_delta * 100,
                "gamma_utilization": abs(self.current_net_gamma) / self.greeks_limits.max_net_gamma * 100,
                "needs_hedge": self._check_hedging_triggers() is not None,
            }

    def record_trade(self, trade_result):
        """
        Record trade result and update risk metrics

        Args:
            trade_result: Dict with trade outcome (pnl, symbol, quantity, etc.)
        """
        with self.risk_lock:
            pnl = trade_result.get("pnl", 0)

            # Update daily P&L
            self.daily_pnl += pnl

            # Update trade count
            self.trades_today += 1

            # Track consecutive losses
            if pnl < 0:
                self.losses_in_row += 1
            else:
                self.losses_in_row = 0

            # Store trade
            trade_result["timestamp"] = datetime.now()
            self.trade_history.append(trade_result)

            # Log
            logger.log_pnl(
                {
                    "trade_pnl": pnl,
                    "daily_pnl": self.daily_pnl,
                    "trades_count": self.trades_today,
                    "losses_in_row": self.losses_in_row,
                }
            )

            # Check if limits breached after trade
            self._check_circuit_breakers()

    def update_risk_exposure(self, exposure_change):
        """Update total risk exposure"""
        with self.risk_lock:
            self.total_risk_exposure += exposure_change
            self.total_risk_exposure = max(0, self.total_risk_exposure)

    def _check_circuit_breakers(self):
        """Check if any circuit breakers should trigger"""
        # Daily loss circuit breaker
        if self.daily_pnl <= -self.max_daily_loss:
            self._halt_trading("Daily loss limit breached")

        # Daily profit target
        if self.max_daily_profit > 0 and self.daily_pnl >= self.max_daily_profit:
            self._halt_trading("Daily profit target achieved")

        # Consecutive losses
        if self.losses_in_row >= 5:
            self._halt_trading("5 consecutive losses")

    def _halt_trading(self, reason):
        """Halt all trading"""
        self.trading_halted = True
        self.halt_reason = reason

        logger.log_risk_event(f"TRADING HALTED: {reason}")
        logger.critical(f"*** TRADING HALTED: {reason} ***")

        # TODO: Send alert/notification

    def resume_trading(self):
        """Resume trading (manual override)"""
        with self.risk_lock:
            self.trading_halted = False
            self.halt_reason = None
            logger.info("Trading resumed manually")

    def _within_trading_window(self):
        """Check if current time is within allowed trading window"""
        try:
            now = datetime.now()
            current_time = now.time()

            # Parse market hours
            start_time = time.fromisoformat(config.MARKET_START_TIME)
            end_time = time.fromisoformat(config.SQUARE_OFF_TIME)

            return start_time <= current_time <= end_time

        except Exception as e:
            logger.error(f"Error checking trading window: {e}")
            return False

    def get_daily_pnl(self):
        """Get current daily P&L"""
        with self.risk_lock:
            return self.daily_pnl

    def get_trades_count(self):
        """Get number of trades today"""
        with self.risk_lock:
            return self.trades_today

    def get_risk_metrics(self):
        """Get all risk metrics"""
        with self.risk_lock:
            return {
                "daily_pnl": self.daily_pnl,
                "trades_today": self.trades_today,
                "total_risk_exposure": self.total_risk_exposure,
                "losses_in_row": self.losses_in_row,
                "trading_halted": self.trading_halted,
                "halt_reason": self.halt_reason,
                "max_daily_loss": self.max_daily_loss,
                "max_daily_profit": self.max_daily_profit,
                "max_trades": self.max_trades_per_day,
            }

    def reset_daily_stats(self):
        """Reset daily statistics (call at start of new trading day)"""
        with self.risk_lock:
            self.daily_pnl = 0.0
            self.trades_today = 0
            self.total_risk_exposure = 0.0
            self.losses_in_row = 0
            self.trading_halted = False
            self.halt_reason = None
            self.trade_history = []

            logger.info("Daily risk statistics reset")

    def check_position_risk(self, position_size, entry_price, stop_loss):
        """
        Validate if position risk is acceptable

        Returns:
            tuple: (bool, str) - (acceptable, reason)
        """
        try:
            # Calculate position risk
            risk_per_unit = abs(entry_price - stop_loss)
            total_risk = position_size * risk_per_unit

            # Check against max loss
            if total_risk > self.max_daily_loss * 0.5:  # Single trade shouldn't risk more than 50% of daily limit
                return False, f"Single trade risk too high: {total_risk}"

            # Check against capital
            risk_pct = (total_risk / config.CAPITAL) * 100
            if risk_pct > config.RISK_PER_TRADE * 100:
                return False, f"Risk percentage too high: {risk_pct:.2f}%"

            return True, "Position risk acceptable"

        except Exception as e:
            logger.error(f"Error checking position risk: {e}")
            return False, "Error validating risk"

    def is_trading_allowed(self):
        """Simple check if trading is currently allowed"""
        with self.risk_lock:
            return not self.trading_halted and self._within_trading_window()

    def get_remaining_trades(self):
        """Get number of trades remaining for the day"""
        with self.risk_lock:
            return max(0, self.max_trades_per_day - self.trades_today)

    def get_remaining_loss_capacity(self):
        """Get remaining loss capacity before hitting limit"""
        with self.risk_lock:
            return max(0, self.max_daily_loss + self.daily_pnl)
