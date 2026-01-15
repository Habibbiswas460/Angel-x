# Angel-X Professional Dashboard

Real-time trading dashboard displaying live market data, P&L, trades, and Greeks exposure.

## 📁 Files

### Core Components
- **`routes.py`** - Flask Blueprint with API endpoints
  - `/api/live` - Real-time metrics
  - `/api/trades` - Trade history
  - `/api/positions` - Open positions
  - `/api/metrics` - Session statistics
  - `/api/chart/pnl` - P&L over time
  - `/api/greek-exposure` - Greeks exposure
  - `/export/*` - CSV/JSON exports

- **`data_aggregator.py`** - Data collection engine
  - Reads from TradeJournalEngine
  - Reads from DataFeed
  - Reads from BrokerClient
  - Formats all data for JSON API responses

- **`app_factory.py`** - Flask app initialization
  - `create_dashboard_app()` - Create configured app
  - `run_dashboard_app()` - Run dashboard directly

### UI Files
- **`dashboard_enhanced.html`** - Main dashboard interface
  - 4 tabs: Overview, Trades, Analytics, Greeks
  - Real-time charts using Chart.js
  - Dark/light theme support
  - Export functionality
  - Responsive design

- **`dashboard_modern.html`** - Modern version (lighter)
- **`dashboard_advanced.html`** - Advanced version (all features)
- **`dashboard_minimal.html`** - Minimal version (lightweight)

---

## 🚀 Quick Start

### Option 1: Standalone Dashboard

```python
from src.dashboard.app_factory import create_dashboard_app
from main import AngelXStrategy

# Create strategy (initializes all components)
strategy = AngelXStrategy()

# Create Flask app with real data
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker
)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

Then open: **http://localhost:5000/dashboard/enhanced**

### Option 2: Dashboard in Background

```python
import threading
from src.dashboard.app_factory import create_dashboard_app
from main import AngelXStrategy

strategy = AngelXStrategy()
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker
)

# Run in background
threading.Thread(
    target=lambda: app.run(host='0.0.0.0', port=5000),
    daemon=True
).start()

# Continue with trading
strategy.start()
```

---

## 📊 Available Endpoints

```bash
# Live metrics
curl http://localhost:5000/dashboard/api/live

# Recent trades (limit=50 optional)
curl http://localhost:5000/dashboard/api/trades?limit=50

# Open positions
curl http://localhost:5000/dashboard/api/positions

# Session statistics
curl http://localhost:5000/dashboard/api/metrics

# P&L chart data
curl http://localhost:5000/dashboard/api/chart/pnl

# Greeks exposure
curl http://localhost:5000/dashboard/api/greek-exposure

# Export trades as CSV
curl http://localhost:5000/dashboard/export/trades/csv

# Export report as JSON
curl http://localhost:5000/dashboard/export/report/json
```

---

## 🎨 Dashboard Features

### Overview Tab
- Real-time P&L display
- Open positions count
- Win rate percentage
- P&L time series chart
- Greeks radar chart
- System performance metrics

### Trades Tab
- Complete trade history
- Entry/exit prices and times
- Trade quantity and side
- Profit/loss per trade
- Trade duration
- Trade status (OPEN/CLOSED)
- Export to CSV

### Analytics Tab
- Trade distribution (pie chart)
- Hourly P&L breakdown (bar chart)
- Performance metrics:
  - Total trades
  - Winning/losing trades
  - Profit factor
  - Risk-reward ratio
  - Average trade duration

### Greeks Tab
- Delta exposure (bullish/neutral/bearish)
- Gamma exposure
- Theta exposure (time decay)
- Vega exposure (volatility)
- Real-time visualization

---

## 🔄 Data Flow

```
AngelXStrategy (trading)
    ↓
TradeJournalEngine (records trades)
DataFeed (market data)
BrokerClient (connection status)
    ↓
DashboardDataAggregator (collects & formats)
    ↓
