"""
PHASE 8.3 & 8.4: Market-Aware Signal Strictness + Win/Loss Risk Adjustment
Dynamic adaptation based on market conditions and recent performance
"""

from typing import Dict, Optional
from datetime import datetime, time as dt_time
from enum import Enum


class MarketSession(Enum):
    """Market session types"""

    OPENING = "opening"  # 9:15-10:00
    MORNING = "morning"  # 10:00-11:30
    LUNCH = "lunch"  # 11:30-14:00
    AFTERNOON = "afternoon"  # 14:00-15:00
    CLOSING = "closing"  # 15:00-15:30


class VolatilityRegime(Enum):
    """Volatility classification"""

    VERY_LOW = "very_low"  # IV < 15
    LOW = "low"  # IV 15-20
    NORMAL = "normal"  # IV 20-30
    HIGH = "high"  # IV 30-40
    EXTREME = "extreme"  # IV > 40


class MarketAwareStrictness:
    """
    Adjust signal strictness based on market conditions
    High volatility → strict rules
    Low volatility → extra confirmation
    Lunch session → almost no trade
    """

    def __init__(self):
        self.base_bias_threshold = 0.65
        self.base_oi_threshold = 1500
        self.base_trap_threshold = 0.70

    def get_current_session(self) -> MarketSession:
        """Identify current market session"""
        now = datetime.now().time()

        if dt_time(9, 15) <= now < dt_time(10, 0):
            return MarketSession.OPENING
        elif dt_time(10, 0) <= now < dt_time(11, 30):
            return MarketSession.MORNING
        elif dt_time(11, 30) <= now < dt_time(14, 0):
            return MarketSession.LUNCH
        elif dt_time(14, 0) <= now < dt_time(15, 0):
            return MarketSession.AFTERNOON
        else:
            return MarketSession.CLOSING

    def get_volatility_regime(self, current_iv: float) -> VolatilityRegime:
        """Classify current volatility"""
        if current_iv < 15:
            return VolatilityRegime.VERY_LOW
        elif current_iv < 20:
            return VolatilityRegime.LOW
        elif current_iv < 30:
            return VolatilityRegime.NORMAL
        elif current_iv < 40:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME

    def get_session_multiplier(self, session: Optional[MarketSession] = None) -> float:
        """
        Strictness multiplier by session
        Higher = stricter (harder to pass)
        """
        if session is None:
            session = self.get_current_session()

        multipliers = {
            MarketSession.OPENING: 1.4,  # Very strict - false moves
            MarketSession.MORNING: 1.0,  # Normal - best trading
            MarketSession.LUNCH: 2.0,  # Almost block - choppy
            MarketSession.AFTERNOON: 1.2,  # Slightly strict
            MarketSession.CLOSING: 1.5,  # Very strict - erratic
        }

        return multipliers.get(session, 1.0)

    def get_volatility_multiplier(self, iv: float) -> float:
        """
        Strictness multiplier by volatility
        High volatility = stricter rules
        """
        regime = self.get_volatility_regime(iv)

        multipliers = {
            VolatilityRegime.VERY_LOW: 1.3,  # Low vol = need more confirmation
            VolatilityRegime.LOW: 1.1,
            VolatilityRegime.NORMAL: 1.0,
            VolatilityRegime.HIGH: 1.3,  # High vol = much stricter
            VolatilityRegime.EXTREME: 1.6,  # Extreme vol = very strict
        }

        return multipliers.get(regime, 1.0)

    def get_adjusted_thresholds(self, current_iv: float) -> Dict:
        """
        Get dynamically adjusted thresholds
        Returns all thresholds adapted to current market
        """
        session_mult = self.get_session_multiplier()
        vol_mult = self.get_volatility_multiplier(current_iv)

        # Combined multiplier
        total_mult = session_mult * vol_mult

        return {
            "bias_threshold": self.base_bias_threshold * total_mult,
            "oi_threshold": self.base_oi_threshold * total_mult,
            "trap_threshold": self.base_trap_threshold * total_mult,
            "session": self.get_current_session().value,
            "volatility": self.get_volatility_regime(current_iv).value,
            "strictness_multiplier": total_mult,
        }

    def should_pause_trading(self, current_iv: float) -> Dict:
        """
        Check if should pause trading due to market conditions

        Pause during:
        - Lunch session (11:30-14:00)
        - Extreme volatility
        """
        session = self.get_current_session()
        vol_regime = self.get_volatility_regime(current_iv)

        pause = False
        reason = None

        # Lunch session - almost no trading
        if session == MarketSession.LUNCH:
            pause = True
            reason = "Lunch session - choppy market"

        # Extreme volatility
        elif vol_regime == VolatilityRegime.EXTREME:
            pause = True
            reason = f"Extreme volatility (IV: {current_iv:.1f})"

        return {"should_pause": pause, "reason": reason, "session": session.value, "volatility": vol_regime.value}


