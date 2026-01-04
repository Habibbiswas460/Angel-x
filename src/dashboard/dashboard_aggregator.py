"""
PHASE 9: Dashboard Data Aggregator
Connects Phase 1-8 engines to dashboard
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass

from src.dashboard.live_dashboard import (
    LiveDashboard, MarketOverview, OptionChainView, OptionStrikeData,
    BiasEligibilityPanel, LiveTradeMonitor, RiskSafetyPanel,
    MarketStatus, TradeAllowance
)
from src.dashboard.post_trade_analytics import (
    PostTradeAnalytics, CompletedTrade, ExitReason
)

# NOTE: Import existing engines when integrating with Phase 1-8
# from src.engines.market_bias.engine import MarketBiasEngine
# from src.engines.entry.engine import EntrySignalEngine
# from src.core.greeks_engine import GreeksEngine
# from src.core.risk_calibration import RiskCalibrationSystem
# from src.core.adaptive_strictness import AdaptiveStrictnessEngine
# from src.core.metrics_tracker import PerformanceTracker


class DashboardAggregator:
    """
    Aggregates data from all Phase 1-8 components
    Feeds both Live and Post-Trade dashboards
    """
    
    def __init__(self):
        # Dashboards
        self.live_dashboard = LiveDashboard()
        self.post_analytics = PostTradeAnalytics()
        
        # Phase 1-8 engines (will be injected when integrating)
        self.bias_engine: Optional[Any] = None
        self.entry_engine: Optional[Any] = None
        self.greeks_engine: Optional[Any] = None
        self.risk_system: Optional[Any] = None
        self.strictness_engine: Optional[Any] = None
        self.metrics_tracker: Optional[Any] = None
        
        # Current state cache
        self.current_market_data: Dict = {}
        self.current_option_chain: Dict = {}
        self.active_position: Optional[Dict] = None
    
    def connect_engines(self,
                       bias_engine=None,
                       entry_engine=None,
                       greeks_engine=None,
                       risk_system=None,
                       strictness_engine=None,
                       metrics_tracker=None):
        """Connect Phase 1-8 engines"""
        self.bias_engine = bias_engine
        self.entry_engine = entry_engine
        self.greeks_engine = greeks_engine
        self.risk_system = risk_system
        self.strictness_engine = strictness_engine
        self.metrics_tracker = metrics_tracker
    
    def update_market_data(self, market_data: Dict):
        """Update with latest market tick"""
        self.current_market_data = market_data
    
    def update_option_chain(self, option_chain: Dict):
        """Update with latest option chain"""
        self.current_option_chain = option_chain
    
    def update_active_position(self, position: Optional[Dict]):
        """Update current position"""
        self.active_position = position
    
    def build_market_overview(self) -> MarketOverview:
        """Build Market Overview Panel from current data"""
        spot = self.current_market_data.get('nifty_spot', 0.0)
        future = self.current_market_data.get('nifty_future', 0.0)
        expiry = self.current_market_data.get('expiry', 'UNKNOWN')
        days_to_expiry = self.current_market_data.get('days_to_expiry', 0)
        spot_change = self.current_market_data.get('spot_change_pct', 0.0)
        
        # Determine market status
        now = datetime.now().time()
        from datetime import time as dt_time
        
        if dt_time(9, 0) <= now < dt_time(9, 15):
            status = MarketStatus.PRE_OPEN
        elif dt_time(9, 15) <= now < dt_time(15, 30):
            status = MarketStatus.OPEN
        else:
            status = MarketStatus.CLOSED
        
        return MarketOverview(
            timestamp=datetime.now(),
            nifty_spot=spot,
            nifty_future=future,
            current_expiry=expiry,
            market_status=status,
            days_to_expiry=days_to_expiry,
            spot_change_pct=spot_change
        )
    
    def build_option_chain_view(self) -> OptionChainView:
        """Build Option Chain Intelligence View"""
        atm_strike = self.current_option_chain.get('atm_strike', 18000)
        strikes_data = self.current_option_chain.get('strikes', [])
        
        option_strikes = []
        for strike_info in strikes_data:
            strike_data = OptionStrikeData(
                strike=strike_info.get('strike', 0),
                ce_ltp=strike_info.get('ce_ltp', 0.0),
                pe_ltp=strike_info.get('pe_ltp', 0.0),
                ce_oi=strike_info.get('ce_oi', 0),
                pe_oi=strike_info.get('pe_oi', 0),
                ce_oi_delta=strike_info.get('ce_oi_delta', 0),
                pe_oi_delta=strike_info.get('pe_oi_delta', 0),
                ce_volume=strike_info.get('ce_volume', 0),
                pe_volume=strike_info.get('pe_volume', 0),
                ce_delta=strike_info.get('ce_delta', 0.0),
                pe_delta=strike_info.get('pe_delta', 0.0),
                ce_gamma=strike_info.get('ce_gamma', 0.0),
                pe_gamma=strike_info.get('pe_gamma', 0.0),
                ce_theta=strike_info.get('ce_theta', 0.0),
                pe_theta=strike_info.get('pe_theta', 0.0)
            )
            option_strikes.append(strike_data)
        
        return OptionChainView(
            timestamp=datetime.now(),
            atm_strike=atm_strike,
            strikes=option_strikes
        )
    
    def build_bias_panel(self) -> BiasEligibilityPanel:
        """Build Bias & Eligibility Panel"""
        # Get bias from bias engine
        if self.bias_engine:
            bias_result = self.bias_engine.get_current_bias()
            market_bias = bias_result.get('bias', 'NEUTRAL')
            bias_strength = bias_result.get('strength', 0.0)
            bias_confidence = bias_result.get('confidence', 'MEDIUM')
            oi_score = bias_result.get('oi_score', 0.0)
            volume_score = bias_result.get('volume_score', 0.0)
            greeks_score = bias_result.get('greeks_score', 0.0)
            price_score = bias_result.get('price_score', 0.0)
        else:
            # Mock data
            market_bias = "NEUTRAL"
            bias_strength = 0.5
            bias_confidence = "MEDIUM"
            oi_score = 0.5
            volume_score = 0.5
            greeks_score = 0.5
            price_score = 0.5
        
        # Get trade allowance from strictness engine
        if self.strictness_engine:
            conditions = self.strictness_engine.evaluate_trading_conditions(
                current_iv=self.current_market_data.get('iv', 25.0),
                recent_pnl=self.current_market_data.get('daily_pnl', 0)
            )
            can_trade = conditions.get('can_trade', True)
            block_reasons = conditions.get('pause_reasons', [])
        else:
            can_trade = True
            block_reasons = []
        
        trade_allowed = TradeAllowance.ALLOWED if can_trade else TradeAllowance.BLOCKED
        
        return BiasEligibilityPanel(
            timestamp=datetime.now(),
            market_bias=market_bias,
            bias_strength=bias_strength,
            bias_confidence=bias_confidence,
            trade_allowed=trade_allowed,
            block_reasons=block_reasons,
            oi_bias_score=oi_score,
            volume_bias_score=volume_score,
            greeks_bias_score=greeks_score,
            price_action_score=price_score
        )
    
    def build_trade_monitor(self) -> LiveTradeMonitor:
        """Build Live Trade Monitor"""
        if not self.active_position:
            return LiveTradeMonitor(
                timestamp=datetime.now(),
                has_position=False
            )
        
        # Extract position details
        return LiveTradeMonitor(
            timestamp=datetime.now(),
            has_position=True,
            symbol=self.active_position.get('symbol'),
            option_type=self.active_position.get('option_type'),
            strike=self.active_position.get('strike'),
            entry_price=self.active_position.get('entry_price'),
            current_price=self.active_position.get('current_price'),
            quantity=self.active_position.get('quantity'),
            stop_loss=self.active_position.get('stop_loss'),
            trailing_sl=self.active_position.get('trailing_sl'),
            target_price=self.active_position.get('target'),
            current_delta=self.active_position.get('current_delta'),
            current_theta=self.active_position.get('current_theta'),
            current_gamma=self.active_position.get('current_gamma'),
            entry_delta=self.active_position.get('entry_delta'),
            delta_change=self.active_position.get('delta_change'),
            theta_exit_ready=self.active_position.get('theta_exit_ready', False),
            reversal_exit_ready=self.active_position.get('reversal_exit_ready', False),
            time_exit_ready=self.active_position.get('time_exit_ready', False),
            unrealized_pnl=self.active_position.get('pnl'),
            pnl_percentage=self.active_position.get('pnl_pct')
        )
    
    def build_risk_panel(self) -> RiskSafetyPanel:
        """Build Risk & Safety Panel"""
        # Get data from risk system
        if self.risk_system:
            risk_state = self.risk_system.get_current_state()
        else:
            risk_state = {}
        
        # Get strictness engine data
        if self.strictness_engine:
            risk_adjuster = self.strictness_engine.risk_adjuster
            consecutive_wins = risk_adjuster.get_consecutive_wins()
            consecutive_losses = risk_adjuster.get_consecutive_losses()
            current_risk_pct = risk_adjuster.get_adjusted_risk_pct()
        else:
            consecutive_wins = 0
            consecutive_losses = 0
            current_risk_pct = 2.0
        
        return RiskSafetyPanel(
            timestamp=datetime.now(),
            trades_taken_today=risk_state.get('trades_today', 0),
            max_trades_allowed=risk_state.get('max_trades', 5),
            daily_pnl=risk_state.get('daily_pnl', 0.0),
            max_loss_limit=risk_state.get('max_loss', 10000.0),
            loss_remaining=risk_state.get('loss_remaining', 10000.0),
            current_exposure=risk_state.get('exposure', 0.0),
            max_exposure_allowed=risk_state.get('max_exposure', 50000.0),
            cooldown_active=risk_state.get('cooldown', False),
            cooldown_reason=risk_state.get('cooldown_reason'),
            cooldown_until=risk_state.get('cooldown_until'),
            consecutive_wins=consecutive_wins,
            consecutive_losses=consecutive_losses,
            current_risk_pct=current_risk_pct,
            drawdown_pct=risk_state.get('drawdown_pct', 0.0)
        )
    
    def refresh_live_dashboard(self):
        """Refresh all live dashboard panels"""
        market_overview = self.build_market_overview()
        option_chain = self.build_option_chain_view()
        bias_panel = self.build_bias_panel()
        trade_monitor = self.build_trade_monitor()
        risk_panel = self.build_risk_panel()
        
        self.live_dashboard.update_all(
            market_overview=market_overview,
            option_chain=option_chain,
            bias_panel=bias_panel,
            trade_monitor=trade_monitor,
            risk_panel=risk_panel
        )
    
    def get_live_dashboard_snapshot(self) -> Dict:
        """Get current live dashboard state"""
        return self.live_dashboard.get_complete_snapshot()
    
    def render_live_dashboard(self) -> str:
        """Render live dashboard for terminal"""
        return self.live_dashboard.render_terminal_dashboard()
    
    def check_alerts(self) -> tuple:
        """Check for any alerts"""
        return self.live_dashboard.should_alert()
    
    def load_completed_trades(self, trades: List[CompletedTrade]):
        """Load trades for post-trade analytics"""
        self.post_analytics.load_trades(trades)
    
    def run_post_trade_analysis(self, period: str = "DAY") -> str:
        """Run and get post-trade analytics report"""
        self.post_analytics.run_full_analysis(period=period)
        return self.post_analytics.generate_complete_report()
    
    def save_live_snapshot(self, filepath: str):
        """Save live dashboard snapshot"""
        self.live_dashboard.save_snapshot(filepath)
    
    def save_analytics_report(self, filepath: str):
        """Save post-trade analytics report"""
        self.post_analytics.save_report(filepath)


class DashboardDataFeeder:
    """
    Helper to feed sample/mock data to dashboard
    Useful for testing and development
    """
    
    @staticmethod
    def get_sample_market_data() -> Dict:
        """Sample market data"""
        return {
            'nifty_spot': 19542.75,
            'nifty_future': 19565.50,
            'expiry': '25-JAN-2024',
            'days_to_expiry': 3,
            'spot_change_pct': 0.45,
            'iv': 16.5,
            'daily_pnl': 350.0
        }
    
    @staticmethod
    def get_sample_option_chain() -> Dict:
        """Sample option chain"""
        atm = 19500
        strikes_data = []
        
        for offset in range(-5, 6):  # ATM ±5
            strike = atm + (offset * 100)
            strikes_data.append({
                'strike': strike,
                'ce_ltp': max(10, 200 - abs(offset) * 30),
                'pe_ltp': max(10, 200 - abs(offset) * 30),
                'ce_oi': 50000 + (offset * 5000 if offset > 0 else 0),
                'pe_oi': 50000 + (abs(offset) * 5000 if offset < 0 else 0),
                'ce_oi_delta': 2000 if offset > 0 else -500,
                'pe_oi_delta': 2000 if offset < 0 else -500,
                'ce_volume': 15000 + abs(offset) * 2000,
                'pe_volume': 15000 + abs(offset) * 2000,
                'ce_delta': 0.5 + (offset * 0.08),
                'pe_delta': -0.5 - (offset * 0.08),
                'ce_gamma': 0.05,
                'pe_gamma': 0.05,
                'ce_theta': -45,
                'pe_theta': -45
            })
        
        return {
            'atm_strike': atm,
            'strikes': strikes_data
        }
    
    @staticmethod
    def get_sample_position() -> Dict:
        """Sample active position"""
        return {
            'symbol': 'NIFTY',
            'option_type': 'CE',
            'strike': 19500,
            'entry_price': 185.50,
            'current_price': 195.25,
            'quantity': 2,
            'stop_loss': 170.00,
            'trailing_sl': 180.00,
            'target': 210.00,
            'current_delta': 0.58,
            'current_theta': -42,
            'current_gamma': 0.048,
            'entry_delta': 0.52,
            'delta_change': 0.06,
            'theta_exit_ready': False,
            'reversal_exit_ready': False,
            'time_exit_ready': False,
            'pnl': 487.50,
            'pnl_pct': 5.25
        }
    
    @staticmethod
    def get_sample_completed_trades() -> List[CompletedTrade]:
        """Sample completed trades for analytics"""
        trades = []
        
        # Sample trade data
        trade_configs = [
            (True, ExitReason.TARGET, "MORNING", "HIGH", 850),
            (True, ExitReason.THETA_DECAY, "AFTERNOON", "MEDIUM", 320),
            (False, ExitReason.STOP_LOSS, "OPENING", "LOW", -250),
            (True, ExitReason.TARGET, "MORNING", "HIGH", 920),
            (False, ExitReason.REVERSAL, "LUNCH", "MEDIUM", -180),
            (True, ExitReason.THETA_DECAY, "AFTERNOON", "HIGH", 450),
            (True, ExitReason.TARGET, "MORNING", "HIGH", 780),
            (False, ExitReason.STOP_LOSS, "CLOSING", "LOW", -320),
        ]
        
        for i, (won, exit_reason, session, oi_conv, pnl) in enumerate(trade_configs):
            entry_time = datetime.now().replace(hour=10, minute=15) - timedelta(days=i)
            exit_time = entry_time + timedelta(minutes=25)
            
            trade = CompletedTrade(
                trade_id=f"T{i+1:03d}",
                timestamp=entry_time,
                symbol="NIFTY",
                option_type="CE" if i % 2 == 0 else "PE",
                strike=19500,
                entry_price=180.0,
                exit_price=180.0 + (pnl / 50),  # Approx
                entry_time=entry_time,
                exit_time=exit_time,
                holding_minutes=25,
                pnl=pnl,
                pnl_percentage=(pnl / 9000) * 100,
                won=won,
                exit_reason=exit_reason,
                entry_delta=0.52,
                entry_theta=-48,
                entry_gamma=0.05,
                entry_bias="BULLISH" if i % 2 == 0 else "BEARISH",
                bias_strength=0.75,
                oi_conviction=oi_conv,
                volume_conviction="HIGH",
                session=session
            )
            trades.append(trade)
        
        return trades
