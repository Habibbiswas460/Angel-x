# PHASE 5 INTEGRATION GUIDE

## How Phase 5 Fits Into the Complete System

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    ANGEL-X COMPLETE PIPELINE                │
└─────────────────────────────────────────────────────────────┘

Phase 1: Broker Adapter (Angel One)
    ↓
    Market Data Feed (Real-time)
    ↓
Phase 2B: Option Chain Data Engine
    └─→ ce_dominance, ce_volume, pe_volume, etc.
    ↓
Phase 3: Greeks Engine
    └─→ delta, gamma, theta, vega, IV
    ↓
Phase 4: Smart Money Detector
    ├─→ oi_conviction (OI buildup patterns)
    ├─→ volume_aggression (fresh volume)
    └─→ trap_probability (institution trap detection)
    ↓
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃  PHASE 5: MARKET BIAS + TRADE ELIGIBILITY    ┃
┃                  (THIS PHASE)                   ┃
┃                                                  ┃
┃  Decision Gate:                                  ┃
┃  ├─ Bias Detection (BULLISH/BEARISH/NEUTRAL)   ┃
┃  ├─ Time Gating (9:20/11:15/12:00)             ┃
┃  ├─ Greeks Safety (theta/IV/gamma)             ┃
┃  ├─ 5-Gate Eligibility                         ┃
┃  └─ Strike Selection                           ┃
┃                                                  ┃
┃  Output: ExecutionSignal (TRADE/NO-TRADE)      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
    ↓
Phase 6: Entry/Exit Signal Engine (Coming)
    └─→ precise entry levels, position management
    ↓
Phase 7: Order Execution (Coming)
    └─→ send orders to broker
```

---

## Phase 4 → Phase 5 Data Handoff

### What Phase 4 Provides

**SmartMoneySignal output (from Phase 4):**

```python
class SmartMoneySignal:
    oi_buildup: float              # OI aggression (0-1)
    volume_leadership: float       # Volume conviction (0-1)
    trap_probability: float        # Trap risk (0-1)
    ce_dominance: float            # CE activity (0-1)
    primary_buildup_direction: str # "CALL" | "PUT" | None
    institutional_action: str      # Detection of institution
    confidence_level: float        # Phase 4 confidence (0-1)
```

### What Phase 5 Needs from Phase 4

**Mapping Phase 4 → Phase 5:**

| Phase 4 Output | Phase 5 Input | Usage |
|---|---|---|
| `ce_dominance` | `ce_dominance` | Bias direction |
| `oi_buildup` | `oi_conviction` | Conviction scoring |
| `volume_leadership` | `volume_aggression` | Conviction scoring |
| `trap_probability` | `trap_probability` | Gate 4 check |
| `primary_buildup_direction` | (informational) | Bias direction hint |

---

## Data Flow: Tick-by-Tick

### Step 1: Collect Market Data (Real-time)

```python
# Every tick (e.g., every 15-30 seconds)
market_tick = {
    "timestamp": datetime.now(),
    "atm_ce_price": 500,
    "atm_pe_price": 490,
    "atm_ce_volume": 2500,
    "atm_pe_volume": 2400,
    "atm_ce_oi": 15000,
    "atm_pe_oi": 12000,
    "atm_ce_delta": 0.60,
    "atm_pe_delta": -0.65,
    "atm_ce_gamma": 0.020,
    "atm_pe_gamma": 0.018,
    "atm_ce_theta": -0.45,
    "atm_pe_theta": -0.40,
    "iv": 0.22,
}
```

### Step 2: Feed to Phase 4 (Smart Money)

```python
from src.utils.smart_money_detector import SmartMoneyDetector

detector = SmartMoneyDetector()
smart_signal = detector.analyze_smart_money(
    ce_volume=market_tick["atm_ce_volume"],
    pe_volume=market_tick["atm_pe_volume"],
    ce_oi=market_tick["atm_ce_oi"],
    pe_oi=market_tick["atm_pe_oi"],
    # ... other inputs
)

# Output: SmartMoneySignal with:
#   ce_dominance, oi_conviction, volume_aggression, trap_probability
```

### Step 3: Feed to Phase 5 (Market Bias Engine)

```python
from src.utils.phase5_market_bias_engine import MarketBiasAndEligibilityEngine
from src.utils.phase5_market_bias_models import DataHealthStatus

engine = MarketBiasAndEligibilityEngine()
engine.set_universe("NIFTY", atm_strike=20000, days_to_expiry=7.0)

