# ANGEL-X Phase 8 Implementation Complete
**Advanced Greeks + ML Foundation + Institutional Position Sizing**

## Implementation Date: January 8, 2026

---

## ✅ Completed Features

### 1. Greeks-Based Smart Exit Engine
**File**: `src/engines/smart_exit_engine.py`

**New Exit Triggers**:
- ✓ **Delta Weakness**: Exit when delta declines >15% from entry
- ✓ **Gamma Rollover**: Exit when gamma drops to 80% of entry (Greeks peak)
- ✓ **IV Crush**: Exit when IV drops >5% while price stalls
- ✓ **Expiry Rush**: Auto-exit 5 minutes before expiry
- ✓ **Trailing Stops**: Dynamic trailing stop at 2% of peak
- ✓ **Profit Laddering**: Partial exits at 1%, 2%, 3% profit

**Key Methods**:
```python
check_exit_conditions(
    trade_id, current_price, current_delta, current_gamma,
    current_theta, current_iv, entry_price, entry_delta,
    entry_gamma, entry_iv, sl_price, target_price,
    entry_time, time_to_expiry_minutes, quantity, exited_qty
) -> Optional[ExitSnapshot]
```

**Config Settings**:
- `USE_SMART_EXIT_ENGINE = True`
- `USE_TRAILING_STOP = True`
- `TRAILING_STOP_PERCENT = 2.0`
- `USE_PROFIT_LADDER = True`

---

### 2. Backtesting Framework
**File**: `src/backtesting/backtest_engine.py`

**Features**:
- ✓ Historical data loader (CSV/Database/API)
- ✓ Tick-by-tick simulation
- ✓ Realistic slippage & brokerage costs
- ✓ Performance metrics calculation
- ✓ Equity curve tracking
- ✓ Sharpe ratio, drawdown, profit factor

**Usage**:
```python
from src.backtesting.backtest_engine import BacktestEngine, BacktestConfig
from datetime import datetime

config = BacktestConfig(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    initial_capital=100000
)

engine = BacktestEngine(config)
result = engine.run(strategy)

print(f"Win Rate: {result.win_rate:.1f}%")
print(f"Total P&L: ₹{result.total_pnl:,.2f}")
print(f"Profit Factor: {result.profit_factor:.2f}")
```

**Config Settings**:
- `BACKTESTING_ENABLED = False`
- `BACKTEST_DATA_DIR = "./backtests/data"`
- `BACKTEST_SLIPPAGE_PERCENT = 0.05`

---

### 3. Multi-Strike Auto Selection Engine
**File**: `src/engines/portfolio/multi_strike_engine.py`

**Features**:
- ✓ **Auto CE/PE selection** based on market bias
- ✓ **ATM ± 3 strikes scanning** (OTM/ITM)
- ✓ **Greeks + IV scoring** for best strikes
- ✓ Portfolio balancing (delta-neutral, gamma scalping)

**Strike Scoring Algorithm**:
```
Score = Delta_Score (40 pts) + Gamma_Score (30 pts) + IV_Score (30 pts)

Delta Score: Higher delta = more responsive (0-40)
Gamma Score: Higher gamma = better scalping (0-30)
IV Score: Optimal 20-30% IV (0-30)
```

**Key Methods**:
```python
# Auto CE/PE selection
option_type = engine.auto_select_option_type(bias='bullish', confidence=75)

# Scan strikes
candidates = engine.scan_strike_ladder(
    atm_strike=23500,
    option_type='CE',
    greeks_manager=greeks_manager
)

# Build multi-strike plan
legs = engine.build_multi_strike_plan(
    bias='bullish',
    confidence=80,
    atm_strike=23500,
    greeks_manager=greeks_manager,
    max_legs=3
)
```

**Config Settings**:
- `USE_MULTI_STRIKE = False`
- `MULTI_STRIKE_RANGE = 3`
- `MULTI_STRIKE_MIN_DELTA = 0.20`
- `MULTI_STRIKE_MIN_GAMMA = 0.001`
- `MULTI_STRIKE_MIN_IV = 15.0`

---

### 4. Dynamic Institutional Position Sizing
**File**: `src/core/position_sizing.py`

**Features**:
- ✓ **Kelly Criterion** for optimal bet sizing
- ✓ **Greeks-based probability estimation**
- ✓ **IV edge detection**
- ✓ **High-probability auto-scaling**

