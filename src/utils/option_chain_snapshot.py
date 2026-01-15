"""
Phase 2: Snapshot Engine & State Management

Maintains current and previous snapshots for delta calculations.
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from collections import deque

from src.utils.option_chain_data_models import OptionChainSnapshot, OptionChainDelta, StrikeData, OptionType

logger = logging.getLogger(__name__)


class SnapshotEngine:
    """
    Manages snapshots and calculates deltas.

    Maintains:
    - Current snapshot (fresh data)
    - Previous snapshot (for delta calc)
    - Historical snapshots (for metrics)
    """

    def __init__(self, max_history: int = 100):
        self.current: Optional[OptionChainSnapshot] = None
        self.previous: Optional[OptionChainSnapshot] = None

        # Historical snapshots (for metrics/debugging)
        self.history = deque(maxlen=max_history)

        self.logger = logging.getLogger(f"{__name__}.SnapshotEngine")

    def update_snapshot(self, new_snapshot: OptionChainSnapshot) -> OptionChainDelta:
        """
        Update with new snapshot, calculate delta.

        Returns:
            Delta object with changes from previous snapshot
        """

        # Shift snapshots
        self.previous = self.current
        self.current = new_snapshot
        self.history.append(new_snapshot)

        # Calculate delta
        delta = self._calculate_delta(new_snapshot, self.previous)

        if delta.has_changes:
            self.logger.debug(
                f"Snapshot delta: {len(delta.oi_changes)} OI changes, " f"{len(delta.volume_changes)} volume changes"
            )

        return delta

    def _calculate_delta(
        self, current: OptionChainSnapshot, previous: Optional[OptionChainSnapshot]
    ) -> OptionChainDelta:
        """Calculate changes between snapshots"""

        delta = OptionChainDelta(timestamp=datetime.utcnow())

        if not previous:
            # First snapshot, no delta
            return delta

        # Compare strikes
        current_strikes = set(current.strikes.keys())
        previous_strikes = set(previous.strikes.keys())

        # New strikes
        delta.new_strikes_added = list(current_strikes - previous_strikes)

        # Removed strikes
        delta.strikes_removed = list(previous_strikes - current_strikes)

        # Changed strikes
        for strike in current_strikes & previous_strikes:
            current_pair = current.strikes[strike]
            previous_pair = previous.strikes[strike]

            # CE changes
            if current_pair.ce and previous_pair.ce:
                self._check_strike_changes(current_pair.ce, previous_pair.ce, f"{strike}-CE", delta)

            # PE changes
            if current_pair.pe and previous_pair.pe:
                self._check_strike_changes(current_pair.pe, previous_pair.pe, f"{strike}-PE", delta)

        # Detect stale strikes
        delta.stale_strikes = self._find_stale_strikes(current, previous)

        return delta

    def _check_strike_changes(
        self, current: StrikeData, previous: StrikeData, strike_key: str, delta: OptionChainDelta
    ):
        """Check single strike for changes"""

        # OI change
        if current.oi != previous.oi:
            change = current.oi - previous.oi
            delta.oi_changes[strike_key] = change

        # Volume change
        if current.volume != previous.volume:
            change = current.volume - previous.volume
            delta.volume_changes[strike_key] = change

        # LTP change
        if current.ltp != previous.ltp:
            change = current.ltp - previous.ltp
            delta.ltp_changes[strike_key] = change

    def _find_stale_strikes(self, current: OptionChainSnapshot, previous: Optional[OptionChainSnapshot]) -> list:
        """Find strikes that haven't changed"""

        stale = []

        if not previous:
            return stale

        for strike in current.strikes.keys():
            if strike not in previous.strikes:
                continue

            curr_pair = current.strikes[strike]
            prev_pair = previous.strikes[strike]

            # Check if any side is truly stale (no OI/Vol change)
            ce_stale = (
                curr_pair.ce
                and prev_pair.ce
                and curr_pair.ce.oi == prev_pair.ce.oi
                and curr_pair.ce.volume == prev_pair.ce.volume
                and curr_pair.ce.ltp == prev_pair.ce.ltp
            )

            pe_stale = (
                curr_pair.pe
                and prev_pair.pe
                and curr_pair.pe.oi == prev_pair.pe.oi
                and curr_pair.pe.volume == prev_pair.pe.volume
                and curr_pair.pe.ltp == prev_pair.pe.ltp
            )

            if ce_stale or pe_stale:
                stale.append(strike)

        return stale

    def get_atm_ce(self) -> Optional[StrikeData]:
        """Get current ATM call"""
        if self.current:
            return self.current.get_atm_ce()
        return None

    def get_atm_pe(self) -> Optional[StrikeData]:
        """Get current ATM put"""
        if self.current:
            return self.current.get_atm_pe()
        return None

    def get_strike(self, offset: int) -> Optional[object]:
        """Get strike pair at offset from ATM"""
        if self.current:
            return self.current.get_strike(offset)
        return None

    def get_chain_summary(self) -> Dict:
        """Get current chain summary"""
        if self.current:
            return self.current.get_chain_summary()
        return {}

    def get_history_summary(self) -> Dict:
        """Summary of historical data"""
        if not self.history:
            return {}

        return {
            "snapshots_captured": len(self.history),
            "first_snapshot": self.history[0].timestamp.isoformat() if self.history else None,
            "latest_snapshot": self.history[-1].timestamp.isoformat() if self.history else None,
            "avg_fetch_latency_ms": (
                sum(s.fetch_latency_ms for s in self.history) / len(self.history) if self.history else 0
            ),
        }


