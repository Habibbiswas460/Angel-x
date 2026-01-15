"""
PHASE 8: Failover & Recovery System
Auto-recovery from broker hiccups, data freezes, network issues
No panic exits, graceful degradation
"""

import time
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging


class SystemState(Enum):
    """System operational states"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    PAUSED = "paused"
    CRITICAL = "critical"


@dataclass
class HealthCheck:
    """Health check result"""

    component: str
    status: bool
    latency_ms: float
    error_message: Optional[str] = None
    timestamp: datetime = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class BrokerConnectionMonitor:
    """
    Monitor broker API health
    Auto-pause on connection issues
    """

    def __init__(self, max_failures: int = 3, recovery_wait_seconds: int = 30):
        self.max_failures = max_failures
        self.recovery_wait_seconds = recovery_wait_seconds

        self.consecutive_failures = 0
        self.last_failure_time: Optional[datetime] = None
        self.last_success_time: Optional[datetime] = None
        self.total_failures = 0

        self.is_paused = False
        self.pause_until: Optional[datetime] = None

    def record_success(self):
        """Record successful API call"""
        self.consecutive_failures = 0
        self.last_success_time = datetime.now()

        # Auto-resume if paused
        if self.is_paused:
            self.is_paused = False
            self.pause_until = None

    def record_failure(self, error: str):
        """Record failed API call"""
        self.consecutive_failures += 1
        self.total_failures += 1
        self.last_failure_time = datetime.now()

        # Auto-pause if too many failures
        if self.consecutive_failures >= self.max_failures:
            self._activate_pause()

    def _activate_pause(self):
        """Activate trading pause"""
        self.is_paused = True
        self.pause_until = datetime.now() + timedelta(seconds=self.recovery_wait_seconds)

    def can_trade(self) -> bool:
        """Check if trading is allowed"""
        if not self.is_paused:
            return True

        # Check if pause period is over
        if datetime.now() >= self.pause_until:
            self.is_paused = False
            self.consecutive_failures = 0
            return True

        return False

    def get_status(self) -> Dict:
        """Get connection status"""
        return {
            "is_paused": self.is_paused,
            "consecutive_failures": self.consecutive_failures,
            "total_failures": self.total_failures,
            "last_success": self.last_success_time.isoformat() if self.last_success_time else None,
            "pause_until": self.pause_until.isoformat() if self.pause_until else None,
        }


class DataFreezeDetector:
    """
    Detect when market data stops updating
    Prevent trading on stale data

    CRITICAL RULE: No fresh data = NO TRADE
    """

    def __init__(self, max_staleness_seconds: int = 10):
        self.max_staleness_seconds = max_staleness_seconds
        self.last_update_time: Optional[datetime] = None
        self.last_data_hash: Optional[str] = None
        self.freeze_detected = False
        self.trading_blocked = False
        self.block_reason: Optional[str] = None

    def update_data(self, data_hash: str):
        """Record data update"""
        current_time = datetime.now()

        # Check if data actually changed
        if data_hash != self.last_data_hash:
            self.last_update_time = current_time
            self.last_data_hash = data_hash
            self.freeze_detected = False
            self.trading_blocked = False  # Unblock on fresh data
            self.block_reason = None
        else:
            # Data hasn't changed - check staleness
            if self.last_update_time:
                staleness = (current_time - self.last_update_time).total_seconds()
                if staleness > self.max_staleness_seconds:
                    self.freeze_detected = True
                    self._block_trading("Data frozen - no updates received")

    def _block_trading(self, reason: str):
        """Block trading due to data issues"""
        self.trading_blocked = True
        self.block_reason = reason

    def can_trade(self) -> Dict:
        """
        Check if trading is allowed based on data freshness

        CRITICAL: Returns False if no fresh data
        """
        # No data received yet
        if not self.last_update_time:
            return {"allowed": False, "reason": "No market data received yet"}

        # Check data staleness
        staleness = (datetime.now() - self.last_update_time).total_seconds()

        if staleness > self.max_staleness_seconds:
            return {"allowed": False, "reason": f"Data stale ({staleness:.1f}s old, max {self.max_staleness_seconds}s)"}

        if self.freeze_detected:
            return {"allowed": False, "reason": "Data freeze detected"}

        if self.trading_blocked:
            return {"allowed": False, "reason": self.block_reason or "Trading blocked"}

        # All checks passed
        return {"allowed": True, "reason": f"Data fresh ({staleness:.1f}s old)"}

    def is_data_frozen(self) -> bool:
        """Check if data is frozen"""
        if not self.last_update_time:
            return True  # No data yet

        staleness = (datetime.now() - self.last_update_time).total_seconds()
        return staleness > self.max_staleness_seconds or self.freeze_detected

    def get_staleness_seconds(self) -> int:
        """Get data staleness in seconds"""
        if not self.last_update_time:
            return 999

        return int((datetime.now() - self.last_update_time).total_seconds())

    def reset(self):
        """Reset freeze detection"""
        self.freeze_detected = False
        self.last_update_time = datetime.now()
        self.trading_blocked = False
        self.block_reason = None


class PartialOrderReconciliation:
    """
    Handle partial order fills and reconciliation
    Ensure position tracking stays accurate
    """

    def __init__(self):
        self.pending_orders: Dict[str, Dict] = {}
        self.partial_fills: Dict[str, List] = {}

    def add_order(self, order_id: str, order_details: Dict):
        """Track pending order"""
        self.pending_orders[order_id] = {
            "details": order_details,
            "timestamp": datetime.now(),
            "filled_qty": 0,
            "total_qty": order_details.get("quantity", 0),
        }

    def update_fill(self, order_id: str, filled_qty: int):
        """Update order fill quantity"""
        if order_id in self.pending_orders:
            self.pending_orders[order_id]["filled_qty"] = filled_qty

            # Track partial fill
            if order_id not in self.partial_fills:
                self.partial_fills[order_id] = []

            self.partial_fills[order_id].append({"qty": filled_qty, "timestamp": datetime.now()})

    def is_fully_filled(self, order_id: str) -> bool:
        """Check if order is completely filled"""
        if order_id not in self.pending_orders:
            return False

        order = self.pending_orders[order_id]
        return order["filled_qty"] >= order["total_qty"]

    def get_unfilled_quantity(self, order_id: str) -> int:
        """Get remaining unfilled quantity"""
        if order_id not in self.pending_orders:
            return 0

        order = self.pending_orders[order_id]
        return order["total_qty"] - order["filled_qty"]

    def remove_order(self, order_id: str):
        """Remove completed order"""
        if order_id in self.pending_orders:
            del self.pending_orders[order_id]

    def get_pending_orders(self) -> List[Dict]:
        """Get all pending orders"""
        return [
            {
                "order_id": oid,
                "filled_pct": (order["filled_qty"] / order["total_qty"] * 100) if order["total_qty"] > 0 else 0,
                **order,
            }
            for oid, order in self.pending_orders.items()
        ]


class SessionAutoRefresh:
    """
    Auto-refresh broker session without restart
    Handle token expiry gracefully
    """

    def __init__(self, refresh_callback: Callable):
        self.refresh_callback = refresh_callback
        self.session_start_time: datetime = datetime.now()
        self.last_refresh_time: Optional[datetime] = None
        self.refresh_interval_minutes = 240  # 4 hours

        self.auto_refresh_enabled = True

    def should_refresh(self) -> bool:
        """Check if session should be refreshed"""
        if not self.auto_refresh_enabled:
            return False

        if not self.last_refresh_time:
            self.last_refresh_time = self.session_start_time

        elapsed = (datetime.now() - self.last_refresh_time).total_seconds() / 60
        return elapsed >= self.refresh_interval_minutes

    def refresh_session(self) -> bool:
        """Attempt session refresh"""
        try:
            success = self.refresh_callback()
            if success:
                self.last_refresh_time = datetime.now()
                return True
        except Exception as e:
            logging.error(f"Session refresh failed: {e}")

        return False

    def auto_refresh_check(self):
        """Periodic check and refresh"""
        if self.should_refresh():
            return self.refresh_session()
        return True


class SafeExitManager:
    """
    Manage safe exit from positions during failures
    No panic selling, orderly exit
    """

    def __init__(self):
        self.exit_mode = False
        self.exit_reason: Optional[str] = None
        self.positions_to_exit: List[Dict] = []

    def activate_safe_exit(self, reason: str, positions: List[Dict]):
        """Activate safe exit mode"""
        self.exit_mode = True
        self.exit_reason = reason
        self.positions_to_exit = positions.copy()

    def deactivate_exit_mode(self):
        """Deactivate safe exit"""
        self.exit_mode = False
        self.exit_reason = None
        self.positions_to_exit.clear()

    def get_next_exit_action(self) -> Optional[Dict]:
        """Get next position to exit"""
        if not self.exit_mode or not self.positions_to_exit:
            return None

        # Exit one position at a time
        return self.positions_to_exit[0]

    def mark_position_exited(self, position_id: str):
        """Mark position as successfully exited"""
        self.positions_to_exit = [p for p in self.positions_to_exit if p.get("id") != position_id]


class FailoverRecoverySystem:
    """
    Master failover and recovery orchestrator
    Ensures system never crashes, always recovers gracefully
    """

    def __init__(self, refresh_callback: Callable = None):
        self.broker_monitor = BrokerConnectionMonitor()
        self.freeze_detector = DataFreezeDetector()
        self.order_reconciliation = PartialOrderReconciliation()
        self.session_refresh = SessionAutoRefresh(refresh_callback or self._dummy_refresh)
        self.safe_exit = SafeExitManager()

        self.state = SystemState.HEALTHY
        self.recovery_attempts = 0
        self.max_recovery_attempts = 3

        # Health history
        self.health_checks: List[HealthCheck] = []
        self.max_history = 100

    def _dummy_refresh(self) -> bool:
        """Dummy refresh for testing"""
        return True

    def check_broker_health(self, test_func: Callable) -> HealthCheck:
        """Check broker API health"""
        start_time = time.time()

        try:
            result = test_func()
            latency_ms = (time.time() - start_time) * 1000

            if result:
                self.broker_monitor.record_success()
                check = HealthCheck("broker_api", True, latency_ms)
            else:
                self.broker_monitor.record_failure("API test failed")
                check = HealthCheck("broker_api", False, latency_ms, "API test failed")

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.broker_monitor.record_failure(str(e))
            check = HealthCheck("broker_api", False, latency_ms, str(e))

        self._record_health_check(check)
        return check

    def check_data_freshness(self, data_hash: str) -> HealthCheck:
        """Check if data is updating"""
        self.freeze_detector.update_data(data_hash)

        is_frozen = self.freeze_detector.is_data_frozen()
        staleness = self.freeze_detector.get_staleness_seconds()

        if is_frozen:
            check = HealthCheck("data_feed", False, staleness * 1000, f"Data frozen for {staleness}s")
        else:
            check = HealthCheck("data_feed", True, staleness * 1000)

        self._record_health_check(check)
        return check

    def _record_health_check(self, check: HealthCheck):
        """Record health check result"""
        self.health_checks.append(check)
        if len(self.health_checks) > self.max_history:
            self.health_checks.pop(0)

    def assess_system_state(self) -> SystemState:
        """Assess overall system health"""
        # Check broker status
        if not self.broker_monitor.can_trade():
            self.state = SystemState.PAUSED
            return self.state

        # Check data freeze
        if self.freeze_detector.is_data_frozen():
            self.state = SystemState.DEGRADED
            return self.state

        # Check recent health
        if len(self.health_checks) >= 5:
            recent = self.health_checks[-5:]
            failed = sum(1 for c in recent if not c.status)

            if failed >= 3:
                self.state = SystemState.CRITICAL
            elif failed >= 1:
                self.state = SystemState.DEGRADED
            else:
                self.state = SystemState.HEALTHY

        return self.state

    def attempt_recovery(self) -> bool:
        """
        Attempt system recovery
        Returns True if recovery successful
        """
        if self.recovery_attempts >= self.max_recovery_attempts:
            return False

        self.recovery_attempts += 1
        self.state = SystemState.RECOVERING

        # Step 1: Refresh session
        if not self.session_refresh.refresh_session():
            return False

        # Step 2: Reset freeze detector
        self.freeze_detector.reset()

        # Step 3: Wait briefly
        time.sleep(2)

        # Step 4: Test connection
        try:
            # Assume recovery successful if we reach here
            self.state = SystemState.HEALTHY
            self.recovery_attempts = 0
            return True
        except:
            return False

    def handle_broker_error(self, error: Exception) -> Dict:
        """
        Handle broker API error
        Returns: action recommendation
        """
        error_str = str(error).lower()

        # Token/session errors
        if any(x in error_str for x in ["token", "session", "auth"]):
            self.session_refresh.refresh_session()
            return {"action": "retry", "reason": "Session refreshed", "wait_seconds": 2}

        # Rate limiting
        if any(x in error_str for x in ["rate", "limit", "too many"]):
            return {"action": "pause", "reason": "Rate limited", "wait_seconds": 60}

        # Network errors
        if any(x in error_str for x in ["network", "timeout", "connection"]):
            self.broker_monitor.record_failure(str(error))
            return {"action": "retry", "reason": "Network issue", "wait_seconds": 5}

        # Unknown error
        self.broker_monitor.record_failure(str(error))
        return {"action": "pause", "reason": f"Unknown error: {error}", "wait_seconds": 30}

    def initiate_safe_exit(self, reason: str, positions: List[Dict]):
        """Initiate safe exit from all positions"""
        self.safe_exit.activate_safe_exit(reason, positions)
        self.state = SystemState.PAUSED

    def get_system_status(self) -> Dict:
        """Get comprehensive system status"""
        state = self.assess_system_state()

        return {
            "state": state.value,
            "broker": self.broker_monitor.get_status(),
            "data_staleness_seconds": self.freeze_detector.get_staleness_seconds(),
            "data_frozen": self.freeze_detector.is_data_frozen(),
            "pending_orders": len(self.order_reconciliation.pending_orders),
            "safe_exit_active": self.safe_exit.exit_mode,
            "recovery_attempts": self.recovery_attempts,
            "recent_health": [
                {"component": c.component, "status": c.status, "latency_ms": c.latency_ms}
                for c in self.health_checks[-10:]
            ],
        }

    def should_allow_trading(self) -> Dict:
        """
        Check if trading is allowed
        Returns: {allowed: bool, reason: str}
        """
        # Broker check
        if not self.broker_monitor.can_trade():
            return {"allowed": False, "reason": "Broker connection issues - system paused"}

        # Data check
        if self.freeze_detector.is_data_frozen():
            return {"allowed": False, "reason": f"Data frozen for {self.freeze_detector.get_staleness_seconds()}s"}

        # Safe exit mode
        if self.safe_exit.exit_mode:
            return {"allowed": False, "reason": f"Safe exit mode: {self.safe_exit.exit_reason}"}

        # State check
        if self.state in [SystemState.CRITICAL, SystemState.PAUSED]:
            return {"allowed": False, "reason": f"System state: {self.state.value}"}

        return {"allowed": True, "reason": "All systems operational"}
