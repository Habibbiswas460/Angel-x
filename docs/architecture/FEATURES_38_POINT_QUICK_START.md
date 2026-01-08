# 🚀 ANGEL-X 38-Point Feature Integration Quick Start

## Phase 1: Quick Wins (1-2 days) ✅

### ✓ Completed
1. **Live WebSocket Data Feed** - REST polling with WS fallback ready
2. **Alert System** - Telegram-ready (console tested)
3. **Enhanced Trade Journal** - With greeks snapshot and exit reasons
4. **Smart Exit Engine** - Trailing stops + profit laddering

### 🚀 Just Added
1. **Real-Time Web Dashboard**
   - Live positions, Greeks, P&L
   - Portfolio Greeks aggregation
   - Performance metrics
   - Recent trades view

2. **Trade Journal Analytics**
   - Entry reason win-rate analysis
   - Exit reason profitability analysis
   - Time-of-day analysis
   - Greeks correlation analysis
   - Comprehensive reports

3. **Smart Exit Engine (Advanced)**
   - Trailing stop losses
   - Profit ladder partial exits
   - Delta weakness detection
   - Gamma rollover exits
   - IV crush exits
   - Expiry rush protection

4. **Integration Hub**
   - Central component management
   - Unified initialization
   - Dashboard sync
   - Analytics reporting

---

## 🎯 Running the Full System

### 1. Enable New Features in config.py
```python
# Dashboard
DASHBOARD_ENABLED = True
DASHBOARD_PORT = 5000

# Smart Exits
USE_SMART_EXIT_ENGINE = True
USE_TRAILING_STOP = True
TRAILING_STOP_PERCENT = 2.0
USE_PROFIT_LADDER = True

# Analytics
TRADE_JOURNAL_ENABLED = True
EXPORT_ANALYTICS_ON_STOP = True
```

### 2. Start the Strategy
```bash
cd /home/lora/git_clone_projects/Angel-x
set -a && source .env && set +a
PYTHONPATH=. .venv/bin/python main.py
```

### 3. Open Dashboard (in browser)
```
http://localhost:5000
```

The dashboard will show:
- **Live Positions** with Greeks
- **Portfolio Greeks** (Δ, Γ, Θ, ν)
- **Risk Usage Meter**
- **Daily P&L**
- **Session Performance**
- **Recent Closed Trades**

---

## 📊 Smart Exit Engine Features

### Trailing Stop Loss
```python
USE_TRAILING_STOP = True
TRAILING_STOP_PERCENT = 2.0  # Trail by 2% of peak

# Example:
# Entry @ ₹100, Peak @ ₹105
# Trail = 105 * 0.02 = ₹2.10
# Exit trigger @ ₹102.90
```

### Profit Ladder (Partial Exits)
```python
USE_PROFIT_LADDER = True
PROFIT_LADDER_RUNGS = [
    (1.0, 0.25),   # 25% qty at 1% profit
    (2.0, 0.50),   # 50% qty at 2% profit
    (3.0, 0.25),   # 25% qty at 3% profit
]

# Example:
# Entry: 50 qty @ ₹100
# At ₹101: Exit 12.5 qty (25%)
# At ₹102: Exit 25 qty (50%)
# At ₹103: Exit 12.5 qty (25%)
```

### Greeks-Based Exits
```python
# Delta Weakness - Exit if delta drops 15%
# Entry Delta: 0.50 → Exit if drops to 0.425

# Gamma Rollover - Exit if gamma falls to 80% of entry
# Entry Gamma: 0.005 → Exit if drops to 0.004

# IV Crush - Exit if IV drops >5%
# Entry IV: 25 → Exit if drops to <23.75
```

---

## 📈 Trade Journal Analytics

