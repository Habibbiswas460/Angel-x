# 🧪 Master Test Plan - Quick Reference

## One-Line Summary
**"boring system = professional system" - 9-level progressive testing before live trading**

---

## 🚀 Quick Start

```bash
cd /home/lora/git_clone_projects/Angel-x

# Check progress
python scripts/run_master_test.py --progress

# Run specific test
python scripts/run_master_test.py --test TEST-0

# Run all tests (with confirmations)
python scripts/run_master_test.py --auto
```

---

## 📋 Test Sequence (CANNOT SKIP)

| # | Test | Duration | One-Line Goal |
|---|------|----------|---------------|
| 0 | Safety | 5 min | Verify DEMO_MODE, no orders |
| 1 | Data Health | 1-2 days | 70%+ NO TRADE, zero stale trades |
| 2 | Signal Flood | 1 day | 100 signals → 10-15 trades |
| 3 | Entry Quality | 2-3 days | 70-80% block rate |
| 4 | Adaptive Veto | 3-5 days | 30% adaptive blocks |
| 5 | Risk Manager | 2-3 days | Zero trades after limit |
| 6 | SL Failure | 1 day | Force exit on SL fail |
| 7 | Shadow-Live | 5-7 days | Real decisions, no execution |
| 8 | Micro Live | 5-10 days | 1 trade/day, smallest qty |

**Total: 3-4 weeks**

---

## 🏆 Golden Rules (ALL MUST BE YES)

Before TEST-8 (live trading):

```
1. SL কখনো skip হয়নি?           → YES ✅
2. Loss এর পর bot চুপ ছিল?       → YES ✅
3. Chop day-এ trade কম?          → YES ✅
4. তুমি mentally শান্ত?          → YES ✅
```

**One NO → STOP immediately**

---

## ⚠️ Critical Rules

1. **Cannot skip test levels** - Must complete in order
2. **Each test must PASS** - No moving forward on FAIL
3. **DEMO_MODE until TEST-8** - No live trading before
4. **Golden Rules mandatory** - All YES before live

---

## 🎯 Key Philosophy

```
বেশি trade = ভালো না
Calm day = Successful day
ধৈর্য + নিয়ম = লাভ
```

**Many "NO TRADE" logs = System working correctly ✅**

---

## 📊 What Success Looks Like

### TEST-1 Success
```
LTP availability: 95%
NO TRADE: 72% of time
Stale data trades: 0
→ ✅ PASS
```

### TEST-2 Success
```
Signals: 100
Trades: 12
Block rate: 88%
Neutral bias trades: 0
→ ✅ PASS
```

### TEST-8 Success
```
Day 1: 1 trade, +₹500, SL placed ✅
Day 2: 1 trade, -₹200, SL hit, cooldown ✅
Day 3: 0 trades (in cooldown) ✅
Day 4: 1 trade, +₹300, SL placed ✅
Day 5: 1 trade, +₹400, SL placed ✅
→ ✅ PASS - Can scale up
```

---

## 🚨 What Failure Looks Like

### TEST-1 Failure
```
Stale data trades: 3
→ ❌ FAIL - Bot trading on bad data
```

### TEST-2 Failure
```
Signals: 100
Trades: 85
→ ❌ FAIL - No filtering, over-trading
```

### TEST-8 Failure
```
Day 1: 5 trades
→ ❌ FAIL - Max 1 trade/day rule broken
→ STOP immediately, go back to TEST-7
```

---

## 📝 Files Created

```
config/test_config.py              # Test configurations
scripts/test_0_safety_setup.py     # TEST-0 runner
scripts/test_1_data_health.py      # TEST-1 runner
scripts/test_2_signal_flood.py     # TEST-2 runner
scripts/run_master_test.py         # Master orchestrator
docs/MASTER_TEST_PLAN.md           # Full documentation
```

---

## 💡 Remember

- **Boring = Professional** (Institutional traders don't chase)
- **Patience = Profit** (Wait for clean setups)
- **Rules = Safety** (Every rule has a reason)
- **NO TRADE = Success** (Protecting capital is winning)

---

**Made with 🔥 by Habib**