class WinLossRiskAdjuster:
    """
    Adjust risk based on recent win/loss pattern
    2 wins → same risk
    1 loss → risk reduce
    2 losses → trading pause
    """

    def __init__(self):
        self.trade_history = []  # List of (pnl, timestamp)
        self.max_history = 10

        self.base_risk_pct = 2.0  # 2% base risk
        self.min_risk_pct = 0.5  # 0.5% minimum

        self.pause_after_losses = 2  # Pause after 2 consecutive losses
        self.recovery_mode = False

    def record_trade(self, pnl: float):
        """Record trade result"""
        self.trade_history.append({"pnl": pnl, "is_win": pnl > 0, "timestamp": datetime.now()})

        # Keep only recent history
        if len(self.trade_history) > self.max_history:
            self.trade_history.pop(0)

        # Check if need recovery mode
        self._update_recovery_mode()

    def _update_recovery_mode(self):
        """Update recovery mode based on recent results"""
        if len(self.trade_history) < self.pause_after_losses:
            self.recovery_mode = False
            return

        # Check last N trades
        recent = self.trade_history[-self.pause_after_losses :]
        all_losses = all(not trade["is_win"] for trade in recent)

        if all_losses:
            self.recovery_mode = True
        else:
            # Exit recovery if won
            if self.trade_history[-1]["is_win"]:
                self.recovery_mode = False

    def get_consecutive_losses(self) -> int:
        """Count consecutive losses from end"""
        count = 0
        for trade in reversed(self.trade_history):
            if not trade["is_win"]:
                count += 1
            else:
                break
        return count

    def get_consecutive_wins(self) -> int:
        """Count consecutive wins from end"""
        count = 0
        for trade in reversed(self.trade_history):
            if trade["is_win"]:
                count += 1
            else:
                break
        return count

    def get_adjusted_risk_pct(self) -> float:
        """
        Calculate risk % based on recent performance

        Pattern:
        - 2+ wins: Normal risk (2%)
        - 1 loss: Reduced risk (1.5%)
        - 2+ losses: Minimum risk (0.5%) or pause
        """
        consecutive_losses = self.get_consecutive_losses()
        consecutive_wins = self.get_consecutive_wins()

        if self.recovery_mode:
            # Recovery mode - very conservative
            return self.min_risk_pct

        if consecutive_losses == 0:
            # Winning streak or neutral
            return self.base_risk_pct

        elif consecutive_losses == 1:
            # One loss - reduce by 25%
            return self.base_risk_pct * 0.75

        else:
            # Multiple losses - minimum risk
            return self.min_risk_pct

    def should_pause_trading(self) -> Dict:
        """
        Check if should pause due to losses

        Pause after 2 consecutive losses
        """
        consecutive_losses = self.get_consecutive_losses()

        pause = consecutive_losses >= self.pause_after_losses

        return {
            "should_pause": pause,
            "reason": f"{consecutive_losses} consecutive losses" if pause else None,
            "consecutive_losses": consecutive_losses,
            "recovery_mode": self.recovery_mode,
        }

    def get_risk_summary(self) -> Dict:
        """Get comprehensive risk status"""
        total_trades = len(self.trade_history)

        if total_trades == 0:
            win_rate = 0
        else:
            wins = sum(1 for t in self.trade_history if t["is_win"])
            win_rate = (wins / total_trades) * 100

        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "consecutive_wins": self.get_consecutive_wins(),
            "consecutive_losses": self.get_consecutive_losses(),
            "current_risk_pct": self.get_adjusted_risk_pct(),
            "recovery_mode": self.recovery_mode,
            "pause_recommended": self.should_pause_trading()["should_pause"],
        }

    def reset_recovery_mode(self):
        """Manually reset recovery mode (e.g., new day)"""
        self.recovery_mode = False


class AdaptiveStrictnessEngine:
    """
    Combined market-aware strictness + win/loss risk adjustment
    Complete adaptive decision making
    """

    def __init__(self):
        self.market_strictness = MarketAwareStrictness()
        self.risk_adjuster = WinLossRiskAdjuster()

    def evaluate_trading_conditions(self, current_iv: float, recent_pnl: Optional[float] = None) -> Dict:
        """
        Complete evaluation of whether to trade

        Returns comprehensive decision with reasons
        """
        # Update risk adjuster if new trade result
        if recent_pnl is not None:
            self.risk_adjuster.record_trade(recent_pnl)

        # Get market-based pause check
        market_pause = self.market_strictness.should_pause_trading(current_iv)

        # Get loss-based pause check
        loss_pause = self.risk_adjuster.should_pause_trading()

        # Get adjusted parameters
        thresholds = self.market_strictness.get_adjusted_thresholds(current_iv)
        risk_pct = self.risk_adjuster.get_adjusted_risk_pct()

        # Determine if should trade
        should_pause = market_pause["should_pause"] or loss_pause["should_pause"]

        pause_reasons = []
        if market_pause["should_pause"]:
            pause_reasons.append(market_pause["reason"])
        if loss_pause["should_pause"]:
            pause_reasons.append(loss_pause["reason"])

        return {
            "can_trade": not should_pause,
            "pause_reasons": pause_reasons,
            "thresholds": thresholds,
            "risk_pct": risk_pct,
            "market_conditions": {
                "session": thresholds["session"],
                "volatility": thresholds["volatility"],
                "strictness": thresholds["strictness_multiplier"],
            },
            "performance_status": self.risk_adjuster.get_risk_summary(),
        }

    def get_signal_requirements(self, current_iv: float) -> Dict:
        """
        Get current requirements for a valid signal
        All dynamically adjusted
        """
        thresholds = self.market_strictness.get_adjusted_thresholds(current_iv)

        # Cap thresholds at reasonable maximums
        return {
            "min_bias_strength": min(0.85, thresholds["bias_threshold"]),
            "min_oi_delta": min(5000, int(thresholds["oi_threshold"])),
            "max_trap_probability": min(0.9, thresholds["trap_threshold"]),
            "strictness_level": thresholds["strictness_multiplier"],
            "session": thresholds["session"],
        }
