"""
PHASE 8: Latency Optimization Layer
Minimize data→signal→order latency for speed edge
"""

import time
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
from collections import OrderedDict


@dataclass
class StrikePriority:
    """Define priority levels for strike processing"""
    ATM: int = 1
    ITM_1: int = 2
    OTM_1: int = 2
    ITM_2: int = 3
    OTM_2: int = 3
    FAR: int = 4


class DifferentialProcessor:
    """
    Process only changed data instead of full snapshots
    Dramatically reduces processing overhead
    """
    
    def __init__(self):
        self.last_snapshot: Dict = {}
        self.last_update_time: float = 0
    
    def get_changes(self, new_snapshot: Dict) -> Dict:
        """
        Extract only what changed since last snapshot
        Returns: {strike: changed_fields}
        """
        changes = {}
        
        for strike, data in new_snapshot.items():
            if strike not in self.last_snapshot:
                # New strike - all data is change
                changes[strike] = data
            else:
                # Check what changed
                old_data = self.last_snapshot[strike]
                changed_fields = {}
                
                for key, value in data.items():
                    if key not in old_data or old_data[key] != value:
                        changed_fields[key] = value
                
                if changed_fields:
                    changes[strike] = changed_fields
        
        # Update last snapshot
        self.last_snapshot = new_snapshot.copy()
        self.last_update_time = time.time()
        
        return changes
    
    def is_stale(self, max_age_seconds: int = 5) -> bool:
        """Check if cached data is too old"""
        if not self.last_update_time:
            return True
        return (time.time() - self.last_update_time) > max_age_seconds


class PriorityStrikeProcessor:
    """
    Process strikes in priority order
    ATM and near strikes get processed first
    """
    
    def __init__(self, atm_strike: int):
        self.atm_strike = atm_strike
    
    def prioritize_strikes(self, strikes: List[Dict]) -> List[Dict]:
        """
        Sort strikes by priority
        ATM → ±1 → ±2 → Far
        """
        def get_priority(strike_data: Dict) -> int:
            strike = strike_data.get('strike', 0)
            distance = abs(strike - self.atm_strike)
            
            if distance == 0:
                return StrikePriority.ATM
            elif distance <= 100:  # ±1 strike
                return StrikePriority.ITM_1
            elif distance <= 200:  # ±2 strikes
                return StrikePriority.ITM_2
            else:
                return StrikePriority.FAR
        
        return sorted(strikes, key=get_priority)
    
    def filter_relevant_strikes(self, strikes: List[Dict], max_strikes: int = 10) -> List[Dict]:
        """
        Keep only most relevant strikes
        Reduces processing overhead
        """
        prioritized = self.prioritize_strikes(strikes)
        return prioritized[:max_strikes]


class BatchProcessor:
    """
    Batch multiple API calls to reduce round-trips
    """
    
    def __init__(self, batch_size: int = 5, max_wait_ms: int = 50):
        self.batch_size = batch_size
        self.max_wait_ms = max_wait_ms
        self.pending_requests: List = []
        self.last_batch_time: float = time.time()
    
    def should_flush(self) -> bool:
        """Check if batch should be processed"""
        if len(self.pending_requests) >= self.batch_size:
            return True
        
        wait_time_ms = (time.time() - self.last_batch_time) * 1000
        if wait_time_ms >= self.max_wait_ms and self.pending_requests:
            return True
        
        return False
    
    def add_request(self, request):
        """Add request to batch"""
        self.pending_requests.append(request)
    
    def flush(self) -> List:
        """Process batch and return results"""
        batch = self.pending_requests.copy()
        self.pending_requests.clear()
        self.last_batch_time = time.time()
        return batch


class AsyncIsolator:
    """
    Run slow operations asynchronously without blocking main thread
    Keep critical path fast
    """
    
    def __init__(self, max_workers: int = 3):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.pending_tasks: Dict[str, asyncio.Future] = {}
    
    def run_async(self, task_id: str, func, *args, **kwargs):
        """
        Run function asynchronously
        Returns immediately, function runs in background
        """
        future = self.executor.submit(func, *args, **kwargs)
        self.pending_tasks[task_id] = future
        return future
    
    def get_result(self, task_id: str, timeout: float = 0.1) -> Optional[any]:
        """
        Get result if ready, don't wait
        """
        if task_id not in self.pending_tasks:
            return None
        
        future = self.pending_tasks[task_id]
        
        try:
            result = future.result(timeout=timeout)
            del self.pending_tasks[task_id]
            return result
        except:
            return None  # Not ready yet
    
    def cleanup_completed(self):
        """Remove completed tasks"""
        completed = [tid for tid, future in self.pending_tasks.items() if future.done()]
        for tid in completed:
            del self.pending_tasks[tid]


