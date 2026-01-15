"""
PHASE 8: Risk Calibration Engine
Adaptive risk management based on streaks, volatility, and drawdown
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import math


@dataclass
class RiskProfile:
    """Current risk parameters"""

    position_size_multiplier: float = 1.0
    max_trades_per_day: int = 10
    risk_per_trade_pct: float = 2.0
    cooldown_minutes: int = 5
    max_concurrent_trades: int = 3
    stop_loss_multiplier: float = 1.0


class StreakBasedRiskManager:
    """
    Adjust risk based on win/loss streaks
    Protect capital during losing streaks
    """

    def __init__(self):
        self.current_streak = 0  # Positive = wins, negative = losses
        self.base_risk_pct = 2.0

    def update_streak(self, won: bool):
        """Update streak counter"""
        if won:
            if self.current_streak > 0:
                self.current_streak += 1
            else:
                self.current_streak = 1
        else:
            if self.current_streak < 0:
                self.current_streak -= 1
            else:
                self.current_streak = -1

    def get_risk_multiplier(self) -> float:
        """
        Calculate risk multiplier based on streak
        Loss streak → reduce risk
        Win streak → keep stable (don't over-leverage)
        """
        if self.current_streak >= 0:
            # Winning or neutral - normal risk
            return 1.0

        # Losing streak - reduce risk progressively
        loss_streak = abs(self.current_streak)

        if loss_streak == 1:
            return 0.9  # 10% reduction
        elif loss_streak == 2:
            return 0.75  # 25% reduction
        elif loss_streak == 3:
            return 0.5  # 50% reduction
        elif loss_streak >= 4:
            return 0.25  # 75% reduction - near stop

        return 1.0

    def should_pause_trading(self) -> bool:
        """Pause trading after severe losing streak"""
        return self.current_streak <= -5


class VolatilityBasedRiskManager:
    """
    Adjust risk based on market volatility
    High volatility = reduce position size
    """

    def __init__(self):
        self.volatility_history: List[float] = []
        self.max_history = 20

    def update_volatility(self, current_iv: float):
        """Track IV levels"""
        self.volatility_history.append(current_iv)
        if len(self.volatility_history) > self.max_history:
            self.volatility_history.pop(0)

    def get_volatility_regime(self) -> str:
        """Classify volatility level"""
        if len(self.volatility_history) < 5:
            return "NORMAL"

        avg_iv = sum(self.volatility_history) / len(self.volatility_history)
        current_iv = self.volatility_history[-1]

        # Compare current to average
        ratio = current_iv / avg_iv

        if ratio > 1.5:
            return "EXTREME"
        elif ratio > 1.2:
            return "HIGH"
        elif ratio < 0.8:
            return "LOW"
        else:
            return "NORMAL"

    def get_volatility_multiplier(self) -> float:
        """
        Risk multiplier based on volatility
        High vol = reduce size
        """
        regime = self.get_volatility_regime()

        multipliers = {
            "LOW": 1.1,  # Slightly larger positions
            "NORMAL": 1.0,
            "HIGH": 0.7,  # Reduce by 30%
            "EXTREME": 0.4,  # Reduce by 60%
        }

        return multipliers.get(regime, 1.0)

    def get_max_trades_adjustment(self) -> int:
        """Adjust max trades based on volatility"""
        regime = self.get_volatility_regime()

        adjustments = {"LOW": 12, "NORMAL": 10, "HIGH": 7, "EXTREME": 4}

        return adjustments.get(regime, 10)


class DrawdownProtection:
    """
    Implement tiered drawdown protection
    Reduce risk as drawdown increases
    """

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.peak_capital = initial_capital
        self.current_capital = initial_capital

        # Drawdown tiers
        self.tier_thresholds = [5, 10, 15, 20]  # Drawdown %
        self.tier_multipliers = [0.8, 0.5, 0.25, 0.0]  # Risk reduction

    def update_capital(self, pnl: float):
        """Update capital and track drawdown"""
        self.current_capital += pnl

        if self.current_capital > self.peak_capital:
            self.peak_capital = self.current_capital

    def get_drawdown_pct(self) -> float:
        """Calculate current drawdown %"""
        if self.peak_capital == 0:
            return 0.0

        drawdown = (self.peak_capital - self.current_capital) / self.peak_capital * 100
        return max(0, drawdown)

    def get_drawdown_tier(self) -> int:
        """Get current drawdown tier (0-4)"""
        dd = self.get_drawdown_pct()

        for i, threshold in enumerate(self.tier_thresholds):
            if dd < threshold:
                return i

        return len(self.tier_thresholds)  # Worst tier

    def get_drawdown_multiplier(self) -> float:
        """Risk multiplier based on drawdown"""
        tier = self.get_drawdown_tier()

        if tier >= len(self.tier_multipliers):
            return 0.0  # Stop trading

        return self.tier_multipliers[tier]

    def should_stop_trading(self) -> bool:
        """Check if drawdown is too severe"""
        return self.get_drawdown_pct() >= self.tier_thresholds[-1]


class DynamicCooldown:
    """
    Adaptive cooldown based on loss severity
    Big loss = longer cooldown
    """

    def __init__(self):
        self.last_trade_time: Optional[datetime] = None
        self.last_trade_pnl: float = 0.0
        self.base_cooldown_minutes = 5

    def record_trade(self, pnl: float):
        """Record trade completion"""
        self.last_trade_time = datetime.now()
        self.last_trade_pnl = pnl

    def get_required_cooldown(self) -> int:
        """
        Calculate required cooldown in minutes
        Larger loss = longer cooldown
        """
        if self.last_trade_pnl >= 0:
            # Win or breakeven - minimal cooldown
            return self.base_cooldown_minutes

        # Loss - scale cooldown by severity
        loss_severity = abs(self.last_trade_pnl)

        if loss_severity < 500:
            return self.base_cooldown_minutes
        elif loss_severity < 1000:
            return self.base_cooldown_minutes * 2
        elif loss_severity < 2000:
            return self.base_cooldown_minutes * 3
        else:
            return self.base_cooldown_minutes * 4  # Big loss

    def can_trade_now(self) -> bool:
        """Check if cooldown period has passed"""
        if not self.last_trade_time:
            return True

        required_cooldown = self.get_required_cooldown()
        time_since_trade = (datetime.now() - self.last_trade_time).total_seconds() / 60

        return time_since_trade >= required_cooldown

    def get_remaining_cooldown_seconds(self) -> int:
        """Get remaining cooldown time"""
        if not self.last_trade_time:
            return 0

        required_minutes = self.get_required_cooldown()
        elapsed_minutes = (datetime.now() - self.last_trade_time).total_seconds() / 60
        remaining_minutes = max(0, required_minutes - elapsed_minutes)

        return int(remaining_minutes * 60)


class TimeBasedRiskManager:
    """
    Adjust risk based on time of day and session progress
    """

    def __init__(self):
        self.session_start_time = datetime.now()
        self.trades_today = 0

    def reset_session(self):
        """Reset for new trading day"""
        self.session_start_time = datetime.now()
        self.trades_today = 0

    def get_time_multiplier(self) -> float:
        """
        Risk multiplier based on time of day
        Reduce risk during opening/closing
        """
        now = datetime.now().time()

        # Opening hour (9:15-10:15)
        if now.hour == 9 or (now.hour == 10 and now.minute < 15):
            return 0.7  # Reduce risk

        # Closing hour (14:30-15:30)
        elif now.hour == 14 and now.minute >= 30:
            return 0.6
        elif now.hour == 15:
            return 0.5  # Very low risk near close

        # Normal hours
        else:
            return 1.0

    def should_stop_new_trades(self) -> bool:
        """Check if too late in day for new trades"""
        now = datetime.now().time()

        # Stop new trades after 3:00 PM
        if now.hour >= 15:
            return True

        return False

    def get_trade_limit_multiplier(self) -> float:
        """
        Adjust max trades based on session progress
        Reduce limit if already traded a lot
        """
        if self.trades_today <= 3:
            return 1.0
        elif self.trades_today <= 6:
            return 0.8
        elif self.trades_today <= 9:
            return 0.6
        else:
            return 0.4  # Slow down significantly


class RiskCalibrationEngine:
    """
    Master risk calibrator
    Combines all adaptive risk components
    """

    def __init__(self, initial_capital: float = 100000):
        self.streak_manager = StreakBasedRiskManager()
        self.volatility_manager = VolatilityBasedRiskManager()
        self.drawdown_protection = DrawdownProtection(initial_capital)
        self.cooldown_manager = DynamicCooldown()
        self.time_manager = TimeBasedRiskManager()

        # Base risk parameters
        self.base_profile = RiskProfile()

        # Emergency stop
        self.emergency_stop_active = False

    def update_trade_result(self, pnl: float):
        """Update all managers with trade result"""
        won = pnl > 0

        self.streak_manager.update_streak(won)
        self.drawdown_protection.update_capital(pnl)
        self.cooldown_manager.record_trade(pnl)
        self.time_manager.trades_today += 1

    def update_market_volatility(self, iv: float):
        """Update volatility tracking"""
        self.volatility_manager.update_volatility(iv)

    def get_calibrated_risk_profile(self) -> RiskProfile:
        """
        Calculate current risk profile
        Applies all adaptive adjustments
        """
        profile = RiskProfile()

        # Start with base values
        profile.position_size_multiplier = self.base_profile.position_size_multiplier
        profile.risk_per_trade_pct = self.base_profile.risk_per_trade_pct
        profile.max_trades_per_day = self.base_profile.max_trades_per_day

        # Apply streak adjustment
        streak_mult = self.streak_manager.get_risk_multiplier()
        profile.position_size_multiplier *= streak_mult

        # Apply volatility adjustment
        vol_mult = self.volatility_manager.get_volatility_multiplier()
        profile.position_size_multiplier *= vol_mult

        # Apply drawdown protection
        dd_mult = self.drawdown_protection.get_drawdown_multiplier()
        profile.position_size_multiplier *= dd_mult

        # Apply time-based adjustment
        time_mult = self.time_manager.get_time_multiplier()
        profile.position_size_multiplier *= time_mult

        # Adjust max trades
        profile.max_trades_per_day = self.volatility_manager.get_max_trades_adjustment()
        profile.max_trades_per_day = int(profile.max_trades_per_day * self.time_manager.get_trade_limit_multiplier())

        # Cooldown
        profile.cooldown_minutes = self.cooldown_manager.get_required_cooldown()

        # Stop loss adjustment for high volatility
        vol_regime = self.volatility_manager.get_volatility_regime()
        if vol_regime in ["HIGH", "EXTREME"]:
            profile.stop_loss_multiplier = 1.5  # Wider stops

        return profile

    def can_take_trade(self) -> Dict:
        """
        Check if allowed to take new trade
        Returns: {allowed: bool, reason: str}
        """
        # Emergency stop
        if self.emergency_stop_active:
            return {"allowed": False, "reason": "Emergency stop active"}

        # Drawdown check
        if self.drawdown_protection.should_stop_trading():
            return {
                "allowed": False,
                "reason": f"Max drawdown exceeded: {self.drawdown_protection.get_drawdown_pct():.1f}%",
            }

        # Streak check
        if self.streak_manager.should_pause_trading():
            return {"allowed": False, "reason": f"Severe losing streak: {abs(self.streak_manager.current_streak)}"}

        # Cooldown check
        if not self.cooldown_manager.can_trade_now():
            remaining = self.cooldown_manager.get_remaining_cooldown_seconds()
            return {"allowed": False, "reason": f"Cooldown active: {remaining}s remaining"}

        # Time check
        if self.time_manager.should_stop_new_trades():
            return {"allowed": False, "reason": "Too late in session"}

        # Trade limit check
        profile = self.get_calibrated_risk_profile()
        if self.time_manager.trades_today >= profile.max_trades_per_day:
            return {"allowed": False, "reason": f"Daily trade limit reached: {self.time_manager.trades_today}"}

        return {"allowed": True, "reason": "All checks passed"}

    def get_position_size(self, account_capital: float, option_price: float) -> int:
        """
        Calculate position size with all adjustments
        Returns number of lots
        """
        profile = self.get_calibrated_risk_profile()

        # Risk amount
        risk_amount = account_capital * (profile.risk_per_trade_pct / 100)
        risk_amount *= profile.position_size_multiplier

        # Lots calculation
        risk_per_lot = option_price * 15  # Assuming Nifty lot size
        lots = int(risk_amount / risk_per_lot)

        # Minimum 1 lot
        return max(1, lots)

    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk status"""
        profile = self.get_calibrated_risk_profile()
        trade_check = self.can_take_trade()

        return {
            "can_trade": trade_check["allowed"],
            "reason": trade_check["reason"],
            "current_profile": {
                "position_multiplier": profile.position_size_multiplier,
                "max_trades_today": profile.max_trades_per_day,
                "cooldown_minutes": profile.cooldown_minutes,
                "risk_per_trade_pct": profile.risk_per_trade_pct,
            },
            "components": {
                "streak": self.streak_manager.current_streak,
                "volatility_regime": self.volatility_manager.get_volatility_regime(),
                "drawdown_pct": self.drawdown_protection.get_drawdown_pct(),
                "trades_today": self.time_manager.trades_today,
            },
            "multipliers": {
                "streak": self.streak_manager.get_risk_multiplier(),
                "volatility": self.volatility_manager.get_volatility_multiplier(),
                "drawdown": self.drawdown_protection.get_drawdown_multiplier(),
                "time": self.time_manager.get_time_multiplier(),
            },
        }

    def activate_emergency_stop(self):
        """Manually activate emergency stop"""
        self.emergency_stop_active = True

    def deactivate_emergency_stop(self):
        """Deactivate emergency stop"""
        self.emergency_stop_active = False

    def reset_daily(self):
        """Reset for new trading day"""
        self.time_manager.reset_session()
        # Don't reset streak/drawdown - those persist across days
