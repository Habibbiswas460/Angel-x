"""
ANGEL-X Integration Hub
Connects all modules and provides unified initialization
"""

import logging
from typing import Optional
from threading import Thread

# Import all components
from config import config
from src.utils.logger import StrategyLogger
from src.dashboard.dashboard_backend import DashboardDataProvider, dashboard_provider, start_dashboard
from src.analytics.trade_journal_analytics import TradeJournalAnalytics
from src.engines.smart_exit_engine import SmartExitEngine, ExitConfiguration

logger = StrategyLogger.get_logger(__name__)


class AngelXIntegration:
    """
    Central integration hub for all ANGEL-X systems:
    - Dashboard (web UI + real-time data)
    - Analytics (trade journal insights)
    - Smart exits (trailing stops, profit laddering)
    - Risk management
    """
    
    def __init__(self):
        logger.info("=" * 80)
        logger.info("ANGEL-X INTEGRATION HUB INITIALIZATION")
        logger.info("=" * 80)
        
        # Initialize dashboard provider
        self.dashboard = dashboard_provider
        logger.info("✓ Dashboard data provider initialized (shared with API)")
        
        # Initialize smart exit engine
        exit_config = ExitConfiguration(
            use_trailing_stop=getattr(config, 'USE_TRAILING_STOP', True),
            trailing_stop_percent=getattr(config, 'TRAILING_STOP_PERCENT', 2.0),
            use_profit_ladder=getattr(config, 'USE_PROFIT_LADDER', True),
            max_hold_time_seconds=getattr(config, 'MAX_HOLD_TIME', 600)
        )
        self.smart_exit = SmartExitEngine(exit_config)
        logger.info("✓ Smart exit engine initialized")
        
        # Initialize analytics
        self.analytics = TradeJournalAnalytics()
        logger.info("✓ Trade journal analytics initialized")
        
        # Dashboard server thread (if enabled)
        self.dashboard_thread = None
        if getattr(config, 'DASHBOARD_ENABLED', True):
            self._start_dashboard_server()
        
        logger.info("=" * 80)
        logger.info("ANGEL-X INTEGRATION HUB READY")
        logger.info("=" * 80)
    
    def _start_dashboard_server(self):
        """Start dashboard server in background thread"""
        dashboard_port = getattr(config, 'DASHBOARD_PORT', 5000)
        
        def run_dashboard():
            try:
                start_dashboard(port=dashboard_port, debug=False)
            except Exception as e:
                logger.error(f"Dashboard server error: {e}")
        
        self.dashboard_thread = Thread(target=run_dashboard, daemon=True)
        self.dashboard_thread.start()
        logger.info(f"✓ Dashboard server started on http://localhost:{dashboard_port}")
    
    def update_position_data(self, trade_manager, greeks_manager):
        """Sync live position data to dashboard"""
        try:
            # Update active trades
            active_trades = trade_manager.get_active_trades()
            self.dashboard.set_active_trades(active_trades)
            
            # Update closed trades
            closed_trades = trade_manager.get_closed_trades()
            self.dashboard.set_closed_trades(closed_trades)
            
            # Update daily P&L
            stats = trade_manager.get_trade_statistics()
            self.dashboard.set_daily_pnl(stats.get('total_pnl', 0), stats.get('total', 0))
            
            # Update Greeks for all tracked symbols
            if hasattr(greeks_manager, 'get_all_tracked'):
                for symbol in greeks_manager.get_all_tracked():
                    greeks = greeks_manager.get_greeks(symbol)
                    if greeks:
                        self.dashboard.update_greeks(symbol, {
                            'symbol': symbol,
                            'delta': greeks.delta,
                            'gamma': greeks.gamma,
                            'theta': greeks.theta,
                            'vega': greeks.vega,
                            'iv': greeks.iv,
                            'ltp': greeks.ltp,
                            'oi': greeks.oi
                        })
        
        except Exception as e:
            logger.error(f"Error updating position data: {e}")
    
    def get_analytics_report(self) -> str:
        """Generate comprehensive analytics report"""
        try:
            report_file = self.analytics.export_analytics_report()
            logger.info(f"Analytics report generated: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"Error generating analytics report: {e}")
            return None
    
    def get_performance_metrics(self) -> dict:
        """Get current performance metrics"""
        try:
            summary = self.analytics.get_summary_report()
            entry_analysis = self.analytics.get_entry_analysis()
            exit_analysis = self.analytics.get_exit_analysis()
            
            return {
                'summary': summary,
                'best_entries': sorted(entry_analysis.items(), 
                                      key=lambda x: x[1]['win_rate'], reverse=True)[:5],
                'best_exits': sorted(exit_analysis.items(),
                                    key=lambda x: x[1]['total_pnl'], reverse=True)[:5]
            }
        except Exception as e:
            logger.error(f"Error getting performance metrics: {e}")
            return None
    
    def shutdown(self):
        """Gracefully shutdown all components"""
        logger.info("ANGEL-X Integration Hub shutting down...")
        # Thread will auto-shutdown as daemon
        logger.info("✓ All components shut down")


# Global integration hub
_integration_hub = None


def get_integration_hub() -> AngelXIntegration:
    """Get or create the global integration hub"""
    global _integration_hub
    if _integration_hub is None:
        _integration_hub = AngelXIntegration()
    return _integration_hub
