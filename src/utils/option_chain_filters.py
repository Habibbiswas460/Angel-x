"""
Phase 2: Noise Reduction Filters & Data Validators

Garbage in → Garbage out prevention.
"""

import logging
from typing import Optional, List, Tuple
from datetime import datetime, timedelta
from src.utils.option_chain_data_models import StrikeData, OptionChainSnapshot, OptionType

logger = logging.getLogger(__name__)


class NoiseFilter:
    """Filters out suspicious/noisy data"""

    def __init__(self, config=None):
        self.config = config or {}

        # Filter thresholds
        self.min_volume = self.config.get("min_volume", 0)  # Drop if vol==0
        self.max_ltp_jump_percent = self.config.get("max_ltp_jump_percent", 10.0)
        self.max_oi_jump_percent = self.config.get("max_oi_jump_percent", 20.0)
        self.stale_data_threshold_sec = self.config.get("stale_data_threshold_sec", 60)

        self.logger = logging.getLogger(f"{__name__}.NoiseFilter")

    def filter_zero_volume(self, strike: StrikeData) -> bool:
        """Filter out zero volume strikes"""
        if strike.volume == 0 and self.min_volume > 0:
            self.logger.debug(f"Filtered zero volume: {strike.strike} {strike.option_type}")
            return False
        return True

    def detect_frozen_ltp(self, strike: StrikeData, prev_strike: Optional[StrikeData]) -> bool:
        """Detect frozen/stale LTP data"""
        if not prev_strike:
            return True  # Can't detect on first snapshot

        # If LTP hasn't moved in 5+ seconds and no volume, suspect frozen data
        if (
            strike.ltp == prev_strike.ltp
            and strike.volume == prev_strike.volume
            and strike.timestamp
            and prev_strike.timestamp
        ):

            age = (strike.timestamp - prev_strike.timestamp).total_seconds()
            if age > self.stale_data_threshold_sec:
                self.logger.debug(f"Detected frozen LTP: {strike.strike} {strike.option_type}")
                return False

        return True

    def detect_ltp_spike(self, strike: StrikeData, prev_strike: Optional[StrikeData]) -> bool:
        """Detect suspicious LTP jumps"""
        if not prev_strike or prev_strike.ltp <= 0:
            return True  # Can't validate on first snapshot

        jump_percent = abs((strike.ltp - prev_strike.ltp) / prev_strike.ltp) * 100

        if jump_percent > self.max_ltp_jump_percent:
            self.logger.warning(
                f"Detected LTP spike: {strike.strike} {strike.option_type} " f"jumped {jump_percent:.1f}%"
            )
            return False

        return True

    def detect_oi_spike(self, strike: StrikeData, prev_strike: Optional[StrikeData]) -> bool:
        """Detect suspicious OI jumps"""
        if not prev_strike or prev_strike.oi <= 0:
            return True

        if strike.oi_prev and strike.oi_prev > 0:
            jump_percent = abs((strike.oi - strike.oi_prev) / strike.oi_prev) * 100

            if jump_percent > self.max_oi_jump_percent:
                self.logger.warning(
                    f"Detected OI spike: {strike.strike} {strike.option_type} " f"jumped {jump_percent:.1f}%"
                )
                return False

        return True

    def validate_strike(
        self, strike: StrikeData, prev_strike: Optional[StrikeData] = None
    ) -> Tuple[bool, Optional[str]]:
        """Comprehensive validation of single strike"""

        checks = [
            (self.filter_zero_volume(strike), "zero_volume"),
            (self.detect_frozen_ltp(strike, prev_strike), "frozen_ltp"),
            (self.detect_ltp_spike(strike, prev_strike), "ltp_spike"),
            (self.detect_oi_spike(strike, prev_strike), "oi_spike"),
        ]

        for is_valid, check_name in checks:
            if not is_valid:
                return False, check_name

        return True, None

    def filter_snapshot(
        self, snapshot: OptionChainSnapshot, prev_snapshot: Optional[OptionChainSnapshot] = None
    ) -> Tuple[OptionChainSnapshot, List[str]]:
        """Filter entire snapshot, return filtered snapshot and drop reasons"""

        dropped_strikes = []
        filtered_pairs = {}

        for strike_price, pair in snapshot.strikes.items():
            ce_valid = True
            pe_valid = True
            ce_reason = None
            pe_reason = None

            # Validate CE
            if pair.ce:
                prev_ce = None
                if prev_snapshot and strike_price in prev_snapshot.strikes:
                    prev_ce = prev_snapshot.strikes[strike_price].ce

                ce_valid, ce_reason = self.validate_strike(pair.ce, prev_ce)

            # Validate PE
            if pair.pe:
                prev_pe = None
                if prev_snapshot and strike_price in prev_snapshot.strikes:
                    prev_pe = prev_snapshot.strikes[strike_price].pe

                pe_valid, pe_reason = self.validate_strike(pair.pe, prev_pe)

            # Keep pair if at least one side is valid
            if ce_valid or pe_valid:
                pair.ce = pair.ce if ce_valid else None
                pair.pe = pair.pe if pe_valid else None
                filtered_pairs[strike_price] = pair
            else:
                dropped_strikes.append(f"{strike_price}({ce_reason or pe_reason})")

        snapshot.strikes = filtered_pairs

        if dropped_strikes:
            snapshot.is_partial = True
            logger.info(f"Dropped {len(dropped_strikes)} strikes: {dropped_strikes[:5]}")

        return snapshot, dropped_strikes


