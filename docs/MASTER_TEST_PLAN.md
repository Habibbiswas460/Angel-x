# 🧪 ANGEL-X MASTER TEST PLAN

**ALL TEST MODE** - "boring system = professional system"

---

## 🎯 Philosophy

```
বেশি trade = ভালো না
calm day = successful day  
ধৈর্য + নিয়ম = লাভ
```

**⚠️ CRITICAL RULE**: Cannot skip test levels. Each must PASS before next.

---

## 📋 Test Levels Overview

| Level | Name | Duration | Focus | Can Skip? |
|-------|------|----------|-------|-----------|
| TEST-0 | Pre-Test Safety | 1 hour | Configuration validation | ❌ NO |
| TEST-1 | Data & Health | 1-2 days | Data quality, stability | ❌ NO |
| TEST-2 | Signal Flood | 1 day | Signal filtering | ❌ NO |
| TEST-3 | Entry Quality | 2-3 days | Quality gates | ❌ NO |
| TEST-4 | Adaptive Veto | 3-5 days | Adaptive blocking | ❌ NO |
| TEST-5 | Risk Manager | 2-3 days | Risk enforcement | ❌ NO |
| TEST-6 | SL Failure | 1 day | Stop-loss behavior | ❌ NO |
| TEST-7 | Shadow-Live | 5-7 days | Real decisions, no execution | ❌ NO |
| TEST-8 | Micro Live | 5-10 days | Live with 1 trade/day | ❌ NO |

**Total Testing Timeline**: 3-4 weeks minimum

---

## 🟥 TEST-0: Pre-Test Safety Setup

**Mandatory first step before ANY testing**

### Configuration

```python
DEMO_MODE = True              # Bot thinks, doesn't execute
ORDER_PLACEMENT = False       # No orders to broker
REAL_MARKET_DATA = True       # Use real market data
LOG_ALL_DECISIONS = True      # Log everything
REQUIRE_HEALTH_CHECK = True   # Data health mandatory
BLOCK_IF_STALE_DATA = True    # No trades on stale data
```

### Pass Criteria

✅ All safety gates enabled  
✅ DEMO_MODE confirmed  
✅ ORDER_PLACEMENT disabled  
✅ Logging enabled  

### Fail Criteria

❌ Any safety gate disabled  
❌ ORDER_PLACEMENT enabled  

### Running

```bash
cd /home/lora/git_clone_projects/Angel-x
python scripts/run_master_test.py --test TEST-0
```

### Expected Output

```
✅ TEST-0 PASSED: Safe to proceed to TEST-1
```

### What Bot Does

- ✅ Analyzes market
- ✅ Makes decisions
- ✅ Logs everything
- ❌ Places NO orders

### Duration

~5 minutes (configuration check)

---

## 🟦 TEST-1: Data & Health Test

**Verify data quality and system stability**

### Configuration

```python
MIN_NO_TRADE_PERCENTAGE = 70   # Expect 70%+ NO TRADE
MAX_STALE_DATA_TRADES = 0      # Zero trades on stale data
LTP_STALE_THRESHOLD = 5        # 5 seconds
GREEKS_STALE_THRESHOLD = 10    # 10 seconds
```

### What to Look For

**✅ PASS if you see:**
- Many "NO TRADE" logs (70%+ of time)
- "HALT" when data stale
- Bot doesn't panic on errors
- WebSocket recovers automatically

**❌ FAIL if:**
- Trades on stale data
- Bot panics on errors
- Continuous crashes

### Monitoring

```bash
# Run in background
python main.py &

# Monitor logs
tail -f logs/strategy_*.log | grep "NO TRADE\|HALT\|STALE"
```

### Metrics to Track

| Metric | Target | Critical? |
|--------|--------|-----------|
| LTP availability | 90%+ | ✅ YES |
| Greeks availability | 90%+ | ✅ YES |
| NO TRADE percentage | 70%+ | ✅ YES |
| Trades on stale data | 0 | ✅ YES |
| Panic events | 0 | ✅ YES |
| WebSocket recovery | All drops recovered | ⚠️ IMPORTANT |

### Running

```bash
python scripts/run_master_test.py --test TEST-1
```

### Duration

1-2 days of continuous operation

---

## 🟨 TEST-2: Signal Flood Test

**Run on a choppy/sideways day**

### The Trap

```
Signal তো আসবেই। 
কিন্তু trade করা উচিত না।
```

### Configuration