Flask Routes (/api/*)
    ↓
Dashboard Frontend (fetches every 2s)
    ↓
Browser Display (charts, tables, metrics)
```

---

## ⚙️ Configuration

### Data Refresh Intervals

Edit `dashboard_enhanced.html` to adjust refresh rates:

```javascript
const REFRESH_INTERVAL = 2000; // 2 seconds for live metrics
// Charts refresh: 2 seconds
// Trades/Greeks refresh: 4 seconds
```

### Dashboard Versions

- `/dashboard/minimal` - Lightweight version
- `/dashboard/modern` - Modern clean design
- `/dashboard/advanced` - Full features
- `/dashboard/enhanced` - **Recommended** (all features + dark/light theme)

---

## 🎯 API Response Examples

### GET /api/live
```json
{
  "timestamp": "2026-01-14T14:35:00",
  "status": "active",
  "data": {
    "total_pnl": 12450,
    "total_trades": 25,
    "winning_trades": 18,
    "losing_trades": 7,
    "win_rate": 0.72,
    "open_positions": 5,
    "nifty_ltp": 27850
  }
}
```

### GET /api/trades
```json
[
  {
    "symbol": "NIFTY 28000 CE",
    "entry_price": 125.50,
    "exit_price": 138.75,
    "quantity": 1,
    "side": "BUY",
    "pnl_rupees": 1325,
    "pnl_percent": 1.06,
    "status": "CLOSED",
    "duration_seconds": 135
  }
]
```

### GET /api/metrics
```json
{
  "total_pnl": 12450,
  "total_trades": 25,
  "winning_trades": 18,
  "losing_trades": 7,
  "win_rate": 0.72,
  "profit_factor": 1.86,
  "avg_pnl_per_trade": 498.0
}
```

---

## 🔧 Customization

### Add Custom Metric

1. Add method to `DashboardDataAggregator`:
```python
def get_custom_metric(self) -> Dict[str, Any]:
    return {'my_data': self.trade_journal.calculate_something()}
```

2. Add endpoint to `routes.py`:
```python
@dashboard_bp.route('/api/custom-metric')
def get_custom_metric():
    aggregator = get_aggregator()
    return jsonify(aggregator.get_custom_metric())
```

3. Update dashboard HTML to fetch and display.

---

## 🐛 Troubleshooting

### No data displayed
- Check: Is `strategy.trade_journal` initialized?
- Check: Are there any trades in the journal?
- Check: Browser console for JavaScript errors

### API returns error
- Check: Are all data sources (trade_journal, data_feed) initialized?
- Check: Server logs for Python errors
- Check: Flask app is running on correct port

### High CPU usage
- Solution: Reduce REFRESH_INTERVAL
- Solution: Run on separate thread
- Solution: Use WebSocket instead of polling

### Charts not updating
- Check: Is fetch working? (F12 → Network tab)
- Check: Is data being returned from /api/chart/pnl?
- Check: Browser console for Chart.js errors

---

## 📚 Documentation

- [DASHBOARD_QUICK_START.md](../docs/DASHBOARD_QUICK_START.md) - 5 minute setup
- [DASHBOARD_INTEGRATION.md](../docs/DASHBOARD_INTEGRATION.md) - Comprehensive guide
- [DASHBOARD_IMPLEMENTATION_SUMMARY.md](../docs/DASHBOARD_IMPLEMENTATION_SUMMARY.md) - Technical summary

---

## 🚀 Production Deployment

### Using Gunicorn

```bash
pip install gunicorn

# Create wsgi.py
python -m gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app
```

### Using Docker

See `../Dockerfile` for dashboard container setup.

### Using Systemd

```ini
[Unit]
Description=Angel-X Dashboard
After=network.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/angel-x
ExecStart=/usr/bin/python3 /home/trader/angel-x/dashboard_server.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

---

## 📞 Support

See documentation files:
- **Setup issues**: [DASHBOARD_QUICK_START.md](../docs/DASHBOARD_QUICK_START.md)
- **Integration help**: [DASHBOARD_INTEGRATION.md](../docs/DASHBOARD_INTEGRATION.md)
- **API reference**: [DASHBOARD_INTEGRATION.md](../docs/DASHBOARD_INTEGRATION.md#3-api-endpoints-reference)

---

## ✨ Features Highlights

✅ Real-time data from trading system
✅ Professional UI with animations
✅ Dark/light theme support
✅ Responsive design (mobile-friendly)
✅ Export trades to CSV/JSON
✅ Multiple dashboard versions
✅ Complete Greeks exposure tracking
✅ Trade performance analytics
✅ System health monitoring
✅ Production-ready error handling

---

**Dashboard Version**: 2.0 (Enhanced)
**Last Updated**: 2026-01-14
**Status**: Production Ready ✅
