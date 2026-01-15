"""
PHASE 5 — Time Intelligence Gate & Volatility/Theta Guard

Blocks trades based on:
1. Time Windows (9:20-11:15 OK, 11:15-12:00 caution, post 12:00 blocked)
2. Theta spike detection
3. IV crush detection
4. Gamma exhaustion
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime, time
from src.utils.market_bias_models import TimeWindow, ThetaVelocityAlert, Phase5Config
import logging

logger = logging.getLogger(__name__)


class TimeIntelligenceGate:
    """
    Manages intraday time windows for trading eligibility
    """

    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        self.time_checks_history = []

    def analyze_time_window(self, current_time: Optional[time] = None) -> Tuple[TimeWindow, bool, str]:
        """
        Analyze current time and determine trading window

        Returns:
            - TimeWindow enum
            - Is trading allowed? (bool)
            - Recommendation string
        """

        if current_time is None:
            current_time = datetime.now().time()

        # Check morning window (9:20-11:15)
        if self.config.morning_start <= current_time < self.config.morning_end:
            return (TimeWindow.ALLOWED, True, "Morning window - Full trading allowed")

        # Check caution window (11:15-12:00)
        if self.config.caution_start <= current_time < self.config.caution_end:
            return (TimeWindow.CAUTION, True, "Caution window - Apply high filter, theta rising")

        # Check theta danger zone (post 12:00)
        if current_time >= self.config.theta_danger_start:
            return (TimeWindow.THETA_DANGER, False, "Theta danger zone - NO TRADE after 12:00 (theta crush risk)")

        # Pre-market or after hours
        if current_time < self.config.morning_start:
            return (TimeWindow.PRE_MARKET, False, "Pre-market - trading not started yet")

        return (TimeWindow.AFTER_HOURS, False, "After market hours - trading ended")

    def get_time_filter_strictness(self, time_window: TimeWindow) -> float:
        """
        Get filter strictness for this time window

        Returns: [0-1] where higher = stricter filtering
        """

        if time_window == TimeWindow.ALLOWED:
            return 0.3  # Relaxed filtering
        elif time_window == TimeWindow.CAUTION:
            return 0.7  # Strict filtering
        elif time_window == TimeWindow.THETA_DANGER:
            return 1.0  # Maximum filtering (no trades)
        else:
            return 1.0  # No trades outside main windows

    def get_time_decay_factor(self, current_time: Optional[time] = None) -> float:
        """
        Get theta decay intensity factor as day progresses

        Returns: [0-1] where higher = more theta decay pressure
        """

        if current_time is None:
            current_time = datetime.now().time()

        # Early morning: low theta
        if current_time < time(10, 0):
            return 0.1

        # Mid-morning: moderate theta
        if current_time < time(11, 0):
            return 0.3

        # Late morning: elevated theta
        if current_time < time(12, 0):
            return 0.6

        # Post noon: maximum theta
        if current_time < time(14, 0):
            return 0.9

        # Late afternoon: extreme theta
        return 0.95


class VolatilityAndThetaGuard:
    """
    Detects and guards against:
    - Theta spike (rapid worsening)
    - IV crush (rapid IV decline)
    - Gamma exhaustion (gamma too low)
    """

    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        self.theta_history = []
        self.iv_history = []
        self.gamma_history = []
        self.max_history = 20

    def analyze_theta_velocity(
        self,
        theta_current: float,
        theta_previous: float,
        gamma_current: float,
        iv_current: float,
        iv_previous: float,
    ) -> ThetaVelocityAlert:
        """
        Analyze Greeks velocity and detect dangerous conditions

        Returns ThetaVelocityAlert with warnings and safety assessment
        """

        # Track history
        self.theta_history.append(theta_current)
        self.iv_history.append(iv_current)
        self.gamma_history.append(gamma_current)

        if len(self.theta_history) > self.max_history:
            self.theta_history.pop(0)
            self.iv_history.pop(0)
            self.gamma_history.pop(0)

        warnings = []

        # Check 1: Theta spike
        theta_spike_detected = False
        theta_change = theta_current - theta_previous

        if theta_change < -0.2:  # Theta worsening rapidly
            theta_spike_detected = True
            warnings.append(f"⚠️ Theta spike detected: {theta_change:.3f}")

        # Check 2: IV crush
        iv_crush_detected = False
        iv_change = iv_current - iv_previous

        if iv_change < -0.05:  # IV declining rapidly
            iv_crush_detected = True
            warnings.append(f"⚠️ IV crush detected: {iv_change:.3f}")

        # Check 3: Gamma exhaustion
        gamma_exhausted = gamma_current < self.config.max_gamma_exhaustion

        if gamma_exhausted:
            warnings.append(f"⚠️ Gamma exhausted: {gamma_current:.5f}")

        # Check 4: Extreme theta
        if theta_current < self.config.max_theta_threshold:
            warnings.append(f"⚠️ Theta too aggressive: {theta_current:.3f}")

        # Overall safety assessment
        safe_to_trade = (
            not theta_spike_detected
            and not iv_crush_detected
            and not gamma_exhausted
            and theta_current >= self.config.max_theta_threshold
        )

        alert = ThetaVelocityAlert(
            theta_current=theta_current,
            theta_previous=theta_previous,
            theta_spike_detected=theta_spike_detected,
            gamma_current=gamma_current,
            gamma_exhausted=gamma_exhausted,
            iv_crush_detected=iv_crush_detected,
            iv_current=iv_current,
            iv_previous=iv_previous,
            safe_to_trade=safe_to_trade,
            warnings=warnings,
            timestamp=datetime.now(),
        )

        return alert

    def get_theta_trend(self) -> str:
        """
        Analyze theta trend over last few ticks

        Returns: "worsening" | "improving" | "stable"
        """
        if len(self.theta_history) < 2:
            return "insufficient_data"

        recent = self.theta_history[-5:]  # Last 5 readings

        if len(recent) < 2:
            return "insufficient_data"

        # Calculate trend
        first_half_avg = sum(recent[: len(recent) // 2]) / (len(recent) // 2)
        second_half_avg = sum(recent[len(recent) // 2 :]) / (len(recent) - len(recent) // 2)

        diff = first_half_avg - second_half_avg  # Negative = worsening (more negative)

        if diff < -0.05:
            return "worsening"
        elif diff > 0.05:
            return "improving"
        else:
            return "stable"

    def get_iv_trend(self) -> str:
        """
        Analyze IV trend

        Returns: "crushing" | "rising" | "stable"
        """
        if len(self.iv_history) < 2:
            return "insufficient_data"

        recent = self.iv_history[-5:]

        if len(recent) < 2:
            return "insufficient_data"

        first_half_avg = sum(recent[: len(recent) // 2]) / (len(recent) // 2)
        second_half_avg = sum(recent[len(recent) // 2 :]) / (len(recent) - len(recent) // 2)

        diff = second_half_avg - first_half_avg  # Positive = rising

        if diff < -0.02:
            return "crushing"
        elif diff > 0.02:
            return "rising"
        else:
            return "stable"

    def get_risk_assessment(self) -> Dict[str, str]:
        """Get overall risk assessment"""

        return {
            "theta_trend": self.get_theta_trend(),
            "iv_trend": self.get_iv_trend(),
        }

    def reset(self):
        """Clear history"""
        self.theta_history.clear()
        self.iv_history.clear()
        self.gamma_history.clear()


class CombinedTimeAndGreeksGate:
    """
    Combined gate that checks both time window and Greeks safety
    """

    def __init__(self, config: Phase5Config = None):
        self.config = config or Phase5Config()
        self.time_gate = TimeIntelligenceGate(config)
        self.theta_guard = VolatilityAndThetaGuard(config)

    def get_eligibility(
        self,
        theta_current: float,
        theta_previous: float,
        gamma_current: float,
        iv_current: float,
        iv_previous: float,
        current_time: Optional[time] = None,
    ) -> Tuple[bool, List[str]]:
        """
        Get overall eligibility based on time + Greeks

        Returns:
            - Eligible? (bool)
            - List of blocking reasons (empty if eligible)
        """

        blocks = []

        # Check 1: Time window
        time_window, time_allowed, time_reason = self.time_gate.analyze_time_window(current_time)

        if not time_allowed:
            blocks.append(f"TIME: {time_reason}")

        # Check 2: Theta & Greeks
        if time_allowed:  # Only check if time is OK
            theta_alert = self.theta_guard.analyze_theta_velocity(
                theta_current, theta_previous, gamma_current, iv_current, iv_previous
            )

            if not theta_alert.safe_to_trade:
                for warning in theta_alert.warnings:
                    blocks.append(f"GREEKS: {warning}")

        eligible = len(blocks) == 0

        return eligible, blocks
