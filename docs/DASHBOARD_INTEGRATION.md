"""
ANGEL-X DASHBOARD REAL DATA INTEGRATION GUIDE

This guide shows how to integrate the professional dashboard with real trading data
from your AngelXStrategy system.

Components:
1. DashboardDataAggregator - Collects real trading data
2. Dashboard Routes - Flask API endpoints
3. App Factory - Creates Flask app with real data sources
4. Dashboard HTML - Frontend that fetches and displays data
"""

# ============================================================================
# 1. BASIC INTEGRATION WITH ANGELX STRATEGY
# ============================================================================

# In your main.py or wherever you initialize AngelXStrategy:

from flask import Flask
from src.dashboard.app_factory import create_dashboard_app
from main import AngelXStrategy

# Create strategy instance (this initializes trade_journal, data_feed, etc.)
strategy = AngelXStrategy()

# Create Flask app with real data sources
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker  # Or your broker client
)

# Now the dashboard will display real trading data!
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)


# ============================================================================
# 2. RUNNING DASHBOARD ALONGSIDE STRATEGY
# ============================================================================

# Option A: Run dashboard in a separate thread

import threading
from src.dashboard.app_factory import create_dashboard_app
from main import AngelXStrategy

# Create strategy
strategy = AngelXStrategy()

# Create dashboard app
app = create_dashboard_app(
    trade_journal=strategy.trade_journal,
    data_feed=strategy.data_feed,
    broker_client=strategy.integration.broker
)

# Run dashboard in background thread
def run_dashboard():
    app.run(host='0.0.0.0', port=5000, debug=False)

dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
dashboard_thread.start()

# Now run your strategy
strategy.start()  # Or whatever method starts trading


# Option B: Use Gunicorn/uWSGI for production

# Create wsgi.py:
# ----------------
# from src.dashboard.app_factory import create_dashboard_app
# from main import AngelXStrategy
# 
# strategy = AngelXStrategy()
# app = create_dashboard_app(
#     trade_journal=strategy.trade_journal,
#     data_feed=strategy.data_feed,
#     broker_client=strategy.integration.broker
# )
#
# if __name__ == '__main__':
#     app.run()

# Then run: gunicorn -w 2 -b 0.0.0.0:5000 wsgi:app


# ============================================================================
# 3. API ENDPOINTS REFERENCE
# ============================================================================

"""
All endpoints return real trading data from your strategy:

GET /dashboard/api/live
    Returns real-time trading metrics
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

GET /dashboard/api/trades?limit=50
    Returns list of recent trades with details
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
        },
        ...
    ]

GET /dashboard/api/positions
    Returns open positions
    [
        {
            "symbol": "NIFTY 28000 CE",
            "entry_price": 125.50,
            "current_price": 138.75,
            "pnl_rupees": 1325,
            "pnl_percent": 1.06,
            "quantity": 1
        },
        ...
    ]

GET /dashboard/api/metrics
    Returns session statistics
    {
        "total_pnl": 12450,
        "total_trades": 25,
        "winning_trades": 18,
        "losing_trades": 7,
        "win_rate": 0.72,
        "max_profit": 2150,
        "max_loss": -650,
        "profit_factor": 1.86,
        "avg_pnl_per_trade": 498.0
    }

GET /dashboard/api/chart/pnl
    Returns P&L over time for charting
    {
        "labels": ["09:30", "10:00", "10:30", ...],
        "values": [0, 500, 1200, ...]
    }

GET /dashboard/api/greek-exposure
    Returns current Greeks exposure
    {
        "delta": {"value": 0.45, "status": "positive"},
        "gamma": {"value": 0.08, "status": "positive"},
        "theta": {"value": 0.65, "status": "positive"},
        "vega": {"value": -0.12, "status": "negative"}
    }

GET /dashboard/export/trades/csv
    Downloads trades as CSV file

GET /dashboard/export/report/json
    Downloads report as JSON file
"""

# ============================================================================
# 4. DATA FLOW ARCHITECTURE
# ============================================================================

"""
┌─────────────────────────────────────────────────────────────────────┐
│                      ANGEL-X STRATEGY EXECUTION                     │
│  (Trades, Positions, Greeks, Market Data flowing through system)   │
└──────────────────┬────────────────────────────────────────────────┘
                   │
                   ├─→ TradeJournalEngine (stores all trades)
                   ├─→ DataFeed (market data)
                   └─→ BrokerClient (connection status)
                   
┌──────────────────────────────────────────────────────────────────────┐
│           DashboardDataAggregator (Real-Time Data Collection)        │
│  Reads from: TradeJournalEngine, DataFeed, BrokerClient             │
│  Methods: get_live_data(), get_trades(), get_positions(), etc.      │
└──────────────────┬────────────────────────────────────────────────┘
                   │
                   └─→ Flask Routes (/api/*)
                      ├─→ /api/live (aggregator.get_live_data())
                      ├─→ /api/trades (aggregator.get_all_trades())
                      ├─→ /api/positions (aggregator.get_positions())
                      ├─→ /api/metrics (aggregator.get_session_stats())
                      ├─→ /api/chart/pnl (aggregator.get_pnl_chart_data())
                      └─→ /api/greek-exposure (aggregator.get_greeks_exposure())

┌──────────────────────────────────────────────────────────────────────┐
│              Dashboard Frontend (Browser)                            │
│  ✓ Fetches /api/* every 2 seconds                                   │
│  ✓ Updates charts in real-time                                       │
│  ✓ Displays live P&L, trades, Greeks exposure                       │
│  ✓ Dark/light theme toggle                                          │
│  ✓ Export functionality (CSV, JSON)                                 │
└──────────────────────────────────────────────────────────────────────┘
"""

