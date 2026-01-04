# PHASE 5 QUICK REFERENCE GUIDE

## One-Sentence Summary
**"3-state market bias detection + 5-gate eligibility = binary TRADE/NO-TRADE decision"**

---

## The 3-State Bias System

```
BULLISH      NEUTRAL      BEARISH
(Trade CE)   (No Trade)   (Trade PE)
   ✅           ❌           ✅
```

- **BULLISH:** CE dominance >55% + Delta CE up + Gamma CE support
- **BEARISH:** CE dominance <45% + Delta PE down + Gamma PE support
- **NEUTRAL:** Mixed signals = Default NO-TRADE (capital protection)

---

## The 5-Gate Eligibility System

All gates must pass (AND logic):

```
Gate 1: Bias ≠ NEUTRAL              ✓ or ✗
   ↓
Gate 2: Strength ≥ MEDIUM           ✓ or ✗
   ↓
Gate 3: Time ∈ {ALLOWED, CAUTION}  ✓ or ✗
   ↓
Gate 4: Trap Probability ≤ 30%      ✓ or ✗
   ↓
Gate 5: Data Health = GREEN         ✓ or ✗
   ↓
All Pass → TRADE_ALLOWED=True
Any Fail → TRADE_ALLOWED=False + block_reason
```

---

## Strength Levels

| Level | Conviction | Status | Trade? |
|-------|-----------|--------|--------|
| LOW | <0.50 | 🔴 Weak | ❌ NO |
| MEDIUM | 0.50-0.75 | 🟡 OK | ✅ YES |
| HIGH | 0.75-0.90 | 🟢 Strong | ✅ YES |
| EXTREME | >0.90 | 🟢🟢 Max | ✅ YES |

---

## Time Windows

| Window | Time | Status | Action |
|--------|------|--------|--------|
| **ALLOWED** | 9:20-11:15 | ✅ | Trade freely |
| **CAUTION** | 11:15-12:00 | ⚠️ | High filter |
| **THETA_DANGER** | 12:00+ | 🛑 | BLOCKED |

**Why 12:00+ blocked?** Theta crush risk + rapid time decay

---

## Strike Selection

**BULLISH → Best CALL**
- Choose between: ATM or ATM+1
- Scoring: Gamma (50%) + Fresh OI (30%) + Volume (20%)

**BEARISH → Best PUT**
- Choose between: ATM or ATM-1
- Scoring: Gamma (50%) + Fresh OI (30%) + Volume (20%)

---

## Input Data Required

```python
# Bias inputs (from Phase 4)
ce_dominance          # CE activity %
delta_ce              # Call delta
delta_pe              # Put delta
gamma_ce              # Call gamma
gamma_pe              # Put gamma
oi_conviction         # OI pattern strength
volume_aggression     # Fresh volume
trap_probability      # Smart money trap risk

# Greeks inputs
theta_current         # Current theta
theta_previous        # Previous theta
iv_current            # Current IV
iv_previous           # Previous IV

# Quality inputs
data_health           # GREEN/YELLOW/RED
data_age_seconds      # Freshness
current_time          # Trading time
```

---

## Output: ExecutionSignal

```python
ExecutionSignal(
    trade_allowed=True/False,              # Binary decision
    direction='CALL' or 'PUT' or 'NEUTRAL', # Direction
    strike_offset='ATM' or 'ATM+1' etc.,   # Strike selection
    confidence_level=0.88,                 # 0-1 confidence
    block_reason='...' if not allowed,    # Why blocked
)
```

---

## Safety Guarantees

✅ **Never forced to trade**
- Default: NO TRADE if ANY gate fails
- Requirement: ALL 5 gates must pass

✅ **Theta protection**
- 12:00+ = AUTO BLOCK
- Theta spike = BLOCK
- Extreme theta = BLOCK

✅ **Data quality**
- Stale data (>5s) = BLOCK
- Health RED = BLOCK
- Missing data = BLOCK

✅ **Trap avoidance**
- Trap prob >30% = BLOCK
- Smart money indicator = CONSIDERED

---

## Quick Usage

```python
from src.utils.phase5_market_bias_engine import MarketBiasAndEligibilityEngine

engine = MarketBiasAndEligibilityEngine()
engine.set_universe("NIFTY", atm_strike=20000, days_to_expiry=7.0)

signal = engine.generate_signal(
    ce_dominance=0.65,
    delta_ce=0.60,
    delta_pe=-0.62,
    gamma_ce=0.020,
    gamma_pe=0.012,
    oi_conviction=0.75,
    volume_aggression=0.70,
    trap_probability=0.15,
    theta_current=-0.40,
    theta_previous=-0.35,
    iv_current=0.22,
    iv_previous=0.23,
    data_health=DataHealthStatus.GREEN,
    data_age_seconds=2,
    current_time=datetime.now().time(),
)

if signal.trade_allowed:
    execute_trade(signal.direction, signal.strike_offset)
else:
    log_blocked_reason(signal.block_reason)
```

---

## Common Blocking Reasons

| Reason | Cause | Fix |
|--------|-------|-----|
| "Bias is NEUTRAL" | Mixed signals | Wait for clear direction |
| "Bias strength LOW" | Weak conviction | Wait for stronger signal |
| "Time window THETA_DANGER" | Post 12:00 | Only trade 9:20-12:00 |
| "Trap probability HIGH" | Institutional trap setup | Avoid obvious levels |
| "Data health RED" | Bad data quality | Wait for good data |
| "Theta spike detected" | Rapid time decay | Wait for stability |
| "IV crush detected" | Volatility collapsing | Avoid low IV |
| "Gamma exhaustion" | No gamma support | Wait for recovery |
| "Data stale (>5s)" | Late market data | Ensure real-time feed |

---

## Performance Targets

- **Signal generation:** <100ms ✅
- **Real-time capable:** YES ✅
- **Scalability:** 1000+ signals/sec ✅
- **Memory:** ~2MB per instance ✅

---

## Test Results

**19/19 PASSING ✅**

- 3 bias detection tests
- 3 time window tests
- 2 Greeks guard tests
- 3 eligibility tests
- 2 strike selection tests
- 3 integration tests
- 3 safety edge case tests

---

## Philosophy

**"Strategy never forced to trade"**

- 🛑 Default = NO TRADE (capital protection)
- ✅ Requirements = ALL gates pass
- 🎯 Goal = High probability trades only
- 🔒 Safety = Multiple layers

---

## Files

```
Production Code:
├─ src/utils/phase5_market_bias_models.py (enums, classes)
├─ src/utils/phase5_market_bias_constructor.py (3-state bias)
├─ src/utils/phase5_time_and_greeks_gate.py (time + safety)
├─ src/utils/phase5_eligibility_and_selector.py (5 gates + striker)
└─ src/utils/phase5_market_bias_engine.py (orchestrator)

Tests:
└─ scripts/phase5_market_bias_engine_test.py (19 tests)

Docs:
├─ PHASE5_COMPLETION_REPORT.md (detailed)
└─ PHASE5_QUICK_REFERENCE.md (this file)
```

---

## Next: Phase 6

Phase 6 Entry/Exit Engine will:
- Receive ExecutionSignal from Phase 5
- Generate precise entry levels
- Manage position lifecycle
- Implement risk controls

---

*Angel-X Phase 5 | December 2024*
