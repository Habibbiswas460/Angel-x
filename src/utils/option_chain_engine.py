"""
Phase 2: Option Chain Data Engine

Main orchestrator for fetching, filtering, normalizing and serving clean option chain data.

Architecture:
  Broker Feed → Filter → Normalize → Snapshot Store → Stream Bus
"""

import logging
import time
import threading
from typing import Optional, Dict, List, Callable
from datetime import datetime, timedelta
from dataclasses import asdict

from src.utils.option_chain_data_models import (
    OptionChainSnapshot, OptionChainDelta, ExpiryInfo, UniverseDefinition,
    DataHealthStatus, DataHealthReport, OptionType, StrikeData
)
from src.utils.option_chain_filters import (
    NoiseFilter, DataValidator, StaleDataDetector, BrokerHiccupDetector
)
from src.utils.option_chain_snapshot import (
    SnapshotEngine, SnapshotCache, SnapshotValidator
)

logger = logging.getLogger(__name__)


class OptionChainDataEngine:
    """
    Low-latency, clean option chain data engine.
    
    Responsibilities:
    1. Fetch raw data from broker
    2. Filter & validate
    3. Normalize & align
    4. Maintain snapshots
    5. Serve clean interface
    6. Monitor health
    """
    
    def __init__(self, adapter, config=None):
        """
        Initialize engine.
        
        Args:
            adapter: AngelOnePhase2 broker adapter
            config: Configuration dict
        """
        self.adapter = adapter
        self.config = config or {}
        
        # Universe definition
        self.universe: Optional[UniverseDefinition] = None
        
        # Components
        self.noise_filter = NoiseFilter(self.config)
        self.validator = DataValidator()
        self.stale_detector = StaleDataDetector(self.config.get('stale_threshold_sec', 60))
        self.hiccup_detector = BrokerHiccupDetector(self.config.get('error_threshold', 3))
        self.snapshot_engine = SnapshotEngine()
        self.snapshot_cache = SnapshotCache()
        self.snapshot_validator = SnapshotValidator()
        
        # Health tracking
        self.health_report = DataHealthReport(
            status=DataHealthStatus.OFFLINE,
            timestamp=datetime.utcnow()
        )
        self.fetch_count = 0
        self.error_count = 0
        self.latencies: List[float] = []
        
        # Threading
        self._stop_event = threading.Event()
        self._fetch_thread: Optional[threading.Thread] = None
        self._subscribers: List[Callable] = []
        
        # Callbacks
        self.on_snapshot = None  # Called on new snapshot
        self.on_delta = None     # Called on delta
        
        self.logger = logging.getLogger(f"{__name__}.OptionChainDataEngine")
    
    # =========================================================================
    # UNIVERSE DEFINITION
    # =========================================================================
    
    def set_universe(self, underlying: str, expiry_date: datetime, atm_reference: float, 
                     strikes_range: int = 5):
        """
        Define trading universe.
        
        Args:
            underlying: "NIFTY"
            expiry_date: datetime of expiry
            atm_reference: Current spot price for ATM calculation
            strikes_range: ATM ± N strikes
        """
        
        expiry_code = self._get_expiry_code(expiry_date)
        expiry_info = ExpiryInfo(
            expiry_code=expiry_code,
            expiry_date=expiry_date,
            is_weekly=True
        )
        
        self.universe = UniverseDefinition(
            underlying=underlying,
            expiry=expiry_info,
            atm_reference=atm_reference,
            strikes_range=strikes_range
        )
        
        self.logger.info(
            f"Universe defined: {underlying} {expiry_code} "
            f"ATM {atm_reference} ±{strikes_range}"
        )
    
    def _get_expiry_code(self, expiry_date: datetime) -> str:
        """Convert datetime to expiry code (e.g., '08JAN26')"""
        day = expiry_date.strftime('%d')
        month = expiry_date.strftime('%b').upper()
        year = expiry_date.strftime('%y')
        return f"{day}{month}{year}"
    
    # =========================================================================
    # FETCH & PROCESSING
    # =========================================================================
    
    def fetch_option_chain(self) -> Optional[OptionChainSnapshot]:
        """
        Fetch fresh option chain snapshot.
        
        Process:
        1. Fetch raw from broker
        2. Filter noise
        3. Normalize
        4. Validate
        5. Cache
        6. Notify subscribers
        
        Returns:
            Cleaned snapshot, or None on error
        """
        
        if not self.universe:
            self.logger.warning("Universe not defined")
            return None
        
        fetch_start = time.time()
        
        try:
            # Step 1: Fetch raw data from broker
            raw_snapshot = self._fetch_from_broker()
            if not raw_snapshot:
                self.hiccup_detector.record_error()
                self.error_count += 1
                return None
            
            # Step 2: Filter noise
            filtered_snapshot, drops = self.noise_filter.filter_snapshot(
                raw_snapshot,
                self.snapshot_engine.previous
            )
            
            # Step 3: Normalize & validate
            is_valid, reason = self.validator.check_strike_alignment(filtered_snapshot)
            if not is_valid:
                self.logger.warning(f"Validation failed: {reason}")
            
            # Step 4: Compute quality score
            quality_score = self.validator.compute_quality_score(filtered_snapshot)
            filtered_snapshot.data_quality_score = quality_score
            
            # Step 5: Validate consistency
            if not self.snapshot_validator.validate_snapshot_consistency(filtered_snapshot):
                self.logger.warning("Snapshot consistency check failed")
                self.error_count += 1
                return None
            
            # Record latency
            fetch_latency = (time.time() - fetch_start) * 1000  # ms
            filtered_snapshot.fetch_latency_ms = fetch_latency
            self.latencies.append(fetch_latency)
            if len(self.latencies) > 100:
                self.latencies.pop(0)
            
            # Step 6: Update snapshot engine (calculate delta)
            delta = self.snapshot_engine.update_snapshot(filtered_snapshot)
            
            # Step 7: Cache
            self.snapshot_cache.store(
                self.universe.underlying,
                self.universe.expiry.expiry_code,
                filtered_snapshot
            )
            
            # Step 8: Update health
            self.hiccup_detector.record_success()
            self.fetch_count += 1
            self._update_health(quality_score)
            
            # Step 9: Notify subscribers
            if self.on_snapshot:
                self.on_snapshot(filtered_snapshot)
            
            if self.on_delta and delta.has_changes:
                self.on_delta(delta)
            
            return filtered_snapshot
        
        except Exception as e:
            self.logger.error(f"Fetch failed: {e}", exc_info=True)
            self.error_count += 1
            self.hiccup_detector.record_error()
            return None
    
    def _fetch_from_broker(self) -> Optional[OptionChainSnapshot]:
        """
        Fetch raw option chain from broker.
        
        This would call Angel One API to get all strikes for current universe.
        For now, stubbed - needs implementation with real broker calls.
        """
        
        # TODO: Implement real broker fetching
        # This should:
        # 1. Get spot price
        # 2. Fetch option chain from broker (all strikes)
        # 3. Build snapshot object
        # 4. Return with timestamps
        
        self.logger.debug(f"Fetching from broker: {self.universe.underlying} {self.universe.expiry.expiry_code}")
        
        # Stub implementation
        snapshot = OptionChainSnapshot(
            underlying=self.universe.underlying,
            expiry=self.universe.expiry.expiry_code,
            timestamp=datetime.utcnow()
        )
        
        # In real implementation, would fetch from broker and populate
        # For now, return empty to demonstrate structure
        
        return snapshot
    
    # =========================================================================
    # STREAM INTERFACE (Clean API)
    # =========================================================================
    
    def get_atm_ce(self) -> Optional[StrikeData]:
        """Get current ATM call option"""
        return self.snapshot_engine.get_atm_ce()
    
    def get_atm_pe(self) -> Optional[StrikeData]:
        """Get current ATM put option"""
        return self.snapshot_engine.get_atm_pe()
    
    def get_strike(self, offset: int) -> Optional[object]:
        """
        Get strike pair at offset from ATM.
        
        offset: 0=ATM, -1=one strike lower, +1=one strike higher
        """
        return self.snapshot_engine.get_strike(offset)
    
    def get_chain_summary(self) -> Dict:
        """Get current chain summary"""
        return self.snapshot_engine.get_chain_summary()
    
    def get_current_snapshot(self) -> Optional[OptionChainSnapshot]:
        """Get current full snapshot"""
        return self.snapshot_engine.current
    
    def get_previous_snapshot(self) -> Optional[OptionChainSnapshot]:
        """Get previous snapshot (for delta calc)"""
        return self.snapshot_engine.previous
    
    # =========================================================================
    # BACKGROUND FETCH
    # =========================================================================
    
    def start_continuous_fetch(self, interval_sec: float = 5):
        """
        Start background continuous fetching.
        
        Args:
            interval_sec: Fetch interval in seconds
        """
        
        if self._fetch_thread and self._fetch_thread.is_alive():
            self.logger.warning("Fetch thread already running")
            return
        
        self._stop_event.clear()
        self._fetch_thread = threading.Thread(
            target=self._fetch_loop,
            args=(interval_sec,),
            daemon=True,
            name="OptionChainFetch"
        )
        self._fetch_thread.start()
        self.logger.info(f"Started continuous fetch (interval: {interval_sec}s)")
    
    def stop_continuous_fetch(self):
        """Stop background fetching"""
        self._stop_event.set()
        if self._fetch_thread:
            self._fetch_thread.join(timeout=5)
        self.logger.info("Stopped continuous fetch")
    
    def _fetch_loop(self, interval_sec: float):
        """Background fetch loop"""
        
        while not self._stop_event.is_set():
            try:
                # Fetch
                snapshot = self.fetch_option_chain()
                
                if snapshot:
                    self.logger.debug(
                        f"Fetched: {snapshot.complete_pairs} complete pairs, "
                        f"{snapshot.fetch_latency_ms:.1f}ms"
                    )
            
            except Exception as e:
                self.logger.error(f"Fetch loop error: {e}", exc_info=True)
            
            # Sleep
            self._stop_event.wait(interval_sec)
    
    # =========================================================================
    # HEALTH MONITORING
    # =========================================================================
    
    def _update_health(self, quality_score: float):
        """Update health report"""
        
        total = max(self.fetch_count + self.error_count, 1)
        success_rate = (self.fetch_count / total) * 100
        
        # Determine status
        if self.hiccup_detector.should_soft_pause():
            status = DataHealthStatus.OFFLINE
        elif quality_score < 50:
            status = DataHealthStatus.UNHEALTHY
        elif quality_score < 75:
            status = DataHealthStatus.DEGRADED
        else:
            status = DataHealthStatus.HEALTHY
        
        # Detect stale data
        if self.snapshot_engine.current and self.stale_detector.is_stale(self.snapshot_engine.current):
            status = DataHealthStatus.STALE
        
        # Update report
        self.health_report = DataHealthReport(
            status=status,
            timestamp=datetime.utcnow(),
            missing_strikes_percent=0,  # TODO: calculate
            fetch_success_rate=success_rate,
            avg_fetch_latency_ms=sum(self.latencies) / len(self.latencies) if self.latencies else 0,
            last_fetch_time=datetime.utcnow(),
            is_trading_ready=status == DataHealthStatus.HEALTHY and success_rate >= 95
        )
    
    def get_health(self) -> DataHealthReport:
        """Get current health status"""
        return self.health_report
    
    def is_data_ready(self) -> bool:
        """Can strategy trade on this data"""
        return self.health_report.is_trading_ready
    
    # =========================================================================
    # METRICS & DIAGNOSTICS
    # =========================================================================
    
    def get_metrics(self) -> Dict:
        """Get engine metrics"""
        
        return {
            'status': self.health_report.status.value,
            'is_ready': self.health_report.is_trading_ready,
            'fetch_count': self.fetch_count,
            'error_count': self.error_count,
            'success_rate_percent': self.health_report.fetch_success_rate,
            'avg_latency_ms': self.health_report.avg_fetch_latency_ms,
            'current_snapshot': self.snapshot_engine.get_chain_summary(),
            'cache_size': self.snapshot_cache.get_cache_size(),
            'hiccup_errors': self.hiccup_detector.consecutive_errors,
        }
    
    def get_detailed_status(self) -> Dict:
        """Detailed status for debugging"""
        
        current = self.snapshot_engine.current
        previous = self.snapshot_engine.previous
        
        return {
            'universe': asdict(self.universe) if self.universe else None,
            'current_snapshot': asdict(current) if current else None,
            'previous_snapshot': asdict(previous) if previous else None,
            'health': asdict(self.health_report),
            'metrics': self.get_metrics(),
            'cache': self.snapshot_cache.list_cached(),
        }
    
    # =========================================================================
    # SUBSCRIPTIONS (for real-time updates)
    # =========================================================================
    
    def subscribe(self, callback: Callable):
        """Subscribe to snapshot updates"""
        self._subscribers.append(callback)
    
    def unsubscribe(self, callback: Callable):
        """Unsubscribe from updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)
    
    def _notify_subscribers(self, snapshot: OptionChainSnapshot):
        """Notify all subscribers"""
        for callback in self._subscribers:
            try:
                callback(snapshot)
            except Exception as e:
                self.logger.error(f"Subscriber error: {e}")
