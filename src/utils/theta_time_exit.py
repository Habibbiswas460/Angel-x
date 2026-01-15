"""
PHASE 7 — THETA DECAY & TIME-BASED EXIT

Time bomb detection
Scalping: in & out
No over-holding
"""

from datetime import datetime, time
from typing import Optional, Tuple
from src.utils.exit_models import ThetaDecayMonitor, ThetaExitSignal, Phase7Config


class ThetaDecayExitEngine:
    """
    Theta decay is silent killer in scalping

    Rules:
    1. If theta spiking → exit
    2. If holding > max time → exit
    3. If IV crushing → exit
    4. Time > limit always wins
    """

    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()

    # ====================================================================
    # STEP 1: THETA ACCELERATION DETECTION
    # ====================================================================

    def detect_theta_acceleration(
        self,
        theta_current: float,
        theta_prev: float,
        time_since_update_secs: float = 60.0,
    ) -> Tuple[bool, float, str]:
        """
        Detect if theta is accelerating (getting worse)
        """

        if time_since_update_secs == 0:
            return False, 0.0, "Not enough time"

        # Calculate theta change per minute
        theta_per_minute = (theta_current - theta_prev) / (time_since_update_secs / 60.0)

        # If theta getting worse (more negative) too fast
        if theta_per_minute < -0.05:  # Losing >0.05 per minute
            acceleration = abs(theta_per_minute)
            return True, acceleration, f"Theta accelerating at -{acceleration:.3f}/min"

        return False, 0.0, f"Theta stable ({theta_per_minute:.3f}/min)"

    # ====================================================================
    # STEP 2: TIME LIMIT CHECK
    # ====================================================================

    def check_time_exceeded(
        self,
        entry_time: datetime,
        current_time: datetime,
    ) -> Tuple[bool, int, str]:
        """
        Check if holding time exceeded limit
        """

        elapsed_secs = int((current_time - entry_time).total_seconds())
        max_secs = self.config.max_holding_seconds

        if elapsed_secs > max_secs:
            excess = elapsed_secs - max_secs
            return True, elapsed_secs, f"Time limit exceeded by {excess}s ({elapsed_secs}s > {max_secs}s)"

        percent_used = (elapsed_secs / max_secs) * 100
        return False, elapsed_secs, f"Time {percent_used:.0f}% used ({elapsed_secs}s)"

    # ====================================================================
    # STEP 3: IV CRUSH DETECTION
    # ====================================================================

    def detect_iv_crush(
        self,
        iv_current: float,
        iv_entry: float,
    ) -> Tuple[bool, float, str]:
        """
        Detect if IV is crushing (collapsing)
        """

        if iv_entry == 0:
            return False, 0.0, "No entry IV"

        iv_change_percent = ((iv_current - iv_entry) / iv_entry) * 100

        # IV dropped >10% = crush territory
        if iv_change_percent < -10:
            return True, abs(iv_change_percent), f"IV crush: {iv_current:.1%} (was {iv_entry:.1%}), -10.0% threshold"

        return False, 0.0, f"IV: {iv_current:.1%} (change {iv_change_percent:+.1f}%)"

    # ====================================================================
    # STEP 4: COMBINED THETA EXIT CHECK
    # ====================================================================

    def should_exit_theta(
        self,
        theta_current: float,
        theta_prev: float,
        entry_time: datetime,
        current_time: datetime,
        iv_current: float,
        iv_entry: float,
        time_since_update_secs: float = 60.0,
    ) -> Tuple[bool, Optional[ThetaExitSignal], float, str]:
        """
        Check all theta-related exit signals
        Returns: (should_exit, signal, confidence, reason)
        """

        # Check 1: Theta acceleration
        theta_accel, accel_rate, theta_msg = self.detect_theta_acceleration(
            theta_current, theta_prev, time_since_update_secs
        )

        if theta_accel and accel_rate > 0.08:
            return (
                True,
                ThetaExitSignal.THETA_ACCELERATION,
                0.95,
                f"Theta accelerating at -{accel_rate:.3f}/min - immediate exit",
            )

        # Check 2: Time exceeded
        time_exceeded, elapsed, time_msg = self.check_time_exceeded(entry_time, current_time)

        if time_exceeded:
            return (
                True,
                ThetaExitSignal.TIME_WINDOW_EXCEEDED,
                0.99,
                f"Time limit exceeded: {elapsed}s > {self.config.max_holding_seconds}s",
            )

        # Check 3: IV crush
        iv_crush, crush_percent, iv_msg = self.detect_iv_crush(iv_current, iv_entry)

        if iv_crush:
            return True, ThetaExitSignal.IV_CRUSH_DETECTED, 0.90, f"IV crush {crush_percent:.1f}% - theta bomb safe"

        # Check 4: Combination of signals
        if theta_accel and (time_exceeded or iv_crush):
            return (
                True,
                ThetaExitSignal.THETA_ACCELERATION,
                0.98,
                f"Multiple theta signals: accel + {'time' if time_exceeded else 'IV crush'}",
            )

        return False, None, 0.0, f"Theta OK: {theta_msg}, {time_msg}, {iv_msg}"


class TimeBasedForceExitEngine:
    """
    Forced exits based on market timing

    Rules:
    - Force exit before lunch (liquidity drops)
    - Force exit near close (wide spread, low volume)
    - No holding beyond limits
    """

    def __init__(self, config: Optional[Phase7Config] = None):
        self.config = config or Phase7Config()

    def should_force_exit(
        self,
        current_time: datetime,
        entry_time: datetime,
    ) -> Tuple[bool, str]:
        """
        Check time-based forced exit rules
        """

        # Get current time components
        current_hour = current_time.hour
        current_minute = current_time.minute

        # Rule 1: Lunch session approaching (11:30 IST)
        lunch_start = datetime.strptime(self.config.lunch_session_start, "%H:%M").time()
        current_t = current_time.time()

        time_to_lunch = self._time_until(current_t, lunch_start)

        if 0 < time_to_lunch < 300:  # Less than 5 mins to lunch
            return True, f"Lunch approaching in {time_to_lunch}s - force exit"

        # Rule 2: Market close approaching (15:15 IST = market close 15:30)
        if current_hour >= 15 and current_minute >= 15:
            return True, "Market close approaching - force exit"

        # Rule 3: Very early morning (before 9:25)
        if current_hour < 9 or (current_hour == 9 and current_minute < 25):
            return False, "Pre-market"

        # Rule 4: Extreme holding time (>20 mins for scalp)
        elapsed = (current_time - entry_time).total_seconds()
        if elapsed > 1200:  # 20 mins
            return True, f"Extreme holding time {int(elapsed/60)}m - forced exit"

        return False, "Normal trading hours"

    def _time_until(self, current_time: time, target_time: time) -> int:
        """Minutes until target time"""
        curr_mins = current_time.hour * 60 + current_time.minute
        target_mins = target_time.hour * 60 + target_time.minute

        if target_mins > curr_mins:
            return (target_mins - curr_mins) * 60
        else:
            return ((24 * 60) - curr_mins + target_mins) * 60