**Win Probability Factors**:
```
Base Probability: 50%

Delta Factor: +15% (delta > 0.40)
Gamma Factor: +10% (gamma > 0.01)
IV Edge: +10% (IV 15-25% sweet spot)
Bias Confidence: +10% (high confidence)
OI Confirmation: +5% (rising OI)

Final Probability: 30-80% (clamped for safety)
```

**Kelly Criterion**:
```
Kelly% = (p*b - q) / b
Adjusted = Kelly% × 0.25 (quarter Kelly)
Clamped = max(0%, min(20%, Adjusted))
```

**Usage**:
```python
position = position_sizing.calculate_position_size(
    entry_price=150,
    hard_sl_price=140,
    target_price=165,
    delta=0.45,
    gamma=0.008,
    iv=22.5,
    bias_confidence=75,
    oi_change=500
)

print(f"Quantity: {position.quantity}")
print(f"Win Probability: {position.win_probability:.1%}")
print(f"Kelly Fraction: {position.kelly_fraction:.2%}")
```

**Config Settings**:
- `USE_KELLY_CRITERION = False`
- `KELLY_FRACTION = 0.25`
- `USE_PROBABILITY_WEIGHTING = True`

---

### 5. Advanced Greeks Exposure Limits
**File**: `src/core/risk_manager.py`

**Features**:
- ✓ **Portfolio-level Greeks tracking**
- ✓ **Delta/Gamma/Theta/Vega limits**
- ✓ **Auto-hedging triggers**
- ✓ **Real-time exposure monitoring**

**Limits**:
```
Max Net Delta: ±100
Max Gross Delta: 200
Max Net Gamma: 5.0
Max Gross Gamma: 10.0
Max Daily Theta: -₹500/day
Max Net Vega: 1000

Auto-Hedge Triggers:
- Delta ≥ 80 → Hedge required
- Gamma ≥ 4.0 → Hedge required
```

**Usage**:
```python
# Update portfolio Greeks
risk_manager.update_portfolio_greeks(
    net_delta=75.5,
    net_gamma=3.2,
    net_theta=-350,
    net_vega=800,
    gross_delta=120
)

# Check Greeks exposure
greeks = risk_manager.get_portfolio_greeks()
print(f"Delta Utilization: {greeks['delta_utilization']:.1f}%")
print(f"Needs Hedge: {greeks['needs_hedge']}")

# Check trade with Greeks limits
allowed, reason = risk_manager.can_take_trade(
    trade_info={'quantity': 75},
    position_delta=25.5,
    position_gamma=1.2,
    position_theta=-100
)
```

**Config Settings**:
- `MAX_NET_DELTA = 100.0`
- `MAX_GROSS_DELTA = 200.0`
- `MAX_NET_GAMMA = 5.0`
- `DELTA_HEDGE_TRIGGER = 80.0`
- `GAMMA_HEDGE_TRIGGER = 4.0`

---

### 6. PostgreSQL Database Layer for ML
**File**: `src/database/ml_database.py`

**Features**:
- ✓ **Market ticks table** (LTP, volume, bid/ask)
- ✓ **Greeks snapshots table** (complete Greeks history)
- ✓ **Trades table** (entry/exit lifecycle)
- ✓ **Bias history table** (market state changes)
- ✓ **OI changes table** (smart money tracking)
- ✓ **ML features table** (derived features for training)
- ✓ **Batch inserts** for performance
- ✓ **Query helpers** for ML dataset extraction

**Schema Tables**:
```sql
market_ticks: timestamp, symbol, ltp, bid, ask, volume, oi
greeks_snapshots: timestamp, symbol, strike, delta, gamma, theta, vega, iv, oi
trades: entry/exit data, Greeks evolution, P&L, holding time
bias_history: bias changes over time
oi_changes: OI delta tracking
ml_features: JSON feature storage for training
```

**Usage**:
```python
from src.database import get_ml_database, DatabaseConfig

# Initialize database
db_config = DatabaseConfig(
    host="localhost",
    database="angelx_ml",
    user="angelx",
    password="your_password"
)

db = get_ml_database(db_config)

# Insert market tick
db.insert_market_tick(
    timestamp=datetime.now(),
    symbol="NIFTY23500CE",
    ltp=150.50,
    bid=150.25,
    ask=150.75,
    volume=1000,
    oi=50000
)

# Insert Greeks snapshot
db.insert_greeks_snapshot(
    timestamp=datetime.now(),
    symbol="NIFTY23500CE",
    underlying="NIFTY",
    strike=23500,
    option_type="CE",
    expiry_date="2026-01-13",
    ltp=150.50,
    delta=0.45,
    gamma=0.008,
    theta=-0.03,
    vega=0.15,
    iv=22.5,
    oi=50000,
    volume=1000
)

# Query ML dataset
dataset = db.query_ml_dataset(
    start_date=datetime(2025, 1, 1),
    end_date=datetime(2025, 12, 31),
    underlying='NIFTY'
)

# Flush all pending data
db.flush_all()
```

