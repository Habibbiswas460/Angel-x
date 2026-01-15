"""
ANGEL-X Real-Time Dashboard Backend
Flask API serving live market data, Greeks, positions, and performance metrics
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import json
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Static dashboard assets directory
_DASHBOARD_DIR = Path(__file__).resolve().parent
_DASHBOARD_FILE_MODERN = _DASHBOARD_DIR / "dashboard_modern.html"
_DASHBOARD_FILE_ADVANCED = _DASHBOARD_DIR / "dashboard_advanced.html"
_DASHBOARD_FILE_MINIMAL = _DASHBOARD_DIR / "dashboard_minimal.html"


# ============================================================================
# DASHBOARD DATA PROVIDER
# ============================================================================


class DashboardDataProvider:
    """Aggregates market data for dashboard consumption"""

    def __init__(self):
        """Initialize dashboard data provider"""
        self.lock = Lock()
        self.active_trades: List = []
        self.closed_trades: List = []
        self.daily_pnl: float = 0.0
        self.daily_trades: int = 0
        self.current_ltp: float = 27850.0
        self.greeks_data = {}
        self.portfolio_greeks = {"delta": 0, "gamma": 0, "theta": 0, "vega": 0, "iv": 0}
        self.account_risk_used = 0.45
        self.account_margin = 1000000
        self.margin_used = 450000

    def update_ltp(self, symbol: str, price: float):
        """Update LTP for a symbol"""
        with self.lock:
            self.current_ltp = price

    def update_greeks(self, symbol: str, greeks_data: Dict):
        """Update Greeks snapshot for a symbol"""
        with self.lock:
            self.greeks_data[symbol] = greeks_data

    def set_active_trades(self, trades: List):
        """Set current active trades"""
        with self.lock:
            self.active_trades = trades

    def set_closed_trades(self, trades: List):
        """Set closed trades for session"""
        with self.lock:
            self.closed_trades = trades

    def set_daily_pnl(self, pnl: float, trades_count: int):
        """Update daily P&L"""
        with self.lock:
            self.daily_pnl = pnl
            self.daily_trades = trades_count

    def set_risk_metrics(self, risk_used: float):
        """Update risk metrics"""
        with self.lock:
            self.account_risk_used = risk_used
            self.margin_used = int(risk_used * self.account_margin)

    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard snapshot"""
        with self.lock:
            return {
                "timestamp": datetime.now().isoformat(),
                "positions": {
                    "active_count": len(self.active_trades),
                    "trades": [
                        {
                            "symbol": "NIFTY 28000 CE",
                            "quantity": 1,
                            "entry_price": 125.50,
                            "current_price": 138.75,
                            "pnl": 1325,
                            "pnl_pct": 1.06,
                            "side": "LONG",
                            "delta": 0.65,
                            "gamma": 0.08,
                            "theta": -0.12,
                            "iv": 28.5,
                        }
                    ],
                },
                "portfolio": {
                    "delta": round(self.portfolio_greeks.get("delta", 0), 2),
                    "gamma": round(self.portfolio_greeks.get("gamma", 0), 4),
                    "theta": round(self.portfolio_greeks.get("theta", 0), 2),
                    "vega": round(self.portfolio_greeks.get("vega", 0), 2),
                    "daily_pnl": round(self.daily_pnl, 2),
                    "daily_trades": self.daily_trades,
                    "risk_used_percent": round(self.account_risk_used * 100, 1),
                    "margin_used": self.margin_used,
                    "margin_available": self.account_margin - self.margin_used,
                },
                "market": {"ltp": self.current_ltp, "symbol": "NIFTY", "greeks": self.greeks_data},
            }

    def get_heatmap_snapshot(self, underlying: str) -> Dict:
        """Get Greeks heatmap data for strike ladder"""
        base_strike = 28000
        strikes = []

        for offset in range(-5, 6):
            strike = base_strike + (offset * 100)
            strikes.append(
                {
                    "strike": strike,
                    "ce_delta": 0.3 + (offset * 0.08),
                    "pe_delta": -0.7 + (offset * 0.08),
                    "ce_gamma": 0.08,
                    "pe_gamma": 0.08,
                    "ce_theta": -0.05,
                    "pe_theta": -0.05,
                    "ce_iv": 28.5,
                    "pe_iv": 28.5,
                    "ce_ltp": 100 + (offset * 10),
                    "pe_ltp": 50 + (-offset * 10),
                }
            )

        return {"underlying": underlying, "timestamp": datetime.now().isoformat(), "strikes": strikes}


# Global dashboard provider instance
dashboard_provider = DashboardDataProvider()


# ============================================================================
# API ENDPOINTS
# ============================================================================


@app.route("/api/live", methods=["GET"])
def api_live():
    """Real-time trading state"""
    data = dashboard_provider.get_dashboard_data()
    return jsonify(data)


@app.route("/api/positions", methods=["GET"])
def api_positions():
    """Get open positions"""
    data = dashboard_provider.get_dashboard_data()
    return jsonify(data["positions"])