class CacheLayer:
    """
    Smart caching with TTL and invalidation
    Reduce redundant calculations
    """
    
    def __init__(self, default_ttl: int = 5):
        self.cache: OrderedDict = OrderedDict()
        self.ttl_map: Dict[str, float] = {}
        self.default_ttl = default_ttl
        self.max_size = 100
    
    def get(self, key: str) -> Optional[any]:
        """Get from cache if valid"""
        if key not in self.cache:
            return None
        
        # Check TTL
        if key in self.ttl_map:
            if time.time() > self.ttl_map[key]:
                # Expired
                del self.cache[key]
                del self.ttl_map[key]
                return None
        
        # Move to end (LRU)
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def set(self, key: str, value: any, ttl: Optional[int] = None):
        """Set cache with TTL"""
        self.cache[key] = value
        
        ttl = ttl or self.default_ttl
        self.ttl_map[key] = time.time() + ttl
        
        # Enforce max size (LRU eviction)
        if len(self.cache) > self.max_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            if oldest_key in self.ttl_map:
                del self.ttl_map[oldest_key]
    
    def invalidate(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern is None:
            # Clear all
            self.cache.clear()
            self.ttl_map.clear()
        else:
            # Clear matching pattern
            keys_to_remove = [k for k in self.cache.keys() if pattern in k]
            for key in keys_to_remove:
                del self.cache[key]
                if key in self.ttl_map:
                    del self.ttl_map[key]


class LatencyOptimizer:
    """
    Master latency optimization orchestrator
    Combines all optimization techniques
    """
    
    def __init__(self, atm_strike: int, enable_batching: bool = True):
        self.diff_processor = DifferentialProcessor()
        self.priority_processor = PriorityStrikeProcessor(atm_strike)
        self.batch_processor = BatchProcessor() if enable_batching else None
        self.async_isolator = AsyncIsolator()
        self.cache = CacheLayer()
        
        # Performance tracking
        self.processing_times: List[float] = []
        self.optimization_enabled = True
    
    def update_atm(self, new_atm: int):
        """Update ATM strike for priority processing"""
        self.priority_processor.atm_strike = new_atm
    
    def process_option_chain(self, raw_data: Dict, mode: str = "differential") -> Dict:
        """
        Process option chain with optimizations
        
        Modes:
        - differential: Only process changed data
        - priority: Process important strikes first
        - full: Process everything (fallback)
        """
        start_time = time.time()
        
        if mode == "differential" and not self.diff_processor.is_stale():
            # Only process changes
            changes = self.diff_processor.get_changes(raw_data)
            result = {"mode": "differential", "data": changes}
        
        elif mode == "priority":
            # Process priority strikes first
            strikes = raw_data.get('strikes', [])
            filtered = self.priority_processor.filter_relevant_strikes(strikes)
            result = {"mode": "priority", "data": filtered}
        
        else:
            # Full processing
            result = {"mode": "full", "data": raw_data}
        
        # Track performance
        processing_time = (time.time() - start_time) * 1000
        self.processing_times.append(processing_time)
        
        return result
    
    def async_calculate_greeks(self, strike_data: Dict, task_id: str):
        """
        Calculate Greeks asynchronously
        Don't block main signal generation
        """
        def _calculate():
            # Placeholder for actual Greeks calculation
            time.sleep(0.1)  # Simulate computation
            return {"delta": 0.5, "gamma": 0.02, "theta": -0.5, "vega": 0.3}
        
        return self.async_isolator.run_async(task_id, _calculate)
    
    def batch_add_request(self, request: Dict):
        """Add request to batch queue"""
        if self.batch_processor:
            self.batch_processor.add_request(request)
            
            if self.batch_processor.should_flush():
                return self.batch_processor.flush()
        
        return None
    
    def get_cached_calculation(self, cache_key: str, calc_func, *args, ttl: int = 5):
        """
        Get from cache or calculate and cache
        """
        # Check cache
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached
        
        # Calculate
        result = calc_func(*args)
        
        # Cache
        self.cache.set(cache_key, result, ttl)
        
        return result
    
    def get_performance_stats(self) -> Dict:
        """Get optimization performance statistics"""
        if not self.processing_times:
            return {"avg_processing_ms": 0, "total_processed": 0}
        
        recent = self.processing_times[-100:]  # Last 100
        
        return {
            "avg_processing_ms": sum(recent) / len(recent),
            "min_processing_ms": min(recent),
            "max_processing_ms": max(recent),
            "total_processed": len(self.processing_times),
            "cache_size": len(self.cache.cache),
            "pending_async": len(self.async_isolator.pending_tasks)
        }
    
    def optimize_signal_path(self, raw_market_data: Dict, 
                            calculate_greeks: bool = True,
                            use_cache: bool = True) -> Dict:
        """
        Full optimization pipeline: Data → Signal
        Minimize latency end-to-end
        """
        pipeline_start = time.time()
        
        # Step 1: Differential processing
        processed_data = self.process_option_chain(raw_market_data, mode="differential")
        
        # Step 2: Priority filtering
        if processed_data["mode"] != "differential":
            processed_data = self.process_option_chain(raw_market_data, mode="priority")
        
        # Step 3: Greeks calculation (async if enabled)
        if calculate_greeks:
            strikes = processed_data.get("data", {})
            
            # Handle both dict and list formats
            if isinstance(strikes, dict):
                items = strikes.items()
            elif isinstance(strikes, list):
                items = [(s.get('strike', i), s) for i, s in enumerate(strikes)]
            else:
                items = []
            
            for strike, data in items:
                cache_key = f"greeks_{strike}_{data.get('ltp', 0)}"
                
                if use_cache:
                    # Try cache first
                    greeks = self.cache.get(cache_key)
                    if greeks:
                        data['greeks'] = greeks
                        continue
                
                # Async calculation
                task_id = f"greeks_{strike}"
                self.async_calculate_greeks(data, task_id)
        
        # Step 4: Cleanup async tasks
        self.async_isolator.cleanup_completed()
        
        total_latency_ms = (time.time() - pipeline_start) * 1000
        
        return {
            "data": processed_data,
            "latency_ms": total_latency_ms,
            "optimizations_applied": processed_data["mode"]
        }
    
    def reset_optimizations(self):
        """Reset all optimization state (for testing)"""
        self.diff_processor = DifferentialProcessor()
        self.cache.invalidate()
        self.processing_times.clear()