class DataValidator:
    """Validates data completeness and consistency"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.DataValidator")

    def check_expiry_match(self, snapshot: OptionChainSnapshot, expected_expiry: str) -> bool:
        """Verify all strikes match expected expiry"""
        if snapshot.expiry != expected_expiry:
            self.logger.warning(f"Expiry mismatch: got {snapshot.expiry}, expected {expected_expiry}")
            return False
        return True

    def check_strike_alignment(self, snapshot: OptionChainSnapshot) -> Tuple[bool, str]:
        """Verify strikes form regular intervals"""
        if not snapshot.strikes:
            return False, "no_strikes"

        strikes = sorted(snapshot.strikes.keys())

        # Calculate intervals
        intervals = [strikes[i + 1] - strikes[i] for i in range(len(strikes) - 1)]

        if not intervals:
            return False, "insufficient_strikes"

        # Most common interval should be 100 for NIFTY
        from collections import Counter

        common_interval = Counter(intervals).most_common(1)[0][0]

        # Check if most strikes follow this interval
        aligned_count = sum(1 for i in intervals if abs(i - common_interval) < 1)
        alignment_ratio = aligned_count / len(intervals)

        if alignment_ratio < 0.8:
            self.logger.warning(f"Poor strike alignment: {alignment_ratio:.1%}")
            return False, "misaligned_strikes"

        return True, "aligned"

    def check_completeness(self, snapshot: OptionChainSnapshot, min_pairs: int = 8) -> Tuple[bool, float]:
        """Check if we have minimum required pairs"""
        complete_pairs = snapshot.complete_pairs
        completeness = complete_pairs / max(snapshot.strike_count, 1)

        if complete_pairs < min_pairs:
            self.logger.warning(f"Insufficient complete pairs: {complete_pairs} < {min_pairs}")
            return False, completeness

        return True, completeness

    def compute_quality_score(self, snapshot: OptionChainSnapshot) -> float:
        """
        Compute data quality score (0-100)
        Factors:
        - Completeness (40%)
        - Liquidity (40%)
        - Freshness (20%)
        """

        # Completeness score
        if snapshot.strike_count > 0:
            completeness_score = (snapshot.complete_pairs / snapshot.strike_count) * 100
        else:
            completeness_score = 0

        # Liquidity score
        if snapshot.complete_pairs > 0:
            liquidity_score = (snapshot.liquid_pairs / snapshot.complete_pairs) * 100
        else:
            liquidity_score = 0

        # Freshness score (0-100, 100 if < 5 seconds old)
        age_sec = (datetime.utcnow() - snapshot.timestamp).total_seconds()
        freshness_score = max(0, 100 - (age_sec * 10))  # Loses 10 points per second

        # Weighted score
        quality = (completeness_score * 0.4) + (liquidity_score * 0.4) + (freshness_score * 0.2)

        return min(100, max(0, quality))  # Clamp 0-100


class StaleDataDetector:
    """Detects and tracks stale/outdated data"""

    def __init__(self, stale_threshold_sec: float = 60):
        self.stale_threshold_sec = stale_threshold_sec
        self.logger = logging.getLogger(f"{__name__}.StaleDataDetector")

    def is_stale(self, snapshot: OptionChainSnapshot) -> bool:
        """Check if snapshot is stale"""
        age_sec = (datetime.utcnow() - snapshot.timestamp).total_seconds()
        return age_sec > self.stale_threshold_sec

    def find_stale_strikes(self, snapshot: OptionChainSnapshot) -> List[float]:
        """Find strikes with old LTP data"""
        stale = []
        now = datetime.utcnow()

        for strike_price, pair in snapshot.strikes.items():
            for strike in [pair.ce, pair.pe]:
                if strike and strike.timestamp:
                    age = (now - strike.timestamp).total_seconds()
                    if age > self.stale_threshold_sec:
                        stale.append(strike_price)
                        break

        return stale

    def partial_chain_detector(self, snapshot: OptionChainSnapshot) -> bool:
        """Detect if chain is partial/incomplete"""
        # Partial if:
        # 1. Missing expected strikes
        # 2. Only one side (CE or PE) for multiple strikes
        # 3. Sudden gaps in strikes

        if snapshot.complete_pairs < (snapshot.strike_count * 0.7):
            self.logger.warning("Partial chain detected: many incomplete pairs")
            return True

        return False


class BrokerHiccupDetector:
    """Detects broker connectivity issues"""

    def __init__(self, error_threshold: int = 3):
        self.error_threshold = error_threshold
        self.consecutive_errors = 0
        self.logger = logging.getLogger(f"{__name__}.BrokerHiccupDetector")

    def record_error(self) -> bool:
        """Record fetch error, return True if threshold exceeded"""
        self.consecutive_errors += 1

        if self.consecutive_errors >= self.error_threshold:
            self.logger.warning(f"Broker hiccup detected: {self.consecutive_errors} consecutive errors")
            return True

        return False

    def record_success(self):
        """Clear error counter on success"""
        self.consecutive_errors = 0

    def should_soft_pause(self) -> bool:
        """Should we pause trading"""
        return self.consecutive_errors >= self.error_threshold
