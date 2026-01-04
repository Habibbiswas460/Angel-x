# ⚡ PHASE 9 QUICK REFERENCE

**Angel-X Dashboard — "লাইভ দেখাবে, পরে শেখাবে"**

---

## 🚀 Quick Start (3 Commands)

```bash
# 1. Run demo with sample data
python3 scripts/phase9_dashboard_demo.py

# 2. Check created files
cat logs/dashboard_snapshot.json
cat logs/post_trade_analytics.txt

# 3. Done! Dashboard works ✅
```

---

## 📦 Import Cheat Sheet

```python
# Live Dashboard (PART A)
from src.dashboard.live_dashboard import (
    LiveDashboard,
    MarketOverview,
    OptionChainView,
    BiasEligibilityPanel,
    LiveTradeMonitor,
    RiskSafetyPanel,
    MarketStatus,
    TradeAllowance
)

# Post-Trade Analytics (PART B)
from src.dashboard.post_trade_analytics import (
    PostTradeAnalytics,
    PnLAnalytics,
    ExitReasonReport,
    GreeksAccuracyReport,
    OIVolumeConvictionReport,
    TimeOfDayReport,
    CompletedTrade,
    ExitReason
)

# Aggregator
from src.dashboard.dashboard_aggregator import (
    DashboardAggregator,
    DashboardDataFeeder
)
```

---

## ⚡ 5-Minute Setup

### 1. Initialize Dashboard
```python
from src.dashboard.dashboard_aggregator import DashboardAggregator

aggregator = DashboardAggregator()
```

### 2. Load Sample Data (for testing)
```python
from src.dashboard.dashboard_aggregator import DashboardDataFeeder

aggregator.update_market_data(DashboardDataFeeder.get_sample_market_data())
aggregator.update_option_chain(DashboardDataFeeder.get_sample_option_chain())
aggregator.update_active_position(DashboardDataFeeder.get_sample_position())
```

### 3. Refresh & Display
```python
aggregator.refresh_live_dashboard()
print(aggregator.render_live_dashboard())
```

### 4. Check Alerts
```python
has_alerts, alerts = aggregator.check_alerts()
if has_alerts:
    for alert in alerts:
        print(f"🚨 {alert}")
```

### 5. Run Analytics
```python
trades = DashboardDataFeeder.get_sample_completed_trades()
aggregator.load_completed_trades(trades)
report = aggregator.run_post_trade_analysis(period="WEEK")
print(report)
```

---

## 📊 Live Dashboard Components

### Market Overview
```python
overview = aggregator.live_dashboard.market_overview
print(f"NIFTY: {overview.nifty_spot} ({overview.spot_change_pct:+.2f}%)")
print(f"Status: {overview.market_status.value}")
```

### Bias Panel
```python
bias = aggregator.live_dashboard.bias_panel
print(f"Bias: {bias.market_bias} ({bias.get_bias_grade()})")
print(f"Trade Allowed: {bias.trade_allowed.value}")
if not bias.is_tradeable():
    print(f"Blocked: {bias.block_reasons}")
```

### Position Monitor
```python
monitor = aggregator.live_dashboard.trade_monitor
if monitor.has_position:
    print(f"{monitor.symbol} {monitor.strike} {monitor.option_type}")
    print(f"PnL: ₹{monitor.unrealized_pnl:+.2f} ({monitor.pnl_percentage:+.2f}%)")
    print(f"Delta: {monitor.current_delta:.3f}")
```

### Risk Panel
```python
risk = aggregator.live_dashboard.risk_panel
print(f"Trades: {risk.trades_taken_today}/{risk.max_trades_allowed}")
print(f"Daily PnL: ₹{risk.daily_pnl:+,.2f}")
print(f"Status: {risk.get_safety_status()}")
```

### Option Chain
```python
chain = aggregator.live_dashboard.option_chain
dominant = chain.get_dominant_strikes()
print(f"CE Dominant: {dominant['ce_dominant_strikes']}")
print(f"PE Dominant: {dominant['pe_dominant_strikes']}")

buildup = chain.get_max_oi_buildup()
print(f"Max CE Buildup: {buildup['max_ce_buildup']['strike']}")
```

---

## 📈 Post-Trade Analytics

