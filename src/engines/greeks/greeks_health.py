"""
PHASE 3 — Greeks Health & Sanity Checks
Detects: Frozen Greeks, abnormal IV spikes, expiry glitches, stale data

Used for: Data quality gating before strategy signals
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple

from .greeks_models import GreeksSnapshot, GreeksHealthReport, GreeksHealthStatus, OptionType, VolatilityState

logger = logging.getLogger(__name__)


class GreeksHealthMonitor:
    """
    Monitor Greeks data quality and health status
    Detects abnormalities and flags unsafe data

    Used for: Blocking signals when data is unreliable
    """

    def __init__(
        self,
        stale_threshold_sec: float = 60.0,  # Data older than 60s is stale
        frozen_greek_threshold: float = 0.0001,  # No movement = frozen
        iv_spike_threshold: float = 0.20,  # IV change >20% = spike
        min_greeks_for_health: int = 8,  # Need ≥8 strikes for healthy
    ):
        """Initialize health monitor"""
        self.stale_threshold = stale_threshold_sec
        self.frozen_greek_threshold = frozen_greek_threshold
        self.iv_spike_threshold = iv_spike_threshold
        self.min_greeks_for_health = min_greeks_for_health

        # Tracking
        self.last_iv_level: Dict[str, float] = {}  # Track IV per underlying
        self.health_history: List[GreeksHealthReport] = []
        self.max_history = 100

        logger.info(
            f"Greeks Health Monitor initialized "
            f"(stale_threshold={stale_threshold_sec}s, "
            f"frozen_threshold={frozen_greek_threshold})"
        )

    def check_health(self, current_greeks: Dict[float, GreeksSnapshot], underlying: str) -> GreeksHealthReport:
        """
        Check overall Greeks health status

        Returns: GreeksHealthReport with status and issues
        """
        report = GreeksHealthReport(timestamp=datetime.now())

        if not current_greeks:
            report.status = GreeksHealthStatus.UNHEALTHY
            report.can_trade = False
            report.recovery_suggestion = "No Greeks data available"
            return report

        now = datetime.now()

        # -------- Check 1: Stale Data --------
        stale_count = 0
        for strike, greek in current_greeks.items():
            age = (now - greek.timestamp).total_seconds()
            if age > self.stale_threshold:
                stale_count += 1

        report.stale_count = stale_count
        report.snapshot_count = len(current_greeks) - stale_count

        # -------- Check 2: Frozen Greeks --------
        frozen_greeks = 0
        for strike, greek in current_greeks.items():
            has_movement = greek.has_greek_movement()
            if not has_movement and greek.delta_previous is not None:
                frozen_greeks += 1

        report.frozen_greeks = frozen_greeks

        # -------- Check 3: IV Availability & Spikes --------
        iv_values = []
        iv_errors = 0
        for strike, greek in current_greeks.items():
            if greek.implied_volatility > 0:
                iv_values.append(greek.implied_volatility)
            else:
                iv_errors += 1

        report.iv_available = len(iv_values) > len(current_greeks) * 0.8

        # Check for IV spike
        if iv_values:
            avg_iv = sum(iv_values) / len(iv_values)
            if underlying in self.last_iv_level:
                last_iv = self.last_iv_level[underlying]
                iv_change = abs(avg_iv - last_iv) / max(last_iv, 0.01)
                if iv_change > self.iv_spike_threshold:
                    report.iv_spike = iv_change
                    logger.warning(
                        f"IV spike detected for {underlying}: "
                        f"{last_iv*100:.1f}% → {avg_iv*100:.1f}% "
                        f"({iv_change*100:.1f}% change)"
                    )

            self.last_iv_level[underlying] = avg_iv

        # -------- Check 4: Calculation Errors --------
        for strike, greek in current_greeks.items():
            if greek.iv_source == "error_fallback":
                report.calculation_errors += 1

        # -------- Determine Overall Status --------
        issues = []

        if report.stale_count > len(current_greeks) * 0.5:
            issues.append("STALE_DATA")

        if frozen_greeks > len(current_greeks) * 0.7:
            issues.append("FROZEN_GREEKS")

        if report.iv_spike and report.iv_spike > self.iv_spike_threshold * 2:
            issues.append("EXTREME_IV_SPIKE")

        if report.calculation_errors > len(current_greeks) * 0.3:
            issues.append("CALCULATION_ERRORS")

        if report.snapshot_count < self.min_greeks_for_health:
            issues.append("INSUFFICIENT_DATA")

        # Determine status
        if not issues:
            report.status = GreeksHealthStatus.HEALTHY
            report.can_trade = True
        elif len(issues) == 1 and issues[0] in ["FROZEN_GREEKS", "CALCULATION_ERRORS"]:
            report.status = GreeksHealthStatus.DEGRADED
            report.can_trade = True
        elif "STALE_DATA" in issues:
            report.status = GreeksHealthStatus.STALE
            report.can_trade = False
            report.recovery_suggestion = "Wait for fresh Greeks data"
        elif "EXTREME_IV_SPIKE" in issues:
            report.status = GreeksHealthStatus.UNHEALTHY
            report.can_trade = False
            report.recovery_suggestion = "IV spike detected, wait for stabilization"
        else:
            report.status = GreeksHealthStatus.UNHEALTHY
            report.can_trade = False
            report.recovery_suggestion = "Multiple issues detected"

        # Record health history
        self.health_history.append(report)
        if len(self.health_history) > self.max_history:
            self.health_history.pop(0)

        logger.info(
            f"Greeks health: {report.status.value}, "
            f"snapshots={report.snapshot_count}, "
            f"stale={report.stale_count}, "
            f"frozen={report.frozen_greeks}"
        )

        return report

    def check_greek_sanity(self, greek: GreeksSnapshot) -> Tuple[bool, Optional[str]]:
        """
        Sanity check single Greek snapshot
        Returns: (is_sane, issue_description)
        """
        # Check 1: Basic ranges
        if not (0.0 <= greek.delta <= 1.0):
            return False, f"Delta out of range: {greek.delta}"

        if greek.gamma < 0.0 or greek.gamma > 0.2:
            return False, f"Gamma out of range: {greek.gamma}"

        if greek.theta > 0.01:  # Theta should be <= 0 (or very close to 0)
            return False, f"Theta positive (should be <= 0): {greek.theta}"

        # Check 2: Freshness
        age = (datetime.now() - greek.timestamp).total_seconds()
        if age > self.stale_threshold * 2:
            return False, f"Data too old: {age:.0f}s old"

        # Check 3: IV bounds
        if not (0.0 <= greek.implied_volatility <= 2.0):
            return False, f"IV out of reasonable bounds: {greek.implied_volatility}"

        # Check 4: IV source validity
        if greek.iv_source not in ["broker", "estimated", "calculated", "error_fallback"]:
            return False, f"Invalid IV source: {greek.iv_source}"

        return True, None

    def detect_iv_state(self, current_greeks: Dict[float, GreeksSnapshot]) -> VolatilityState:
        """
        Detect current IV state (surging, crushing, stable)

        Returns: VolatilityState
        """
        if not current_greeks:
            return VolatilityState.STABLE_MID

        ivs = [g.implied_volatility for g in current_greeks.values() if g.implied_volatility > 0]
        if not ivs:
            return VolatilityState.STABLE_MID

        avg_iv = sum(ivs) / len(ivs)

        # Simple heuristic: classify IV level
        if avg_iv < 0.15:
            return VolatilityState.STABLE_LOW
        elif avg_iv < 0.25:
            return VolatilityState.STABLE_MID
        elif avg_iv < 0.40:
            return VolatilityState.STABLE_HIGH
        else:
            return VolatilityState.SURGING

    def get_health_summary(self) -> Dict:
        """Get summary of health history"""
        if not self.health_history:
            return {"status": "NO_DATA"}

        latest = self.health_history[-1]

        # Count status distribution in last 10 checks
        recent_statuses = [h.status for h in self.health_history[-10:]]
        status_counts = {
            "HEALTHY": recent_statuses.count(GreeksHealthStatus.HEALTHY),
            "DEGRADED": recent_statuses.count(GreeksHealthStatus.DEGRADED),
            "UNHEALTHY": recent_statuses.count(GreeksHealthStatus.UNHEALTHY),
            "STALE": recent_statuses.count(GreeksHealthStatus.STALE),
        }

        return {
            "current_status": latest.status.value,
            "can_trade": latest.can_trade,
            "snapshots": latest.snapshot_count,
            "stale_count": latest.stale_count,
            "frozen_count": latest.frozen_greeks,
            "status_distribution_10": status_counts,
            "last_check": latest.timestamp,
        }