```python
MAX_TRADE_TO_SIGNAL_RATIO = 0.2    # Max 20% signals → trades
MAX_TRADES_ON_CHOP_DAY = 2         # Max 2 trades on choppy day
MIN_NEUTRAL_BIAS_TIME = 60         # 60% time bias should be neutral
```

### What to Look For

**✅ PASS if:**
- 100 signals → 10-15 trades (10-15%)
- Neutral bias → block
- Choppy market → minimal trades
- High block rate (70%+)

**❌ FAIL if:**
- All signals → trades
- Ignores bias
- Trades heavily on choppy day

### Expected Behavior

```
Signal: BULLISH breakout detected
Bias: NEUTRAL
Decision: ⛔ BLOCKED (Bias neutral)

Signal: BEARISH breakdown detected  
Market: CHOPPY
Decision: ⛔ BLOCKED (Market choppy)

Signal: BULLISH confirmation
Bias: BULLISH
Quality: Low (chop)
Decision: ⛔ BLOCKED (Quality gate failed)
```

### Metrics

| Metric | Target | Critical? |
|--------|--------|-----------|
| Signal→Trade ratio | ≤20% | ✅ YES |
| Trades on neutral bias | ≤2 | ✅ YES |
| Trades on chop day | ≤2 | ✅ YES |
| Block rate | ≥70% | ✅ YES |

### Running

```bash
# Pick a choppy/sideways day
python scripts/run_master_test.py --test TEST-2
```

### Duration

1 full choppy trading day

---

## 🟩 TEST-3: Entry Quality Test

**Validate quality gate system**

### Configuration

```python
MIN_BLOCK_RATE = 70               # 70-80% should be blocked
ALLOW_ONLY_CLEAN_SETUPS = True    # Only clean patterns
REQUIRE_CONFIRMATION = True        # Multi-factor confirmation
```

### What to Look For

**✅ PASS if:**
- 70-80% entries blocked
- Only clean setups taken
- Multi-factor confirmation working
- "Quality gate failed" frequent

**❌ FAIL if:**
- Low block rate (<50%)
- Messy setups taken
- Single-factor entries

### Expected Behavior

```
Entry Quality Check:
   Pattern: Clean ✅
   Volume: Good ✅
   Greeks: Healthy ✅
   Bias: Aligned ✅
   Adaptive: Confident ✅
→ Decision: ✅ ENTRY ALLOWED

Entry Quality Check:
   Pattern: Messy ❌
→ Decision: ⛔ BLOCKED (Quality gate failed)
```

### Running

```bash
python scripts/run_master_test.py --test TEST-3
```

### Duration

2-3 days

---

## 🟪 TEST-4: Adaptive Veto Test

**Validate adaptive learning system**

### Configuration

```python
ADAPTIVE_BLOCK_PERCENTAGE = 30     # 30% blocks from adaptive
MIN_CONFIDENCE_FOR_TRADE = 0.6     # 60% confidence minimum
REGIME_DETECTION_ENABLED = True    # Detect regime changes
```

### What to Look For

**✅ PASS if:**
- ~30% blocks from adaptive system
- Low confidence → block
- Regime detection working
- Adapts to changing conditions

**❌ FAIL if:**
- Adaptive not blocking
- Ignores confidence scores
- No regime awareness

### Metrics

| Metric | Target | Critical? |
|--------|--------|-----------|
| Adaptive block % | 25-35% | ✅ YES |
| Min confidence respected | 100% | ✅ YES |
| Regime detection events | Multiple | ⚠️ IMPORTANT |

### Running

```bash
python scripts/run_master_test.py --test TEST-4
```

### Duration

3-5 days

---

## 🟥 TEST-5: Risk Manager Test

**Validate risk limits and circuit breakers**

### Configuration

```python
MAX_DAILY_LOSS = -500              # ₹500 max daily loss
CONSECUTIVE_LOSS_LIMIT = 2         # Max 2 consecutive losses
COOLDOWN_MINUTES = 15              # 15 min cooldown after 2 losses
MAX_POSITION_SIZE = 25             # Max 25 lots
```

### What to Look For

**✅ PASS if:**
- ZERO trades after daily loss limit hit
- ZERO trades during cooldown
- Position size respected
- Risk manager never disabled

**❌ FAIL if:**
- Trades after loss limit
- Revenge trading (no cooldown)
- Oversized positions

### Expected Behavior