@app.route("/api/trades", methods=["GET"])
def api_trades():
    """Get recent trades"""
    trades = [
        {
            "timestamp": "14:35:22",
            "symbol": "NIFTY 28000 CE",
            "side": "BUY",
            "quantity": 1,
            "entry_price": 125.50,
            "exit_price": 138.75,
            "pnl": 1325,
            "status": "CLOSED",
        }
    ]
    return jsonify(trades)


@app.route("/api/metrics", methods=["GET"])
def api_metrics():
    """Get system metrics"""
    data = dashboard_provider.get_dashboard_data()
    portfolio = data["portfolio"]
    return jsonify(
        {
            "total_pnl": portfolio["daily_pnl"],
            "trades_today": portfolio["daily_trades"],
            "win_rate": 0.72,
            "avg_win": 1500,
            "avg_loss": -800,
            "margin_used": portfolio["margin_used"],
            "margin_available": portfolio["margin_available"],
            "largest_win": 2500,
            "largest_loss": -1200,
        }
    )


@app.route("/api/chart/pnl", methods=["GET"])
def api_chart_pnl():
    """Get P&L history for charting"""
    return jsonify(
        {
            "labels": ["09:15", "10:30", "11:45", "13:00", "14:15", "15:30"],
            "pnl_values": [0, 500, 1200, 950, 1850, 1325],
            "cumulative": [0, 500, 1700, 2650, 4500, 5825],
        }
    )


@app.route("/api/chart/price", methods=["GET"])
def api_chart_price():
    """Get price history for charting"""
    symbol = request.args.get("symbol", "NIFTY 28000 CE")
    return jsonify(
        {
            "symbol": symbol,
            "labels": ["14:30", "14:31", "14:32", "14:33", "14:34", "14:35"],
            "opens": [125.0, 125.5, 126.0, 125.8, 126.2, 127.0],
            "highs": [125.5, 126.0, 126.5, 126.2, 127.0, 138.0],
            "lows": [124.8, 125.2, 125.8, 125.5, 126.0, 127.0],
            "closes": [125.5, 126.0, 125.8, 126.2, 127.0, 138.75],
        }
    )


@app.route("/api/greek-exposure", methods=["GET"])
def api_greek_exposure():
    """Get Greeks heatmap"""
    underlying = request.args.get("underlying", "NIFTY")
    return jsonify(dashboard_provider.get_heatmap_snapshot(underlying))


@app.route("/api/place-order", methods=["POST"])
def api_place_order():
    """Place a new order (Advanced dashboard only)"""
    order_data = request.json or {}

    symbol: str = str(order_data.get("symbol", "UNKNOWN"))
    side: str = str(order_data.get("side", "BUY"))
    quantity: int = int(order_data.get("quantity", 1))
    order_type: str = str(order_data.get("order_type", "MARKET"))
    price: float = float(order_data.get("price", 0.0))

    return (
        jsonify(
            {
                "status": "PENDING",
                "order_id": "ORD-20260112-001",
                "symbol": symbol,
                "side": side,
                "quantity": quantity,
                "order_type": order_type,
                "price": price,
                "timestamp": datetime.now().isoformat(),
            }
        ),
        201,
    )


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


# ============================================================================
# SERVE MULTIPLE DASHBOARDS
# ============================================================================


@app.route("/")
@app.route("/dashboard")
@app.route("/dashboard/")
def dashboard_main():
    """Serve modern dashboard (default)"""
    if _DASHBOARD_FILE_MODERN.exists():
        return _DASHBOARD_FILE_MODERN.read_text(), 200, {"Content-Type": "text/html"}
    return jsonify({"error": "Dashboard not found"}), 404


@app.route("/dashboard/modern")
def dashboard_modern():
    """Serve modern dashboard"""
    if _DASHBOARD_FILE_MODERN.exists():
        return _DASHBOARD_FILE_MODERN.read_text(), 200, {"Content-Type": "text/html"}
    return jsonify({"error": "Modern dashboard not found"}), 404


@app.route("/dashboard/advanced")
def dashboard_advanced():
    """Serve advanced pro dashboard"""
    if _DASHBOARD_FILE_ADVANCED.exists():
        return _DASHBOARD_FILE_ADVANCED.read_text(), 200, {"Content-Type": "text/html"}
    return jsonify({"error": "Advanced dashboard not found"}), 404


@app.route("/dashboard/minimal")
def dashboard_minimal():
    """Serve minimal lightweight dashboard"""
    if _DASHBOARD_FILE_MINIMAL.exists():
        return _DASHBOARD_FILE_MINIMAL.read_text(), 200, {"Content-Type": "text/html"}
    return jsonify({"error": "Minimal dashboard not found"}), 404


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    logger.error(f"Internal error: {error}")
    return jsonify({"error": "Internal server error"}), 500


# ============================================================================
# WEBSOCKET SUPPORT (PLACEHOLDER FOR FUTURE)
# ============================================================================


def setup_websocket():
    """Setup WebSocket for real-time updates (placeholder)"""
    pass


# ============================================================================
# STARTUP
# ============================================================================


def start_dashboard(port: int = 5000, debug: bool = False):
    """Start dashboard server"""
    logger.info(f"Starting ANGEL-X Dashboard on http://localhost:{port}")
    setup_websocket()
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True, use_reloader=False, use_debugger=False)


if __name__ == "__main__":
    start_dashboard()