# ============================================================================
# 5. CUSTOM DATA INTEGRATION
# ============================================================================

"""
To add custom data to the dashboard:

Step 1: Add method to DashboardDataAggregator (src/dashboard/data_aggregator.py)
    
    def get_custom_metric(self) -> Dict[str, Any]:
        return {
            'my_metric': self.trade_journal.some_calculation(),
            'status': 'active'
        }

Step 2: Add API endpoint in routes.py (src/dashboard/routes.py)
    
    @dashboard_bp.route('/api/custom-metric', methods=['GET'])
    def get_custom_metric():
        try:
            aggregator = get_aggregator()
            return jsonify(aggregator.get_custom_metric())
        except Exception as e:
            return jsonify({'error': str(e)}), 500

Step 3: Update dashboard HTML to fetch and display
    
    async function fetchCustomMetric() {
        const response = await fetch('/dashboard/api/custom-metric');
        const data = await response.json();
        // Display data...
    }
    
    // Add to initialization:
    setInterval(fetchCustomMetric, 2000);
"""

# ============================================================================
# 6. WEBSOCKET FOR REAL-TIME UPDATES (OPTIONAL)
# ============================================================================

"""
For real-time updates without polling, use WebSocket:

from flask_socketio import SocketIO, emit
from flask import emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('connect')
def handle_connect():
    emit('connect_response', {'data': 'Connected to real-time dashboard'})

@socketio.on('subscribe')
def handle_subscribe(data):
    # Send live data updates
    emit('live_data', aggregator.get_live_data())

# Run in background to push updates
def push_live_updates():
    while True:
        socketio.emit('live_data', aggregator.get_live_data())
        time.sleep(1)

# On dashboard JavaScript:
const socket = io();
socket.on('live_data', (data) => {
    updateLiveMetrics(data);
});
"""

# ============================================================================
# 7. PERFORMANCE OPTIMIZATION
# ============================================================================

"""
Tips for optimal dashboard performance:

1. Data Refresh Rates:
   - Live metrics: 2 seconds (frequent updates for P&L, trades)
   - Greeks data: 5 seconds (less volatile)
   - Charts: 2 seconds (smooth animation)

2. Use WebSocket for high-frequency updates
   - Reduces overhead vs HTTP polling
   - Real-time push updates

3. Implement data caching:
   - Cache expensive calculations
   - Update only when data changes

4. Lazy load heavy components:
   - Load Greeks heatmap only when tab clicked
   - Load detailed analytics on demand

5. Pagination for large datasets:
   - Show recent 50 trades by default
   - Pagination for historical data

6. Compression:
   - Enable gzip compression on API responses
   - Minimize JSON payloads
"""

# ============================================================================
# 8. TROUBLESHOOTING
# ============================================================================

"""
Common Issues & Solutions:

Issue: Dashboard shows "No data" or old data
Solution: Ensure trade_journal is properly initialized and trade objects exist
         Check that TradeJournalEngine is the same instance passed to aggregator

Issue: API returns error 500
Solution: Check logs for aggregator exceptions
         Ensure trade_journal, data_feed, broker_client are not None
         Verify data structures match expected format

Issue: Charts not updating
Solution: Check browser console for JavaScript errors
         Verify API endpoints are returning correct JSON format
         Ensure Chart.js library loaded

Issue: High CPU/Memory usage
Solution: Reduce refresh rate (increase interval)
         Use WebSocket instead of polling
         Implement data caching
         Limit number of trades displayed

Issue: Data delays
Solution: Reduce processing in aggregator methods
         Cache intermediate calculations
         Use async operations for heavy computations
"""

# ============================================================================
# 9. DEPLOYMENT
# ============================================================================

"""
Production Deployment:

1. Docker:
   - Build image with dashboard support
   - Mount strategy and dashboard on same volume
   - Expose port 5000

2. Kubernetes:
   - Run strategy and dashboard as separate services
   - Use ConfigMap for data sharing
   - Load balancer for high availability

3. Systemd:
   - Create service file for dashboard
   - Auto-restart on failure
   - Log rotation

4. Environment Variables:
   - Set FLASK_ENV=production
   - Disable debug mode
   - Configure CORS origins
   - Set security headers
"""

# ============================================================================
# 10. SECURITY CONSIDERATIONS
# ============================================================================

"""
Security Best Practices:

1. Input Validation:
   - All API inputs validated
   - SQL injection protection
   - XSS protection via JSON serialization

2. Authentication:
   - Add JWT token validation
   - Rate limiting on API endpoints
   - API key for external access

3. Data Protection:
   - HTTPS/SSL for API traffic
   - Sensitive data filtering
   - Audit logging

4. Access Control:
   - Restrict API to local network in development
   - CORS configuration for production
   - IP whitelist for data access

5. Monitoring:
   - Log all API requests
   - Monitor for unusual patterns
   - Alert on errors/anomalies
"""

if __name__ == '__main__':
    print(__doc__)