**Config Settings**:
- `DATABASE_ENABLED = False`
- `DATABASE_HOST = "localhost"`
- `DATABASE_NAME = "angelx_ml"`
- `DATABASE_BATCH_SIZE = 100`

**Setup PostgreSQL**:
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Create database
sudo -u postgres createdb angelx_ml
sudo -u postgres createuser angelx

# Install Python driver
pip install psycopg2-binary

# Enable in config
DATABASE_ENABLED = True
```

---

## 🎯 Integration Points

### Main Strategy Integration
All new features are integrated into `main.py`:

```python
# Smart exit engine (via integration hub)
integration.smart_exit.check_exit_conditions(...)

# Multi-strike selection
legs = multi_strike_engine.build_multi_strike_plan(
    bias=bias_state.value,
    confidence=bias_confidence,
    atm_strike=atm_strike,
    greeks_manager=greeks_manager
)

# Dynamic position sizing
position = position_sizing.calculate_position_size(
    entry_price=entry_price,
    hard_sl_price=sl_price,
    target_price=target_price,
    delta=current_delta,
    gamma=current_gamma,
    iv=current_iv,
    bias_confidence=bias_confidence
)

# Risk manager Greeks check
allowed, reason = risk_manager.can_take_trade(
    trade_info={'quantity': qty},
    position_delta=delta,
    position_gamma=gamma,
    position_theta=theta
)

# Database logging
if db.enabled:
    db.insert_greeks_snapshot(...)
    db.insert_trade(trade_data)
```

---

## 📊 Performance Improvements

1. **Exit Accuracy**: Greeks-based exits catch moves earlier (delta/gamma signals)
2. **Position Sizing**: Kelly + probability weighting optimizes risk/reward
3. **Strike Selection**: Automated scoring finds best Greeks/IV combinations
4. **Risk Management**: Portfolio Greeks limits prevent overexposure
5. **ML Foundation**: Complete data pipeline for future ML models

---

## 🚀 Next Steps

### To Enable Features:

1. **Smart Exit Engine**:
   ```python
   USE_SMART_EXIT_ENGINE = True
   USE_TRAILING_STOP = True
   USE_PROFIT_LADDER = True
   ```

2. **Multi-Strike Selection**:
   ```python
   USE_MULTI_STRIKE = True
   MULTI_STRIKE_RANGE = 3
   ```

3. **Dynamic Position Sizing**:
   ```python
   USE_KELLY_CRITERION = True
   USE_PROBABILITY_WEIGHTING = True
   ```

4. **Database Layer**:
   ```bash
   # Setup PostgreSQL first
   pip install psycopg2-binary
   ```
   ```python
   DATABASE_ENABLED = True
   ```

### Future ML Integration:

```python
# Query training dataset
dataset = db.query_ml_dataset(start_date, end_date)

# Train model
from sklearn.ensemble import RandomForestClassifier
X = extract_features(dataset)
y = extract_labels(dataset)
model.fit(X, y)

# Use model for predictions
win_prob = model.predict_proba(current_features)
```

---

## 📝 Testing Commands

```bash
# Restart strategy with new features
PYTHONPATH=. .venv/bin/python main.py

# Access dashboard
http://localhost:5000/dashboard

# Check API endpoints
curl http://localhost:5000/api/dashboard
curl http://localhost:5000/api/positions
curl http://localhost:5000/api/greeks-heatmap
```

---

## 🎓 Key Learnings

1. **Greeks lead, price confirms** - Exit when Greeks degrade, not when price falls
2. **Kelly Criterion** - Optimal bet sizing based on edge
3. **Probability estimation** - Greeks + IV reveal true win probability
4. **Portfolio Greeks** - Track exposure across all positions
5. **ML foundation** - Structured data enables future AI improvements

---

## ✨ Status: All Phase 8 Features COMPLETE ✨

**Strategy is running on http://localhost:5000**

Dashboard live with real-time Greeks, positions, and portfolio metrics!
