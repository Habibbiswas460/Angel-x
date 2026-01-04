# Phase 2B: Option Chain Data Engine - Architecture & Integration Guide

**Date:** January 4, 2026  
**Version:** 2.0  
**Status:** Complete & Tested ✅

---

## 🎯 MISSION: Clean Option Chain Data Pipeline

Transform raw broker data into **low-latency, noise-free, decision-ready** option chain information for strategy layer.

---

## 📊 FULL SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│                    Strategy Layer                              │
│         (Receives clean, typed data objects)                   │
│                                                                 │
│    Used by: entry_engine, bias_engine, risk_manager           │
│                                                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────┐
│              Clean Stream Interface                            │
│  (Broker-independent, noise-free data)                         │
│                                                                │
│  • get_atm_ce() → StrikeData                                  │
│  • get_atm_pe() → StrikeData                                  │
│  • get_strike(offset) → StrikePair                            │
│  • get_chain_summary() → Dict                                 │
│                                                                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌────────────────────────────────────────────────────────────────┐
│         OptionChainDataEngine (Orchestrator)                   │
│                                                                │
│  • Fetch coordination                                          │
│  • Filter orchestration                                        │
│  • Snapshot management                                         │
│  • Health monitoring                                           │
│  • Subscriber notifications                                    │
│                                                                │
└─────────┬────────────────┬────────────────┬────────────────────┘
          │                │                │
          ↓                ↓                ↓
    ┌──────────┐  ┌──────────┐     ┌──────────────┐
    │ Fetch    │  │ Validate │     │ Snapshot    │
    │ Strategy │  │ & Filter │     │ Management   │
    └──────────┘  └──────────┘     └──────────────┘
          │                │                │
          ↓                ↓                ↓
    ┌──────────────────────────────────────────────┐
    │         Broker Data Flow                     │
    │                                              │
    │  Angel One API                              │
    │  ├─ Option chain fetch                      │
    │  ├─ Symbol resolution                       │
    │  ├─ Market data                             │
    │  └─ Rate limiting awareness                 │
    │                                              │
    └──────────────────────────────────────────────┘
```

---

## 🔄 DATA FLOW SEQUENCE

```
1. UNIVERSE DEFINITION
   └─ set_universe("NIFTY", expiry_date, 20050.0, strikes_range=5)
   └─ Scope locked: Only ATM ±5 strikes, only weekly
   └─ Expected: 22 strikes (11 CE + 11 PE)

2. FETCH TRIGGER
   └─ Automatic via background thread (every 5 sec)
   └─ OR manual: fetch_option_chain()

3. RAW FETCH
   └─ Call broker API for all strikes in range
   └─ Build raw OptionChainSnapshot
   └─ Timestamp each strike with exchange time

4. NOISE FILTERING
   NoiseFilter.filter_snapshot()
   ├─ Drop zero volume strikes
   ├─ Detect frozen LTP (no change + no volume)
   ├─ Detect LTP spikes (> 10% jump)
   ├─ Detect OI spikes (> 20% jump)
   └─ Build filtered snapshot

5. DATA VALIDATION
   DataValidator.validate()
   ├─ Check expiry matches
   ├─ Check strike alignment (regular intervals)
   ├─ Check completeness (min pairs)
   ├─ Compute quality score (0-100)
   └─ Flag if partial chain

6. SNAPSHOT MANAGEMENT
   SnapshotEngine.update_snapshot()
   ├─ Store current as new
   ├─ Save previous as old
   ├─ Calculate deltas (OI, volume, LTP changes)
   ├─ Track history (last 100 snapshots)
   └─ Compute momentum hints (raw)

7. CACHING
   SnapshotCache.store()
   ├─ Cache by (underlying, expiry)
   ├─ Fast retrieval for strategy
   └─ Multi-expiry support

8. HEALTH CHECK
   DataHealthReport.update()
   ├─ Check fetch success rate
   ├─ Check for stale data
   ├─ Check broker hiccups
   ├─ Determine data readiness
   └─ Generate health status

9. NOTIFICATION
   ├─ Call on_snapshot(snapshot) if subscribed
   ├─ Call on_delta(delta) if subscribed
   ├─ Update metrics
   └─ Log activity