```
Trade 1: Loss -200
Trade 2: Loss -150
→ Consecutive losses: 2
→ Status: ⏸️ COOLDOWN (15 min)

[15 minutes later]
→ Status: ✅ COOLDOWN ENDED
→ Next signal: Allowed

Daily loss: -550
→ Status: ⛔ DAILY LIMIT HIT
→ Remaining: ZERO TRADES today
```

### Running

```bash
python scripts/run_master_test.py --test TEST-5
```

### Duration

2-3 days (need losing scenarios)

---

## 🟧 TEST-6: SL Failure Simulation

**Test stop-loss failure behavior**

### Configuration

```python
FORCE_EXIT_ON_SL_FAIL = True       # Force exit if SL fails
ZERO_NAKED_POSITIONS = True        # No naked positions allowed
MAX_DRAWDOWN_PERCENT = 5           # 5% max drawdown
```

### What to Look For

**✅ PASS if:**
- Force exits immediately on SL fail
- Zero naked positions
- Drawdown limit respected
- No panic, clean exit

**❌ FAIL if:**
- Naked positions after SL fail
- Drawdown exceeded
- No exit action taken

### Simulation Scenarios

1. **SL slippage**: SL at 100, fills at 95
2. **SL rejection**: SL order rejected by broker
3. **Gap down**: Market gaps through SL

### Expected Behavior

```
SL Order Status: REJECTED
→ Action: 🚨 FORCE MARKET EXIT
→ Exit Price: 94.50 (slippage)
→ Position: CLOSED
→ Status: ✅ SAFE
```

### Running

```bash
python scripts/run_master_test.py --test TEST-6
```

### Duration

1 day (simulated scenarios)

---

## 🟦 TEST-7: Shadow-Live Test

**Real decisions, NO execution**

### Configuration

```python
EXECUTION_ENABLED = False          # No real orders
LOG_WOULD_HAVE_TRADED = True       # Log would-be trades
TRACK_SHADOW_PNL = True            # Track theoretical PnL
```

### What to Look For

**✅ PASS if:**
- All decisions logged clearly
- Would-be PnL tracked
- No emotional behavior
- Mental state calm

**❌ FAIL if:**
- Unclear decisions
- Emotional patterns detected
- Mental stress observed

### Expected Logs

```
10:15:30 - SIGNAL: BULLISH breakout
10:15:31 - QUALITY: Clean setup ✅
10:15:32 - ADAPTIVE: Confident (0.72) ✅
10:15:33 - BIAS: Aligned ✅
10:15:34 - RISK: Within limits ✅
10:15:35 - DECISION: ✅ WOULD HAVE TRADED
10:15:36 - Entry: 20000 CE @ ₹150
10:15:37 - Qty: 25 lots
10:15:38 - SL: ₹140 | Target: ₹165
10:15:39 - Shadow Trade ID: ST-001

[Later]
11:30:00 - Shadow Exit: ₹162
11:30:01 - Shadow PnL: +₹7,500
11:30:02 - Mental State: 😌 Calm
```

### Metrics

| Metric | Target | Critical? |
|--------|--------|-----------|
| Decision clarity | 100% | ✅ YES |
| Emotional events | 0 | ✅ YES |
| Mental state | Calm | ✅ YES |

### Running

```bash
python scripts/run_master_test.py --test TEST-7
```

### Duration

5-7 days

---

## 🟩 TEST-8: Micro Live

**LIVE TRADING - Smallest possible**

### ⚠️ GOLDEN RULES CHECK (ALL MUST BE YES)

```
1. SL কখনো skip হয়নি?           → YES ✅
2. Loss এর পর bot চুপ ছিল?       → YES ✅
3. Chop day-এ trade কম?          → YES ✅
4. তুমি mentally শান্ত?          → YES ✅
```

**One NO → STOP immediately. Do NOT proceed to live.**

### Configuration

```python
EXECUTION_ENABLED = True           # LIVE TRADING
MAX_TRADES_PER_DAY = 1            # Only 1 trade/day
POSITION_SIZE = 1                 # Smallest qty (1 lot)
MIN_TEST_DAYS = 5                 # Minimum 5 days
```

### What to Look For

**✅ PASS if:**
- Max 1 trade/day respected
- Smallest position size
- All rules followed
- Execution quality good
- SL respected 100%

**❌ FAIL if:**
- Multiple trades in one day
- Larger position size
- SL skipped even once
- Emotional behavior

### Daily Checklist

```
□ Only 1 trade today?
□ Smallest qty used?
□ SL placed immediately?
□ Exit clean?
□ Mentally calm?
```

### Running

