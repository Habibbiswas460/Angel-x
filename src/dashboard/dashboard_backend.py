"""
ANGEL-X Real-Time Dashboard Backend
Flask API serving live market data, Greeks, positions, and performance metrics
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import logging
import re
from datetime import datetime
from pathlib import Path
from threading import Lock
from typing import Dict, List, Optional

app = Flask(__name__)
CORS(app)

logger = logging.getLogger(__name__)

# Static dashboard assets
_DASHBOARD_DIR = Path(__file__).resolve().parent
_DASHBOARD_FILE = _DASHBOARD_DIR / "dashboard.html"


class DashboardDataProvider:
    """Aggregates market data for dashboard consumption"""
    
    def __init__(self):
        self.lock = Lock()
        self.current_ltp = {}  # symbol -> price
        self.greeks_data = {}  # symbol -> greeks snapshot
        self.active_trades = []
        self.closed_trades = []
        self.portfolio_greeks = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        self.daily_pnl = 0
        self.daily_trades = 0
        self.account_risk_used = 0
        
    def update_ltp(self, symbol: str, price: float):
        """Update LTP for a symbol"""
        with self.lock:
            self.current_ltp[symbol] = {
                'price': price,
                'timestamp': datetime.now().isoformat()
            }
    
    def update_greeks(self, symbol: str, greeks_data: Dict):
        """Update Greeks snapshot for a symbol"""
        with self.lock:
            self.greeks_data[symbol] = {
                **greeks_data,
                'timestamp': datetime.now().isoformat()
            }
    
    def set_active_trades(self, trades: List):
        """Set current active trades"""
        with self.lock:
            self.active_trades = trades
            self._compute_portfolio_greeks()
    
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
    
    def _compute_portfolio_greeks(self):
        """Compute aggregated portfolio Greeks"""
        portfolio = {'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0}
        
        for trade in self.active_trades:
            portfolio['delta'] += getattr(trade, 'entry_delta', 0) * trade.quantity
            portfolio['gamma'] += getattr(trade, 'entry_gamma', 0) * trade.quantity
            portfolio['theta'] += getattr(trade, 'entry_theta', 0) * trade.quantity
            portfolio['vega'] += getattr(trade, 'entry_iv', 0) * trade.quantity
        
        self.portfolio_greeks = portfolio
    
    def get_dashboard_data(self) -> Dict:
        """Get complete dashboard snapshot"""
        with self.lock:
            return {
                'timestamp': datetime.now().isoformat(),
                'positions': {
                    'active_count': len(self.active_trades),
                    'trades': [
                        {
                            'id': t.trade_id,
                            'underlying': getattr(t, 'underlying', 'NIFTY'),
                            'strike': t.strike,
                            'option_type': t.option_type,
                            'entry_price': t.entry_price,
                            'current_price': t.current_price,
                            'quantity': t.quantity,
                            'pnl': t.pnl,
                            'pnl_percent': t.pnl_percent,
                            'delta': t.entry_delta,
                            'gamma': t.entry_gamma,
                            'theta': t.entry_theta,
                            'iv': t.entry_iv,
                            'status': t.status
                        }
                        for t in self.active_trades
                    ]
                },
                'portfolio': {
                    'delta': round(self.portfolio_greeks['delta'], 2),
                    'gamma': round(self.portfolio_greeks['gamma'], 4),
                    'theta': round(self.portfolio_greeks['theta'], 2),
                    'vega': round(self.portfolio_greeks['vega'], 2),
                    'daily_pnl': round(self.daily_pnl, 2),
                    'daily_trades': self.daily_trades,
                    'risk_used_percent': round(self.account_risk_used * 100, 1)
                },
                'market': {
                    'ltp': self.current_ltp,
                    'greeks': self.greeks_data
                }
            }

    def get_heatmap_snapshot(self, underlying: str) -> Dict:
        """Build a strike ladder heatmap from available Greeks snapshots"""
        with self.lock:
            rows: Dict[int, Dict] = {}
            for symbol, data in self.greeks_data.items():
                strike, opt_type = self._extract_strike_and_type(symbol, data)
                if strike is None or opt_type is None:
                    continue
                row = rows.setdefault(strike, {'strike': strike, 'ce': None, 'pe': None})
                entry = {
                    'symbol': symbol,
                    'ltp': data.get('ltp', 0),
                    'delta': data.get('delta', 0),
                    'gamma': data.get('gamma', 0),
                    'theta': data.get('theta', 0),
                    'vega': data.get('vega', 0),
                    'iv': data.get('iv', 0),
                    'oi': data.get('oi', 0),
                    'timestamp': data.get('timestamp')
                }
                if opt_type == 'CE':
                    row['ce'] = entry
                else:
                    row['pe'] = entry
            ladder = [rows[k] for k in sorted(rows.keys())]
            return {
                'underlying': underlying,
                'timestamp': datetime.now().isoformat(),
                'rows': ladder
            }

    @staticmethod
    def _extract_strike_and_type(symbol: str, data: Dict) -> tuple:
        """Best-effort extraction of strike and option type"""
        if not symbol and data:
            symbol = data.get('symbol')
        if not symbol:
            return None, None
        match = re.search(r"(\d{4,6})(CE|PE)", symbol.upper())
        if match:
            return int(match.group(1)), match.group(2)
        # Fallback: allow explicit strike/type fields if present
        strike = data.get('strike') if isinstance(data, dict) else None
        opt_type = data.get('option_type') if isinstance(data, dict) else None
        if strike and opt_type:
            return int(strike), str(opt_type).upper()
        return None, None


# Global dashboard provider
dashboard_provider = DashboardDataProvider()


@app.route('/api/dashboard', methods=['GET'])
def get_dashboard():
    """Get current dashboard data"""
    return jsonify(dashboard_provider.get_dashboard_data())


@app.route('/api/positions', methods=['GET'])
def get_positions():
    """Get active positions with Greeks"""
    data = dashboard_provider.get_dashboard_data()
    return jsonify(data['positions'])


@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio Greeks and risk metrics"""
    data = dashboard_provider.get_dashboard_data()
    return jsonify(data['portfolio'])