### View Analytics After Trading Session
```python
from src.analytics.trade_journal_analytics import TradeJournalAnalytics

analytics = TradeJournalAnalytics("./journal")

# Summary stats
summary = analytics.get_summary_report()
print(summary)

# Entry analysis - which entry reasons work best?
entry_stats = analytics.get_entry_analysis()

# Exit analysis - which exits are most profitable?
exit_stats = analytics.get_exit_analysis()

# Time of day - when to trade?
time_analysis = analytics.get_time_analysis()

# Greeks correlation
greeks_corr = analytics.get_greeks_correlation()

# Export comprehensive report
report_file = analytics.export_analytics_report()
```

---

## 🌐 Dashboard API Endpoints

All endpoints return JSON:

```bash
# Complete dashboard snapshot
curl http://localhost:5000/api/dashboard

# Active positions only
curl http://localhost:5000/api/positions

# Portfolio Greeks
curl http://localhost:5000/api/portfolio

# Performance metrics
curl http://localhost:5000/api/performance

# Closed trades history (limit 50)
curl "http://localhost:5000/api/trades?limit=50"

# Greeks heatmap
curl "http://localhost:5000/api/greeks-heatmap?underlying=NIFTY"

# Health check
curl http://localhost:5000/health
```

---

## 🔄 Integration Hub Usage

```python
from src.integration_hub import get_integration_hub

# Get the hub
hub = get_integration_hub()

# Update position data from trade manager
hub.update_position_data(trade_manager, greeks_manager)

# Get performance metrics
metrics = hub.get_performance_metrics()
print(metrics)

# Generate analytics report
report_file = hub.get_analytics_report()
print(f"Report: {report_file}")

# Shutdown
hub.shutdown()
```

---

## 📁 New Files Added

1. **src/dashboard/dashboard_backend.py** - Flask API server
2. **src/dashboard/dashboard.html** - Web UI (single page)
3. **src/engines/smart_exit_engine.py** - Advanced exit logic
4. **src/analytics/trade_journal_analytics.py** - Trade analysis
5. **src/integration_hub.py** - Central hub for all components
6. **docs/FEATURE_CONFIG_38_POINT.md** - Configuration reference

---

## 🎯 Next Phase (High Impact - 1 Week)

### Backtesting Framework
```python
# Test strategies on historical data
from src.backtesting.backtest_engine import BacktestEngine

backtest = BacktestEngine(
    start_date="2024-01-01",
    end_date="2024-01-31",
    initial_capital=100000
)

results = backtest.run_strategy(strategy)
# Metrics: Win rate, Sharpe, Max Drawdown, etc.
```

### Greeks Heatmap Visualization
```python
# Visual strike ladder with color-coded Greeks
# Shows call/put chains with delta, gamma, OI changes
```

### Multi-Strike Portfolio
```python
# Trade multiple strikes (hedge strategies)
# ATM + ATM±1 combinations
# Bull call spreads, iron condors, etc.
```

---

## ⚠️ Important Notes

1. **Dashboard port**: Default 5000 (configurable)
2. **Journal location**: `./journal/` directory
3. **Analytics**: Loads trades from JSON files
4. **CORS enabled**: Dashboard accessible from any origin
5. **Thread-safe**: All updates are mutex-protected

---

## 🧪 Quick Test

```bash
# 1. Start strategy with demo mode
PYTHONPATH=. .venv/bin/python main.py

# 2. In another terminal, check dashboard
curl http://localhost:5000/api/dashboard | python -m json.tool

# 3. View analytics
python -c "
from src.analytics.trade_journal_analytics import TradeJournalAnalytics
a = TradeJournalAnalytics()
print(a.get_summary_report())
"
```

---

## 🔍 Troubleshooting

### Dashboard not accessible
```bash
# Check if Flask server is running
lsof -i :5000

# Kill if needed
kill -9 $(lsof -t -i:5000)

# Re-enable in config
DASHBOARD_ENABLED = True
```

### No trade history in analytics
```bash
# Check journal directory
ls -la ./journal/

# Verify journal is logging
grep "log_trade" main.py
```

### Smart exit not triggering
```python
# Enable debug logging
logger.setLevel(logging.DEBUG)

# Check exit engine logs
# Look for "Exit condition met" messages
```

---

**Status:** ✅ Ready for testing
**Last Updated:** January 6, 2026