10. INTERFACE READY
    Strategy can call:
    ├─ engine.get_atm_ce() → Clean StrikeData
    ├─ engine.get_atm_pe() → Clean StrikeData
    ├─ engine.get_strike(-1) → StrikePair
    └─ engine.get_chain_summary() → Dict
```

---

## 🧩 MODULE INTERDEPENDENCIES

```
OptionChainDataEngine (Main)
├─ Uses: AngelOnePhase2 (broker adapter)
├─ Uses: NoiseFilter
├─ Uses: DataValidator
├─ Uses: StaleDataDetector
├─ Uses: BrokerHiccupDetector
├─ Uses: SnapshotEngine
├─ Uses: SnapshotCache
├─ Uses: SnapshotValidator
└─ Produces: OptionChainSnapshot, OptionChainDelta

SnapshotEngine
├─ Manages: OptionChainSnapshot (current + previous)
├─ Calculates: OptionChainDelta
└─ Produces: StrikeData interface

NoiseFilter
├─ Reads: OptionChainSnapshot
├─ Reads: Previous OptionChainSnapshot (optional)
├─ Filters: StrikeData (individual validation)
└─ Produces: Cleaned OptionChainSnapshot

DataValidator
├─ Reads: OptionChainSnapshot
├─ Validates: Alignment, completeness, quality
└─ Produces: Boolean, reason, quality_score

Data Models (No dependencies)
├─ StrikeData
├─ StrikePair
├─ OptionChainSnapshot
├─ OptionChainDelta
├─ ExpiryInfo
└─ UniverseDefinition
```

---

## 🔗 INTEGRATION WITH EXISTING CODE

### Step 1: Add to main.py

```python
from src.utils.option_chain_engine import OptionChainDataEngine
from datetime import datetime, timedelta

class StrategyOrchestrator:
    def __init__(self, broker_adapter):
        self.broker = broker_adapter
        
        # Initialize option chain engine
        self.data_engine = OptionChainDataEngine(broker_adapter, config={
            'min_volume': 0,
            'max_ltp_jump_percent': 10.0,
            'max_oi_jump_percent': 20.0,
            'stale_threshold_sec': 60,
            'error_threshold': 3
        })
    
    def initialize(self):
        # Define universe
        expiry_date = datetime.utcnow() + timedelta(days=4)  # 4 days = weekly
        spot_price = 20050.0  # Get from broker
        
        self.data_engine.set_universe(
            underlying="NIFTY",
            expiry_date=expiry_date,
            atm_reference=spot_price,
            strikes_range=5
        )
        
        # Start continuous fetch
        self.data_engine.start_continuous_fetch(interval_sec=5)
    
    def run_trading_loop(self):
        while True:
            # Check if data is ready
            if not self.data_engine.is_data_ready():
                logger.warning("Data not ready, soft pausing")
                time.sleep(1)
                continue
            
            # Get clean data
            atm_ce = self.data_engine.get_atm_ce()
            atm_pe = self.data_engine.get_atm_pe()
            chain_summary = self.data_engine.get_chain_summary()
            
            # Pass to strategy engines
            signal = self.entry_engine.generate_signal(atm_ce, atm_pe)
            if signal:
                # Execute trade
                pass
            
            time.sleep(0.5)
```

### Step 2: Update entry_engine.py

```python
from src.utils.option_chain_engine import OptionChainDataEngine

class EntryEngine:
    def __init__(self, data_engine: OptionChainDataEngine):
        self.data_engine = data_engine
    
    def generate_signal(self):
        # Get clean data from engine
        atm_ce = self.data_engine.get_atm_ce()
        atm_pe = self.data_engine.get_atm_pe()
        chain = self.data_engine.get_current_snapshot()
        
        # Use for signal generation
        # (entry logic here)
        
        return signal
```

### Step 3: Update bias_engine.py

```python
def analyze_market_state(self, data_engine):
    # Get clean snapshot
    snapshot = data_engine.get_current_snapshot()
    previous = data_engine.get_previous_snapshot()
    
    # Calculate OI changes (provided by engine)
    delta = self.data_engine.snapshot_engine.current_delta
    
    # Use for bias detection
    # (Greeks will be added in Phase 3)
    
    return market_bias
```

---

## 📈 DATA QUALITY LAYERS

```
Layer 1: RAW BROKER DATA
├─ As-is from Angel One API
├─ May have garbage
├─ Timestamps present
└─ No validation

        ↓ NOISE FILTER