class SnapshotCache:
    """
    In-memory cache of snapshots.
    Thread-safe storage of option chain data.
    """

    def __init__(self):
        self.cache: Dict[str, Dict[str, OptionChainSnapshot]] = {}
        # Structure: cache[underlying][expiry] = OptionChainSnapshot

        self.logger = logging.getLogger(f"{__name__}.SnapshotCache")

    def store(self, underlying: str, expiry: str, snapshot: OptionChainSnapshot):
        """Store snapshot in cache"""
        if underlying not in self.cache:
            self.cache[underlying] = {}

        self.cache[underlying][expiry] = snapshot
        self.logger.debug(f"Cached snapshot: {underlying} {expiry}")

    def retrieve(self, underlying: str, expiry: str) -> Optional[OptionChainSnapshot]:
        """Retrieve snapshot from cache"""
        if underlying in self.cache and expiry in self.cache[underlying]:
            return self.cache[underlying][expiry]
        return None

    def get_latest(self, underlying: str) -> Optional[OptionChainSnapshot]:
        """Get latest snapshot for underlying (any expiry)"""
        if underlying not in self.cache:
            return None

        # Return most recent by timestamp
        snapshots = self.cache[underlying].values()
        if not snapshots:
            return None

        return max(snapshots, key=lambda s: s.timestamp)

    def list_cached(self) -> Dict[str, list]:
        """List all cached (underlying, expiry) pairs"""
        result = {}
        for underlying, expiries in self.cache.items():
            result[underlying] = list(expiries.keys())
        return result

    def clear(self, underlying: str = None, expiry: str = None):
        """Clear cache (selective or full)"""
        if underlying is None:
            self.cache.clear()
            self.logger.info("Cleared entire cache")
        elif expiry is None:
            if underlying in self.cache:
                del self.cache[underlying]
                self.logger.info(f"Cleared cache for {underlying}")
        else:
            if underlying in self.cache and expiry in self.cache[underlying]:
                del self.cache[underlying][expiry]
                self.logger.info(f"Cleared cache for {underlying} {expiry}")

    def get_cache_size(self) -> int:
        """Total snapshots in cache"""
        return sum(len(expiries) for expiries in self.cache.values())


class SnapshotValidator:
    """Validates snapshot consistency"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.SnapshotValidator")

    def validate_snapshot_consistency(self, snapshot: OptionChainSnapshot) -> bool:
        """
        Validate internal consistency of snapshot.

        Checks:
        - All CE and PE have proper alignment
        - Timestamps make sense
        - No duplicate strikes
        """

        # Check for duplicates
        if len(snapshot.strikes) == 0:
            self.logger.warning("Empty snapshot")
            return False

        # Validate ATM
        if snapshot.atm_strike and snapshot.atm_strike not in snapshot.strikes:
            self.logger.warning(f"ATM {snapshot.atm_strike} not in strikes")
            return False

        # Check strikes
        for strike, pair in snapshot.strikes.items():
            if pair.ce and pair.ce.strike != strike:
                self.logger.warning(f"CE strike mismatch: {pair.ce.strike} != {strike}")
                return False

            if pair.pe and pair.pe.strike != strike:
                self.logger.warning(f"PE strike mismatch: {pair.pe.strike} != {strike}")
                return False

        return True