@app.route('/api/market', methods=['GET'])
def get_market():
    """Get market data (LTP, Greeks)"""
    data = dashboard_provider.get_dashboard_data()
    return jsonify(data['market'])


@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get session performance metrics"""
    with dashboard_provider.lock:
        total_trades = len(dashboard_provider.closed_trades)
        wins = sum(1 for t in dashboard_provider.closed_trades if t.pnl > 0)
        losses = sum(1 for t in dashboard_provider.closed_trades if t.pnl < 0)
        win_rate = (wins / total_trades * 100) if total_trades > 0 else 0
        avg_win = sum(t.pnl for t in dashboard_provider.closed_trades if t.pnl > 0) / max(wins, 1)
        avg_loss = sum(t.pnl for t in dashboard_provider.closed_trades if t.pnl < 0) / max(losses, 1)
        
        return jsonify({
            'total_trades': total_trades,
            'wins': wins,
            'losses': losses,
            'win_rate': round(win_rate, 1),
            'daily_pnl': round(dashboard_provider.daily_pnl, 2),
            'avg_win': round(avg_win, 2),
            'avg_loss': round(avg_loss, 2),
            'profit_factor': round(sum(t.pnl for t in dashboard_provider.closed_trades if t.pnl > 0) / 
                                  abs(sum(t.pnl for t in dashboard_provider.closed_trades if t.pnl < 0)) 
                                  if sum(t.pnl for t in dashboard_provider.closed_trades if t.pnl < 0) != 0 else 0, 2)
        })


@app.route('/api/trades', methods=['GET'])
def get_trades():
    """Get closed trades history"""
    limit = request.args.get('limit', 50, type=int)
    
    with dashboard_provider.lock:
        trades = dashboard_provider.closed_trades[-limit:]
        return jsonify({
            'total': len(dashboard_provider.closed_trades),
            'trades': [
                {
                    'id': t.trade_id,
                    'underlying': getattr(t, 'underlying', 'NIFTY'),
                    'strike': t.strike,
                    'option_type': t.option_type,
                    'entry_price': t.entry_price,
                    'exit_price': getattr(t, 'exit_price', t.current_price),
                    'entry_time': t.entry_time.isoformat() if hasattr(t.entry_time, 'isoformat') else str(t.entry_time),
                    'exit_time': t.exit_time.isoformat() if t.exit_time and hasattr(t.exit_time, 'isoformat') else str(t.exit_time),
                    'duration_sec': int((t.exit_time - t.entry_time).total_seconds()) if t.exit_time else 0,
                    'pnl': round(t.pnl, 2),
                    'pnl_percent': round(t.pnl_percent, 2),
                    'exit_reason': t.exit_reason,
                    'entry_delta': round(t.entry_delta, 2),
                    'exit_delta': round(getattr(t, 'exit_delta', 0), 2)
                }
                for t in trades
            ]
        })


@app.route('/api/greeks-heatmap', methods=['GET'])
def get_greeks_heatmap():
    """Get Greeks heatmap data for strike ladder"""
    underlying = request.args.get('underlying', 'NIFTY')
    heatmap = dashboard_provider.get_heatmap_snapshot(underlying)
    return jsonify(heatmap)


@app.route('/', methods=['GET'])
@app.route('/dashboard', methods=['GET'])
def serve_dashboard():
    """Serve dashboard UI if available, otherwise link to API endpoints"""
    if _DASHBOARD_FILE.exists():
        return send_from_directory(_DASHBOARD_DIR, 'dashboard.html')
    return jsonify({
        'message': 'ANGEL-X Dashboard API',
        'endpoints': [
            '/api/dashboard',
            '/api/positions',
            '/api/portfolio',
            '/api/market',
            '/api/greeks-heatmap',
            '/api/performance',
            '/api/trades',
            '/health'
        ]
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


def start_dashboard(port: int = 5000, debug: bool = False):
    """Start dashboard server"""
    logger.info(f"Starting ANGEL-X Dashboard on http://localhost:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)


if __name__ == '__main__':
    start_dashboard()