Layer 2: FILTERED DATA
├─ Zero volume removed
├─ Frozen LTP rejected
├─ Spikes detected
└─ Partial chains flagged

        ↓ VALIDATOR

Layer 3: VALIDATED DATA
├─ Strike alignment checked
├─ Expiry verified
├─ Completeness confirmed
├─ Quality scored
└─ Consistency validated

        ↓ SNAPSHOT ENGINE

Layer 4: SNAPSHOT DATA
├─ Current state
├─ Previous state (for delta)
├─ Deltas calculated
├─ History tracked
└─ Momentum hints generated

        ↓ STRATEGY LAYER

Layer 5: DECISION READY
├─ Clean StrikeData objects
├─ No broker knowledge needed
├─ Noise-free
├─ Ready for logic
└─ Fully typed
```

---

## ⚡ PERFORMANCE OPTIMIZATION NOTES

### Fetch Optimization
- Use pull mode (not push/websocket) → simpler, rate-limit friendly
- Interval: 5 seconds = 720 fetches/day
- Within Angel One rate limits

### Filter Optimization
- Filter at broker level (don't request unnecessary strikes)
- Quick checks first (zero volume)
- Spike detection using only previous value (O(1))

### Memory Optimization
- Cache limited to 100 snapshots (~5MB)
- Old snapshots auto-removed
- Lazy delta calculation

### Latency Optimization
- Parallel validation (could be threaded)
- Minimal data copying
- Direct broker API (no intermediate servers)

---

## 🔍 DEBUGGING & MONITORING

### Check Engine Health
```python
health = engine.get_health()
print(f"Status: {health.status}")
print(f"Ready: {health.is_trading_ready}")
print(f"Success rate: {health.fetch_success_rate}%")
print(f"Avg latency: {health.avg_fetch_latency_ms}ms")
```

### Get Metrics
```python
metrics = engine.get_metrics()
print(f"Fetch count: {metrics['fetch_count']}")
print(f"Error count: {metrics['error_count']}")
print(f"Quality score: {metrics['current_snapshot']['data_quality']}")
```

### Get Detailed Status
```python
status = engine.get_detailed_status()
print(json.dumps(status, indent=2, default=str))
```

### Enable Detailed Logging
```python
import logging
logging.getLogger('src.utils.option_chain_engine').setLevel(logging.DEBUG)
```

---

## 🛡️ ERROR HANDLING & RECOVERY

```
Scenario 1: Broker Timeout
├─ Record error in BrokerHiccupDetector
├─ After 3 errors: set status to OFFLINE
├─ Soft pause trading (no orders placed)
├─ Auto-retry continues
└─ Recovery: next successful fetch clears error count

Scenario 2: Partial Chain
├─ NoiseFilter flags as is_partial=True
├─ DataValidator detects incomplete pairs
├─ Quality score drops below 75
├─ Status becomes DEGRADED
├─ Strategy can choose to skip this cycle
└─ Resume when chain completes

Scenario 3: Stale Data
├─ StaleDataDetector notices data age > threshold
├─ Status becomes STALE
├─ is_trading_ready = False
├─ Strategy pauses
└─ Resume on next fresh fetch

Scenario 4: Data Corruption
├─ SnapshotValidator detects inconsistency
├─ Snapshot rejected
├─ Error recorded
└─ Retry on next fetch
```

---

## 📋 COMPLIANCE CHECKLIST

- ✅ Zero garbage data to strategy
- ✅ Expiry always matched
- ✅ CE/PE always aligned
- ✅ OI/Volume changes calculated
- ✅ Broker connectivity monitored
- ✅ Health status reported
- ✅ Rate limits respected
- ✅ Partial chains detected
- ✅ Stale data flagged
- ✅ Quality scored

---

## 🚀 NEXT PHASE (Phase 3)

**Option Chain Data Engine** (complete) ✅  
↓  
**Phase 3: Greeks Calculation & Bias Detection**
- Calculate Delta, Gamma, Theta, Vega
- Greeks-based market bias
- Entry signal generation
- Trap detection

---

**Status:** ✅ Complete & Integrated  
**Quality:** Production-ready  
**Tests:** All passing  
**Documentation:** Complete  

**Ready for:** Phase 3 implementation

---

*Architecture Document: January 4, 2026*