```bash
# ONLY after Golden Rules all YES
python scripts/run_master_test.py --test TEST-8
```

### Duration

Minimum 5-10 days

### Graduation Criteria

After 5-10 days of successful micro live:
- Zero SL skips ✅
- Zero revenge trades ✅
- Consistent execution ✅
- Mental calm maintained ✅
- All rules followed ✅

**Then and only then** → Scale up gradually

---

## 🏆 Golden Rules Validator

### Automated Checks

```bash
python scripts/validate_golden_rules.py
```

### Manual Self-Assessment

Ask yourself honestly:

1. **SL কখনো skip হয়নি?**
   - Check: Did bot ALWAYS place SL?
   - Check: Did SL ALWAYS get filled (or force exit)?
   - Check: Zero naked positions ever?
   
2. **Loss এর পর bot চুপ ছিল?**
   - Check: Cooldown enforced?
   - Check: Zero revenge trading?
   - Check: Gap between consecutive losses?
   
3. **Chop day-এ trade কম?**
   - Check: Choppy days logged?
   - Check: ≤2 trades on chop days?
   - Check: High block rate maintained?
   
4. **তুমি mentally শান্ত?**
   - Check: Can sleep peacefully?
   - Check: No constant chart checking?
   - Check: Trust the system?

**ALL must be YES. One NO = STOP.**

---

## 📊 Test Progression Tracking

```bash
# Show current progress
python scripts/run_master_test.py --progress
```

**Output:**
```
🧪 ANGEL-X MASTER TEST PLAN

Test Progression:
   ✅ TEST-0: Pre-Test Safety (COMPLETED)
   ✅ TEST-1: Data & Health (COMPLETED)
   ⏳ TEST-2: Signal Flood (IN PROGRESS)
   ⬜ TEST-3: Entry Quality
   ⬜ TEST-4: Adaptive Veto
   ⬜ TEST-5: Risk Manager
   ⬜ TEST-6: SL Failure
   ⬜ TEST-7: Shadow-Live
   ⬜ TEST-8: Micro Live

🏆 Golden Rules Status:
   SL কখনো skip হয়নি? → Not checked
   Loss এর পর bot চুপ ছিল? → Not checked
   Chop day-এ trade কম? → Not checked
   তুমি mentally শান্ত? → Not checked

⚠️ Complete all tests and validate Golden Rules before TEST-8
```

---

## 🚀 Quick Start

### 1. Run All Tests (Recommended)

```bash
cd /home/lora/git_clone_projects/Angel-x
python scripts/run_master_test.py --auto
```

This will run all tests in sequence with confirmations between each.

### 2. Run Specific Test

```bash
python scripts/run_master_test.py --test TEST-0
python scripts/run_master_test.py --test TEST-1
# etc...
```

### 3. Check Progress

```bash
python scripts/run_master_test.py --progress
```

---

## ⚠️ Important Reminders

### DO NOT:
- ❌ Skip test levels
- ❌ Rush through tests
- ❌ Disable safety gates
- ❌ Go live without Golden Rules

### DO:
- ✅ Follow test order strictly
- ✅ Wait for PASS before next level
- ✅ Monitor logs continuously
- ✅ Be patient
- ✅ Trust the process

---

## 📝 Test Logs Location

```
logs/
├── test_0_*.log          # Pre-test safety
├── test_1_*.log          # Data health
├── test_2_*.log          # Signal flood
├── test_3_*.log          # Entry quality
├── test_4_*.log          # Adaptive veto
├── test_5_*.log          # Risk manager
├── test_6_*.log          # SL failure
├── test_7_*.log          # Shadow-live
├── test_8_*.log          # Micro live
└── golden_rules_*.log    # Golden Rules validation
```

---

## 🎯 Success Metrics

### Overall Test Suite Success

- All 9 test levels passed ✅
- Golden Rules all YES ✅
- 5-10 days micro live successful ✅
- Mental state calm ✅
- Trust in system ✅

**Then:** Ready for gradual scale-up

---

## 💡 Philosophy Reminder

```
"boring system = professional system"
"বেশি trade = ভালো না"  
"calm day = successful day"
"ধৈর্য + নিয়ম = লাভ"
```

**Institutional traders are BORING. That's why they win.**

---

## 📞 Support

If stuck on any test level:
1. Check logs for errors
2. Review test criteria
3. Run with `--progress` to see status
4. Be patient, don't skip

**Remember:** Each NO TRADE log = system working correctly ✅

---

**Made with 🔥 by Habib**