# Generate Phase 5 signal
execution_signal = engine.generate_signal(
    # From Phase 4
    ce_dominance=smart_signal.ce_dominance,
    delta_ce=market_tick["atm_ce_delta"],
    delta_pe=market_tick["atm_pe_delta"],
    gamma_ce=market_tick["atm_ce_gamma"],
    gamma_pe=market_tick["atm_pe_gamma"],
    oi_conviction=smart_signal.oi_buildup,
    volume_aggression=smart_signal.volume_leadership,
    trap_probability=smart_signal.trap_probability,
    
    # Greeks data
    theta_current=market_tick["atm_ce_theta"],
    theta_previous=previous_theta,  # from last tick
    iv_current=market_tick["iv"],
    iv_previous=previous_iv,        # from last tick
    
    # Quality data
    data_health=DataHealthStatus.GREEN,
    data_age_seconds=calculate_data_age(),
    current_time=datetime.now().time(),
)

# Output: ExecutionSignal with TRADE/NO-TRADE decision
```

### Step 4: Use Phase 5 Signal

```python
if execution_signal.trade_allowed:
    # Execute trade (Phase 6)
    entry_signal = entry_engine.generate_entry(
        market_bias_signal=execution_signal,
        market_data=market_tick,
    )
    
    # Place order via broker
    order = place_order(
        symbol="NIFTY",
        option_type=execution_signal.direction,  # CALL or PUT
        strike=calculate_strike(execution_signal.strike_offset),
        quantity=calculate_quantity(),
        order_type="MIS",  # Intraday
    )
else:
    # Block trade, log reason
    log_blocked(execution_signal.block_reason)
    
    # Wait for next tick
```

---

## Integration Example: Real-Time Loop

### Complete Trading Loop

```python
#!/usr/bin/env python3
"""
Real-time trading loop: Phase 4 → Phase 5 → Execution
"""

from src.utils.phase5_market_bias_engine import MarketBiasAndEligibilityEngine
from src.utils.phase5_market_bias_models import DataHealthStatus
from src.utils.smart_money_detector import SmartMoneyDetector
from datetime import datetime, time
import time as time_module

# Initialize engines
phase4_detector = SmartMoneyDetector()
phase5_engine = MarketBiasAndEligibilityEngine()
phase5_engine.set_universe("NIFTY", atm_strike=20000, days_to_expiry=7.0)

# State
previous_theta = None
previous_iv = None
signal_count = 0

def process_market_tick(market_data):
    """Process one market data tick"""
    global previous_theta, previous_iv, signal_count
    
    # Step 1: Phase 4 - Smart Money Detection
    smart_signal = phase4_detector.analyze_smart_money(
        ce_volume=market_data["atm_ce_volume"],
        pe_volume=market_data["atm_pe_volume"],
        ce_oi=market_data["atm_ce_oi"],
        pe_oi=market_data["atm_pe_oi"],
        # ... other inputs
    )
    
    # Step 2: Phase 5 - Market Bias + Eligibility
    execution_signal = phase5_engine.generate_signal(
        # From Phase 4
        ce_dominance=smart_signal.ce_dominance,
        delta_ce=market_data["atm_ce_delta"],
        delta_pe=market_data["atm_pe_delta"],
        gamma_ce=market_data["atm_ce_gamma"],
        gamma_pe=market_data["atm_pe_gamma"],
        oi_conviction=smart_signal.oi_buildup,
        volume_aggression=smart_signal.volume_leadership,
        trap_probability=smart_signal.trap_probability,
        
        # Greeks
        theta_current=market_data["atm_ce_theta"],
        theta_previous=previous_theta or market_data["atm_ce_theta"],
        iv_current=market_data["iv"],
        iv_previous=previous_iv or market_data["iv"],
        
        # Quality
        data_health=DataHealthStatus.GREEN,
        data_age_seconds=0,
        current_time=datetime.now().time(),
    )
    
    # Update state
    previous_theta = market_data["atm_ce_theta"]
    previous_iv = market_data["iv"]
    
    # Step 3: Process Signal
    if execution_signal.trade_allowed:
        signal_count += 1
        print(f"✓ SIGNAL #{signal_count}: {execution_signal.direction} @ {execution_signal.confidence_level:.0%}")
        
        # Send to execution layer (Phase 6)
        handle_trade_signal(execution_signal, market_data)
    else:
        print(f"✗ BLOCKED: {execution_signal.block_reason}")