### PnL Metrics
```python
pnl = aggregator.post_analytics.pnl_analytics
print(f"Win Rate: {pnl.win_rate:.1f}%")
print(f"Avg R:R: {pnl.avg_risk_reward:.2f}")
print(f"Total PnL: ₹{pnl.total_pnl:+,.2f}")
```

### Exit Analysis
```python
exit_report = aggregator.post_analytics.exit_report
best = exit_report.get_best_exit_strategy()
worst = exit_report.get_worst_exit_strategy()
print(f"Best Exit: {best}")
print(f"Worst Exit: {worst}")
```

### Greeks Accuracy
```python
greeks = aggregator.post_analytics.greeks_accuracy
print(f"Delta Win Rate: {greeks.high_delta_win_rate:.1f}%")
print(f"Theta Exit Win Rate: {greeks.theta_exit_win_rate:.1f}%")
```

### OI Conviction
```python
oi_report = aggregator.post_analytics.oi_conviction
high = oi_report.conviction_performance['HIGH']
print(f"HIGH OI Conviction Win Rate: {high['win_rate']:.1f}%")
```

### Time of Day
```python
time_report = aggregator.post_analytics.time_report
best = time_report.get_best_session()
worst = time_report.get_worst_session()
print(f"Best Session: {best}")
print(f"Worst Session: {worst}")
```

---

## 🔔 Alert System

```python
has_alerts, alerts = aggregator.check_alerts()

# Alert types:
# - Risk limit alerts (trades, loss, exposure)
# - Position alerts (exit triggers)
# - Market alerts (blocked, cooldown)
```

**Alert Examples:**
- `⚠️ Daily trade limit reached (5/5)`
- `⚠️ Theta exit triggered for NIFTY 19500 CE`
- `⚠️ Trading blocked: Low conviction + High volatility`
- `⚠️ Approaching max daily loss (80%)`

---

## 💾 Export Data

### JSON Snapshot
```python
aggregator.save_live_snapshot("logs/dashboard.json")
```

### Analytics Report
```python
aggregator.save_analytics_report("logs/analytics.txt")
```

---

## 🔗 Integration with Phase 1-8

```python
# Connect engines (when integrating with live trading)
aggregator.connect_engines(
    bias_engine=your_bias_engine,
    entry_engine=your_entry_engine,
    greeks_engine=your_greeks_engine,
    risk_system=your_risk_system,
    strictness_engine=your_strictness_engine,
    metrics_tracker=your_metrics_tracker
)

# Then use with live data instead of samples
aggregator.update_market_data(live_market_data)
aggregator.update_option_chain(live_option_chain)
aggregator.refresh_live_dashboard()
```

---

## 📋 Daily Workflow

### Morning (Pre-Market)
```python
# Check dashboard status
aggregator.refresh_live_dashboard()
print(aggregator.render_live_dashboard())

# Verify trade eligibility
bias = aggregator.live_dashboard.bias_panel
if not bias.is_tradeable():
    print("⚠️ Trading not allowed today")
    exit()
```

### During Market Hours
```python
# Refresh every 5-10 seconds
while market_open:
    aggregator.update_market_data(get_live_data())
    aggregator.refresh_live_dashboard()
    
    # Check alerts
    has_alerts, alerts = aggregator.check_alerts()
    if has_alerts:
        send_notifications(alerts)
    
    time.sleep(5)
```

### Post-Market
```python
# Run analytics
trades = load_todays_trades()
aggregator.load_completed_trades(trades)
report = aggregator.run_post_trade_analysis(period="DAY")

# Save report
aggregator.save_analytics_report(f"logs/report_{date.today()}.txt")
```

### Weekly Review
```python
# Load week's trades
trades = load_weeks_trades()
aggregator.load_completed_trades(trades)
report = aggregator.run_post_trade_analysis(period="WEEK")

# Analyze patterns
time_report = aggregator.post_analytics.time_report
best_session = time_report.get_best_session()
print(f"Focus on {best_session} next week")
```

---

## 🎯 Key Metrics to Watch

### Live Trading:
1. **Bias Status** — Am I allowed to trade?
2. **Position PnL** — Am I in profit/loss?
3. **Exit Triggers** — Should I exit now?
4. **Risk Limits** — Can I take another trade?
5. **Option Chain** — Where's smart money?

