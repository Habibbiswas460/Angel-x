# Dashboard Real Data Integration - Quick Start

This guide will get your professional dashboard displaying real trading data in under 5 minutes.

## 📋 Prerequisites

- Python 3.12+ 
- AngelXStrategy initialized (from `main.py`)
- Flask already installed

## 🚀 Quick Start (5 minutes)

### Step 1: Import the App Factory

```python
from src.dashboard.app_factory import create_dashboard_app
from main import AngelXStrategy
```

### Step 2: Create Strategy Instance

```python
# This initializes trade_journal, data_feed, broker_client
strategy = AngelXStrategy()
```

### Step 3: Create Dashboard App with Real Data

```python
# Create Flask app with your real trading data sources
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker
)
```

### Step 4: Run the Dashboard

```python
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Step 5: Open Dashboard

Navigate to: **http://localhost:5000/dashboard/enhanced**

✅ Your dashboard is now displaying **real trading data**!

## 📊 What You're Seeing

The dashboard automatically displays:

- ✅ **Live P&L** - Real-time profit/loss from your trades
- ✅ **Trade History** - All trades with entry/exit prices and return %
- ✅ **Greeks Exposure** - Delta, Gamma, Theta, Vega from your portfolio
- ✅ **Performance Metrics** - Win rate, profit factor, average trade duration
- ✅ **Charts** - P&L timeline, trade distribution, hourly breakdown
- ✅ **Open Positions** - Current positions with live P&L
- ✅ **System Status** - Broker connection, data feed status

## 🔄 Data Refresh

Dashboard updates automatically:
- **Every 2 seconds**: Live metrics, P&L charts, trades
- **Every 5 seconds**: Greeks exposure

No manual refresh needed!

## 🎨 Features

### Dark/Light Theme
Click the moon icon in the top-right to toggle theme. Your preference is saved.

### Export Data
- **Export CSV**: Download all trades
- **Export JSON**: Download complete report with metrics

### Real-Time Updates
All data flows directly from your AngelXStrategy system through:
- `TradeJournalEngine` → trades and statistics
- `DataFeed` → market data (NIFTY, BANKNIFTY LTP)
- `BrokerClient` → connection status

## 🚀 Production Deployment

### Run in Background Thread

```python
import threading

strategy = AngelXStrategy()
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker
)

# Run dashboard in background
dashboard_thread = threading.Thread(
    target=lambda: app.run(host='0.0.0.0', port=5000),
    daemon=True
)
dashboard_thread.start()

# Continue with your strategy
strategy.start()
```

### Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Create wsgi.py
# (See DASHBOARD_INTEGRATION.md for full wsgi.py example)

# Run with 2 worker processes
gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app
```

## 📡 API Endpoints

All endpoints return real data:

```
GET /dashboard/api/live              → Current P&L, trades, positions
GET /dashboard/api/trades?limit=50   → Recent trades
GET /dashboard/api/positions         → Open positions
GET /dashboard/api/metrics           → Session statistics
GET /dashboard/api/chart/pnl         → P&L over time
GET /dashboard/api/greek-exposure    → Greeks exposure

GET /dashboard/export/trades/csv     → Download trades as CSV
GET /dashboard/export/report/json    → Download full report as JSON
```

## 🔧 Troubleshooting

### Dashboard shows no data
**Check**: Is `strategy.trade_journal` properly initialized?
**Solution**: Ensure AngelXStrategy has `self.trade_journal = TradeJournal()` in `__init__`

### API returns "error"
**Check**: Browser console for errors
**Solution**: Ensure all data sources (trade_journal, data_feed) are not None

### Charts not loading
**Check**: Are you using a modern browser with JavaScript enabled?
**Solution**: Check browser console (F12) for errors

### High CPU usage
**Check**: Is refresh interval too frequent?
**Solution**: Reduce REFRESH_INTERVAL in dashboard_enhanced.html (currently 2000ms)

## 📚 Advanced Usage

See [DASHBOARD_INTEGRATION.md](DASHBOARD_INTEGRATION.md) for:
- Custom data integration
- WebSocket real-time updates
- Performance optimization
- Security best practices
- Deployment strategies

## ✨ Next Steps

1. **Start trading** - Run your AngelXStrategy
2. **Watch the dashboard** - See real-time updates of your P&L
3. **Export reports** - Download trades and metrics for analysis
4. **Customize** - Add custom metrics or charts

## 📞 Support

Dashboard issues? Check:
1. [DASHBOARD_INTEGRATION.md](DASHBOARD_INTEGRATION.md) - Comprehensive integration guide
2. [OPERATIONS.md](OPERATIONS.md) - Common operations
3. Browser console (F12) - JavaScript errors
4. Server logs - Python/Flask errors

---

**Happy Trading!** 🚀

Your dashboard is now connected to real trading data from Angel-X.
