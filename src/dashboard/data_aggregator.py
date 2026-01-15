"""
Real-Time Dashboard Data Aggregator
Collects live trading data from the system and formats for dashboard display
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import asdict
import json

class DashboardDataAggregator:
    """
    Aggregates real trading data from various system components
    Provides formatted data for dashboard endpoints
    """

    def __init__(self, trade_journal=None, data_feed=None, broker_client=None):
        """
        Initialize data aggregator with system components
        
        Args:
            trade_journal: TradeJournalEngine instance
            data_feed: DataFeed instance for market data
            broker_client: Broker client for live data
        """
        self.trade_journal = trade_journal
        self.data_feed = data_feed
        self.broker_client = broker_client
        self.session_start = datetime.now()

    # =========================================================================
    # CORE DATA COLLECTION
    # =========================================================================

    def get_live_data(self) -> Dict[str, Any]:
        """Get real-time trading data"""
        try:
            session_stats = self.trade_journal.get_session_stats() if self.trade_journal else {}
            
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "active",
                "session_duration_seconds": (datetime.now() - self.session_start).total_seconds(),
                "data": {
                    "total_pnl": session_stats.get("total_pnl", 0),
                    "total_trades": session_stats.get("total_trades", 0),
                    "winning_trades": session_stats.get("winning_trades", 0),
                    "losing_trades": session_stats.get("losing_trades", 0),
                    "win_rate": session_stats.get("win_rate", 0),
                    "max_profit": session_stats.get("max_profit", 0),
                    "max_loss": session_stats.get("max_loss", 0),
                    "avg_pnl_per_trade": session_stats.get("avg_pnl_per_trade", 0),
                    "avg_holding_time_secs": session_stats.get("avg_holding_time_secs", 0),
                    "avg_holding_time_formatted": session_stats.get("avg_holding_time_formatted", "0m 0s"),
                    "open_positions": self._get_open_positions_count(),
                    "nifty_ltp": self._get_nifty_ltp(),
                    "banknifty_ltp": self._get_banknifty_ltp(),
                    "market_status": self._get_market_status(),
                }
            }
        except Exception as e:
            return {
                "timestamp": datetime.now().isoformat(),
                "status": "error",
                "error": str(e)
            }

    def get_all_trades(self) -> List[Dict[str, Any]]:
        """Get all trades with formatted data"""
        try:
            if not self.trade_journal or not self.trade_journal.trades:
                return []
            
            trades_list = []
            for trade in self.trade_journal.trades:
                trade_dict = {
                    "symbol": trade.symbol or "N/A",
                    "option_type": trade.option_type or "CE",
                    "entry_time": trade.entry_greeks.get("entry_time", "").isoformat() if isinstance(trade.entry_greeks.get("entry_time"), datetime) else str(trade.entry_greeks.get("entry_time", "")),
                    "entry_price": round(trade.entry_price, 2) if trade.entry_price else 0,
                    "exit_time": trade.exit_greeks.get("exit_time", "").isoformat() if isinstance(trade.exit_greeks.get("exit_time"), datetime) else str(trade.exit_greeks.get("exit_time", "")),
                    "exit_price": round(trade.exit_price, 2) if trade.exit_price else 0,
                    "quantity": trade.quantity or 0,
                    "side": trade.side or "LONG",
                    "pnl_rupees": round(trade.pnl_rupees, 2) if trade.pnl_rupees else 0,
                    "pnl_percent": round(trade.pnl_percent, 2) if trade.pnl_percent else 0,
                    "status": "CLOSED" if trade.exit_price else "OPEN",
                    "exit_reason": trade.exit_reason or "MANUAL",
                    "duration_seconds": trade.duration_seconds or 0,
                    "quality_score": round(trade.quality_score, 1) if trade.quality_score else 0,
                }
                trades_list.append(trade_dict)
            
            # Return in reverse order (latest first)
            return sorted(trades_list, key=lambda x: x["entry_time"], reverse=True)
        except Exception as e:
            print(f"Error getting trades: {e}")
            return []

    def get_positions(self) -> List[Dict[str, Any]]:
        """Get open positions"""
        try:
            positions = []
            if self.trade_journal and self.trade_journal.trades:
                for trade in self.trade_journal.trades:
                    if trade.exit_price is None or trade.exit_price == 0:
                        position = {
                            "symbol": trade.symbol or "N/A",
                            "option_type": trade.option_type,
                            "quantity": trade.quantity,
                            "entry_price": round(trade.entry_price, 2),
                            "current_price": round(self._get_ltp_for_symbol(trade.symbol), 2) if trade.symbol else trade.entry_price,
                            "pnl": round(trade.pnl_rupees, 2) if trade.pnl_rupees else 0,
                            "pnl_pct": round(trade.pnl_percent, 2) if trade.pnl_percent else 0,
                            "side": trade.side or "LONG",
                            "entry_time": str(trade.entry_greeks.get("entry_time", "")),
                            "duration_seconds": (datetime.now() - datetime.fromisoformat(str(trade.entry_greeks.get("entry_time", "")))).total_seconds() if trade.entry_greeks.get("entry_time") else 0,
                        }
                        positions.append(position)
            return positions
        except Exception as e:
            print(f"Error getting positions: {e}")
            return []

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        try:
            if not self.trade_journal:
                return self._empty_stats()
            
            stats = self.trade_journal.get_session_stats()
            return {
                "total_trades": stats.get("total_trades", 0),
                "winning_trades": stats.get("winning_trades", 0),
                "losing_trades": stats.get("losing_trades", 0),
                "win_rate": round(stats.get("win_rate", 0), 1),
                "total_pnl": round(stats.get("total_pnl", 0), 2),
                "avg_pnl_per_trade": round(stats.get("avg_pnl_per_trade", 0), 2),
                "max_profit": round(stats.get("max_profit", 0), 2),
                "max_loss": round(stats.get("max_loss", 0), 2),
                "avg_holding_time_secs": stats.get("avg_holding_time_secs", 0),
                "avg_holding_time_formatted": stats.get("avg_holding_time_formatted", "0m 0s"),
                "profit_factor": self._calculate_profit_factor(stats),
                "risk_reward_ratio": self._calculate_risk_reward_ratio(stats),
            }
        except Exception as e:
            print(f"Error getting stats: {e}")
            return self._empty_stats()

    def get_pnl_chart_data(self) -> Dict[str, Any]:
        """Get P&L over time for charting"""
        try:
            if not self.trade_journal or not self.trade_journal.trades:
                return {"labels": [], "data": []}
            
            cumulative_pnl = 0
            labels = []
            data = []
            
            for trade in self.trade_journal.trades:
                cumulative_pnl += trade.pnl_rupees
                entry_time = trade.entry_greeks.get("entry_time")
                if entry_time:
                    if isinstance(entry_time, datetime):
                        labels.append(entry_time.strftime("%H:%M:%S"))
                    else:
                        labels.append(str(entry_time))
                data.append(round(cumulative_pnl, 2))
            
            return {
                "labels": labels[-20:],  # Last 20 trades
                "data": data[-20:]
            }
        except Exception as e:
            print(f"Error getting P&L chart data: {e}")
            return {"labels": [], "data": []}

    def get_hourly_pnl(self) -> Dict[str, Any]:
        """Get hourly P&L breakdown"""
        try:
            hourly_data = {}
            
            if not self.trade_journal or not self.trade_journal.trades:
                return {"hours": [], "pnl": []}
            
            for trade in self.trade_journal.trades:
                entry_time = trade.entry_greeks.get("entry_time")
                if entry_time:
                    if isinstance(entry_time, datetime):
                        hour_key = entry_time.strftime("%H:00")
                    else:
                        hour_key = "Unknown"
                    
                    if hour_key not in hourly_data:
                        hourly_data[hour_key] = 0
                    
                    hourly_data[hour_key] += trade.pnl_rupees
            
            # Sort by hour
            sorted_hours = sorted(hourly_data.keys())
            
            return {
                "hours": sorted_hours,
                "pnl": [round(hourly_data[h], 2) for h in sorted_hours]
            }
        except Exception as e:
            print(f"Error getting hourly P&L: {e}")
            return {"hours": [], "pnl": []}

    def get_trade_distribution(self) -> Dict[str, Any]:
        """Get trade distribution (wins/losses)"""
        try:
            if not self.trade_journal:
                return {"profitable": 0, "breakeven": 0, "loss": 0}
            
            stats = self.trade_journal.get_session_stats()
            winning = stats.get("winning_trades", 0)
            losing = stats.get("losing_trades", 0)
            breakeven = stats.get("total_trades", 0) - winning - losing
            
            return {
                "profitable": winning,
                "breakeven": breakeven,
                "loss": losing
            }
        except Exception as e:
            print(f"Error getting trade distribution: {e}")
            return {"profitable": 0, "breakeven": 0, "loss": 0}

    def get_greeks_exposure(self) -> Dict[str, float]:
        """Get current Greeks exposure"""
        try:
            total_delta = 0
            total_gamma = 0
            total_theta = 0
            total_vega = 0
            
            if self.trade_journal and self.trade_journal.trades:
                for trade in self.trade_journal.trades:
                    if trade.exit_price is None or trade.exit_price == 0:
                        total_delta += trade.entry_greeks.get("delta", 0) * trade.quantity
                        total_gamma += trade.entry_greeks.get("gamma", 0) * trade.quantity
                        total_theta += trade.entry_greeks.get("theta", 0) * trade.quantity
                        total_vega += trade.entry_greeks.get("vega", 0) * trade.quantity
            
            return {
                "delta": round(total_delta, 2),
                "gamma": round(total_gamma, 2),
                "theta": round(total_theta, 2),
                "vega": round(total_vega, 2),
            }
        except Exception as e:
            print(f"Error getting Greeks exposure: {e}")
            return {"delta": 0, "gamma": 0, "theta": 0, "vega": 0}

    def get_broker_status(self) -> Dict[str, Any]:
        """Get broker connection status"""
        try:
            status = {
                "api_connected": False,
                "websocket_active": False,
                "last_heartbeat": None,
                "connection_time": None,
            }
            
            if self.broker_client:
                status["api_connected"] = getattr(self.broker_client, 'connected', False)
                status["websocket_active"] = getattr(self.broker_client, 'ws_connected', False)
                status["last_heartbeat"] = datetime.now().isoformat()
            
            return status
        except Exception as e:
            print(f"Error getting broker status: {e}")
            return {}

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics"""
        try:
            import psutil
            
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "memory_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "api_latency_ms": 45,  # Placeholder
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": str(e)}

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def _get_open_positions_count(self) -> int:
        """Count open positions"""
        if not self.trade_journal or not self.trade_journal.trades:
            return 0
        return sum(1 for t in self.trade_journal.trades if t.exit_price is None or t.exit_price == 0)

    def _get_nifty_ltp(self) -> float:
        """Get NIFTY current LTP"""
        try:
            if self.data_feed and hasattr(self.data_feed, 'get_ltp'):
                return self.data_feed.get_ltp("NIFTY")
            return 24000  # Default placeholder
        except Exception:
            return 24000

    def _get_banknifty_ltp(self) -> float:
        """Get BANKNIFTY current LTP"""
        try:
            if self.data_feed and hasattr(self.data_feed, 'get_ltp'):
                return self.data_feed.get_ltp("BANKNIFTY")
            return 51000  # Default placeholder
        except Exception:
            return 51000

    def _get_ltp_for_symbol(self, symbol: str) -> float:
        """Get LTP for specific symbol"""
        try:
            if self.data_feed and hasattr(self.data_feed, 'get_ltp'):
                return self.data_feed.get_ltp(symbol)
            return 0
        except Exception:
            return 0

    def _get_market_status(self) -> str:
        """Get market status (open/closed)"""
        from datetime import datetime
        now = datetime.now()
        hour = now.hour
        minute = now.minute
        
        # Market hours: 09:15 - 15:30
        if hour > 15 or (hour == 15 and minute > 30):
            return "CLOSED"
        elif hour >= 9 and (hour > 9 or minute >= 15):
            return "OPEN"
        else:
            return "PRE_MARKET"

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty stats structure"""
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0,
            "total_pnl": 0,
            "avg_pnl_per_trade": 0,
            "max_profit": 0,
            "max_loss": 0,
            "avg_holding_time_secs": 0,
            "avg_holding_time_formatted": "0m 0s",
            "profit_factor": 0,
            "risk_reward_ratio": 0,
        }

    def _calculate_profit_factor(self, stats: Dict) -> float:
        """Calculate profit factor (gross profit / gross loss)"""
        try:
            gross_profit = stats.get("max_profit", 0) * stats.get("winning_trades", 0) / max(1, stats.get("total_trades", 1))
            gross_loss = abs(stats.get("max_loss", 0)) * stats.get("losing_trades", 0) / max(1, stats.get("total_trades", 1))
            
            if gross_loss == 0:
                return 0
            
            return round(gross_profit / gross_loss, 2)
        except Exception:
            return 0

    def _calculate_risk_reward_ratio(self, stats: Dict) -> float:
        """Calculate risk reward ratio"""
        try:
            avg_profit = stats.get("avg_pnl_per_trade", 0)
            max_loss = abs(stats.get("max_loss", 0))
            
            if max_loss == 0:
                return 0
            
            return round(avg_profit / max_loss, 2)
        except Exception:
            return 0