### Post-Trade:
1. **Win Rate** — Improving or declining?
2. **R:R Ratio** — Are wins big enough?
3. **Best Exit** — Which exit works best?
4. **Best Time** — When do I trade best?
5. **OI Conviction** — Does HIGH really work?

---

## 🚨 Common Patterns

### Trade Blocked?
```python
bias = aggregator.live_dashboard.bias_panel
if bias.trade_allowed == TradeAllowance.BLOCKED:
    print("Reasons:", bias.block_reasons)
    # Fix: Wait for better setup, don't force trades
```

### Exit Triggered?
```python
monitor = aggregator.live_dashboard.trade_monitor
if monitor.theta_exit_triggered:
    print("Theta exhausted - book profit")
if monitor.reversal_exit_triggered:
    print("Bias reversed - exit immediately")
```

### Risk Limit Reached?
```python
risk = aggregator.live_dashboard.risk_panel
if risk.is_at_risk_limit():
    print("Stop trading for today")
    activate_kill_switch()
```

---

## 💡 Quick Tips

**Live Dashboard:**
- Refresh every 5-10 seconds during market
- Always check alerts before new trade
- Monitor exit triggers closely

**Post-Trade Analytics:**
- Run daily (after market close)
- Run weekly (Friday EOD)
- Focus on actionable insights

**Integration:**
- Use sample data for testing first
- Connect Phase 1-8 engines gradually
- Validate each integration step

---

## 🐛 Troubleshooting

### Dashboard not updating?
```python
# Ensure refresh is called
aggregator.refresh_live_dashboard()
```

### No alerts showing?
```python
# Check if panels are populated
if aggregator.live_dashboard.risk_panel is None:
    print("Risk panel not initialized")
```

### Analytics empty?
```python
# Ensure trades are loaded
if not aggregator.post_analytics.trades:
    aggregator.load_completed_trades(trades)
```

---

## 📁 File Locations

```
src/dashboard/
├── live_dashboard.py           # Live monitoring
├── post_trade_analytics.py     # Learning engine
└── dashboard_aggregator.py     # Integration layer

scripts/
└── phase9_dashboard_demo.py    # Demo script

logs/
├── dashboard_snapshot.json     # Live state export
└── post_trade_analytics.txt    # Analytics report

docs/
├── PHASE9_COMPLETE.md          # Full documentation
└── PHASE9_QUICK_REFERENCE.md   # This file
```

---

## ⚡ One-Liners

```python
# Full dashboard in terminal
print(DashboardAggregator().render_live_dashboard())

# Quick analytics
aggregator.run_post_trade_analysis("DAY")

# Check if tradeable
aggregator.live_dashboard.bias_panel.is_tradeable()

# Current PnL
aggregator.live_dashboard.trade_monitor.unrealized_pnl

# Win rate
aggregator.post_analytics.pnl_analytics.win_rate

# Best time to trade
aggregator.post_analytics.time_report.get_best_session()
```

---

## 🎓 Learn from Dashboard

**Questions Dashboard Answers:**

1. **Why was I blocked?** → Bias Panel (block_reasons)
2. **Should I exit now?** → Trade Monitor (exit triggers)
3. **Can I take another trade?** → Risk Panel (limits)
4. **Where's smart money?** → Option Chain (dominant strikes)
5. **Which exit works best?** → Exit Reason Analysis
6. **When should I trade?** → Time-of-Day Report
7. **Does OI conviction matter?** → OI Conviction Report
8. **Are my Greeks accurate?** → Greeks Accuracy Report

**These answers = Better decisions = Higher profits**

---

## ✅ Validation Checklist

- [ ] Demo runs successfully
- [ ] Live dashboard displays all 5 panels
- [ ] Post-trade analytics generates insights
- [ ] Alerts detected correctly
- [ ] JSON/text exports created
- [ ] Integration points identified
- [ ] Sample data works
- [ ] Ready for Phase 1-8 integration

---

## 🚀 Next Steps

1. **Test with sample data** ✅ (Done)
2. **Integrate with Phase 1-8** (Connect engines)
3. **Add web UI** (Optional - Flask/FastAPI)
4. **Setup alerts** (Telegram/Email)
5. **Deploy to production** (Live trading)

---

**Phase 9 Status: Complete ✅**  
**Philosophy: "লাইভ দেখাবে, পরে শেখাবে" — Delivered!**  
**Angel-X has eyes 👁️ and mirror 🪞**