def handle_trade_signal(signal, market_data):
    """Handle valid trade signal"""
    print(f"""
    Trade Decision:
    ├─ Direction: {signal.direction}
    ├─ Strike: {signal.strike_offset}
    ├─ Confidence: {signal.confidence_level:.0%}
    └─ Time: {datetime.now().time()}
    """)
    
    # TODO: Pass to Phase 6 entry/exit engine
    # TODO: Place order via broker

# Main loop
if __name__ == "__main__":
    print("Starting real-time trading loop...")
    print("Market hours: 9:20 - 15:30 IST")
    
    while True:
        try:
            # Get market data (from your data feed)
            market_data = fetch_market_data()  # Your implementation
            
            if market_data:
                process_market_tick(market_data)
            
            # Wait before next tick
            time_module.sleep(30)  # 30-second ticks
            
        except KeyboardInterrupt:
            print("Trading loop stopped.")
            break
        except Exception as e:
            print(f"Error: {e}")
            continue
```

---

## Integration Checklist

- [ ] Phase 4 engine outputting SmartMoneySignal
- [ ] Phase 5 engine initialized with universe data
- [ ] Market data feed connected (real-time)
- [ ] Data quality checks passing
- [ ] Time windows configured (9:20/11:15/12:00)
- [ ] Theta tracking enabled
- [ ] Trap probability integrated
- [ ] ExecutionSignal being generated
- [ ] Signal routing to Phase 6 (planned)
- [ ] Trade execution working

---

## Troubleshooting

### Problem: Signal not generating
**Check:**
1. Is market_data valid? (data_health=GREEN)
2. Is data fresh? (data_age_seconds<5)
3. Is it trading hours? (9:20-15:30)

### Problem: Always getting NEUTRAL bias
**Check:**
1. Is ce_dominance close to 0.5?
2. Are delta values balanced?
3. Are gamma values similar?

### Problem: Always blocked at 12:00
**Expected:** theta_danger blocks all trades post-12:00  
**This is by design:** Capital protection mode

### Problem: Stale data errors
**Solution:**
1. Increase data_age_seconds tolerance
2. Check data feed connectivity
3. Ensure real-time market data

---

## Performance Metrics

### Expected Throughput
- **Signals per minute:** 1-3 (conservative)
- **False trade rate:** <10% (conservative)
- **Signal latency:** <100ms
- **Processing per tick:** <50ms

### Resource Usage
- **CPU:** <1% (idle), <5% (active)
- **Memory:** ~50MB (phase 4+5 combined)
- **Disk:** Negligible (real-time only)

---

## Configuration

### Phase 5 Configuration

```python
from src.utils.phase5_market_bias_models import Phase5Config

config = Phase5Config()

# Bias thresholds
config.bias_low_threshold = 0.5         # Adjust conviction thresholds
config.bias_medium_threshold = 0.75
config.bias_high_threshold = 0.9

# Eligibility
config.min_bias_strength = BiasStrength.MEDIUM
config.max_trap_probability = 0.3       # 30% max trap risk

# Time windows
config.morning_start = time(9, 20)
config.morning_end = time(11, 15)
config.caution_start = time(11, 15)
config.caution_end = time(12, 0)

# Data freshness
config.max_data_age_seconds = 5

# Apply to engine
engine = MarketBiasAndEligibilityEngine(config=config)
```

---

## Next Steps

1. **Ensure Phase 4 is working** - generates SmartMoneySignal
2. **Set up market data feed** - real-time NIFTY options data
3. **Initialize Phase 5 engine** - with universe configuration
4. **Start generating signals** - feed Phase 4 + market data
5. **Monitor signal quality** - verify bias detection
6. **Route to Phase 6** - entry/exit engine (coming)
7. **Execute trades** - via broker adapter

---

## Files & References

**Phase 5 Implementation:**
- `src/utils/phase5_market_bias_engine.py` - Main orchestrator
- `src/utils/phase5_market_bias_constructor.py` - Bias detection
- `src/utils/phase5_time_and_greeks_gate.py` - Time + safety gates
- `src/utils/phase5_eligibility_and_selector.py` - 5 gates + selector
- `src/utils/phase5_market_bias_models.py` - Data models

**Documentation:**
- `docs/PHASE5_COMPLETION_REPORT.md` - Complete reference
- `docs/PHASE5_QUICK_REFERENCE.md` - Quick guide

**Tests:**
- `scripts/phase5_market_bias_engine_test.py` - 19 test cases

---

*Angel-X Integration Guide | Phase 5 | December 2024*
