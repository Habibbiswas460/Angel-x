"""
PHASE 9 - PART A: Live Dashboard Components
Real-time monitoring during market hours
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, time as dt_time
from enum import Enum
import json


class MarketStatus(Enum):
    """Market operational status"""

    PRE_OPEN = "pre_open"
    OPEN = "open"
    PAUSED = "paused"
    LOCKED = "locked"
    CLOSED = "closed"


class TradeAllowance(Enum):
    """Trade permission status"""

    ALLOWED = "allowed"
    BLOCKED = "blocked"
    CAUTIOUS = "cautious"


@dataclass
class MarketOverview:
    """
    9.1 - Market Overview Panel
    Quick context at a glance
    """

    timestamp: datetime
    nifty_spot: float
    nifty_future: float
    current_expiry: str
    market_status: MarketStatus
    days_to_expiry: int
    spot_change_pct: float

    def to_dict(self) -> Dict:
        data = asdict(self)
        data["market_status"] = self.market_status.value
        data["timestamp"] = self.timestamp.isoformat()
        return data

    def get_display_summary(self) -> str:
        """Human-readable summary"""
        status_icon = {
            MarketStatus.OPEN: "🟢",
            MarketStatus.PAUSED: "🟡",
            MarketStatus.LOCKED: "🔴",
            MarketStatus.PRE_OPEN: "🔵",
            MarketStatus.CLOSED: "⚫",
        }

        icon = status_icon.get(self.market_status, "⚪")

        return f"""
{icon} NIFTY: {self.nifty_spot:.2f} ({self.spot_change_pct:+.2f}%)
Future: {self.nifty_future:.2f}
Expiry: {self.current_expiry} ({self.days_to_expiry}D)
Status: {self.market_status.value.upper()}
"""


@dataclass
class OptionStrikeData:
    """Single strike data for option chain"""

    strike: int
    ce_ltp: float
    pe_ltp: float
    ce_oi: int
    pe_oi: int
    ce_oi_delta: int
    pe_oi_delta: int
    ce_volume: int
    pe_volume: int
    ce_delta: float
    pe_delta: float
    ce_gamma: float
    pe_gamma: float
    ce_theta: float
    pe_theta: float

    def get_dominant_side(self) -> str:
        """Identify which side has more activity"""
        ce_strength = abs(self.ce_oi_delta) + (self.ce_volume / 10)
        pe_strength = abs(self.pe_oi_delta) + (self.pe_volume / 10)

        if ce_strength > pe_strength * 1.5:
            return "CE_DOMINANT"
        elif pe_strength > ce_strength * 1.5:
            return "PE_DOMINANT"
        else:
            return "BALANCED"


@dataclass
class OptionChainView:
    """
    9.2 - Option Chain Intelligence View
    ATM ±5 strikes with smart money indicators
    """

    timestamp: datetime
    atm_strike: int
    strikes: List[OptionStrikeData]

    def get_dominant_strikes(self) -> Dict[str, List[int]]:
        """Find strikes with dominant activity"""
        ce_dominant = []
        pe_dominant = []

        for strike_data in self.strikes:
            side = strike_data.get_dominant_side()
            if side == "CE_DOMINANT":
                ce_dominant.append(strike_data.strike)
            elif side == "PE_DOMINANT":
                pe_dominant.append(strike_data.strike)

        return {"ce_dominant_strikes": ce_dominant, "pe_dominant_strikes": pe_dominant}

    def get_max_oi_buildup(self) -> Dict:
        """Find strikes with maximum OI buildup"""
        if not self.strikes:
            return {}

        max_ce_buildup = max(self.strikes, key=lambda s: s.ce_oi_delta)
        max_pe_buildup = max(self.strikes, key=lambda s: s.pe_oi_delta)

        return {
            "max_ce_buildup": {
                "strike": max_ce_buildup.strike,
                "oi_delta": max_ce_buildup.ce_oi_delta,
                "volume": max_ce_buildup.ce_volume,
            },
            "max_pe_buildup": {
                "strike": max_pe_buildup.strike,
                "oi_delta": max_pe_buildup.pe_oi_delta,
                "volume": max_pe_buildup.pe_volume,
            },
        }

    def to_table_format(self) -> str:
        """Format as readable table"""
        table = "\n" + "=" * 100 + "\n"
        table += f"ATM: {self.atm_strike} | Time: {self.timestamp.strftime('%H:%M:%S')}\n"
        table += "=" * 100 + "\n"
        table += f"{'Strike':<8} | {'CE LTP':<8} | {'CE OI':<10} | {'CE ΔOI':<10} | {'PE ΔOI':<10} | {'PE OI':<10} | {'PE LTP':<8} | {'Side':<12}\n"
        table += "-" * 100 + "\n"

        for strike_data in sorted(self.strikes, key=lambda s: s.strike):
            side = strike_data.get_dominant_side()
            side_icon = "📈" if side == "CE_DOMINANT" else ("📉" if side == "PE_DOMINANT" else "⚖️")

            table += f"{strike_data.strike:<8} | "
            table += f"{strike_data.ce_ltp:<8.2f} | "
            table += f"{strike_data.ce_oi:<10} | "
            table += f"{strike_data.ce_oi_delta:+<10} | "
            table += f"{strike_data.pe_oi_delta:+<10} | "
            table += f"{strike_data.pe_oi:<10} | "
            table += f"{strike_data.pe_ltp:<8.2f} | "
            table += f"{side_icon} {side:<10}\n"

        table += "=" * 100 + "\n"
        return table


@dataclass
class BiasEligibilityPanel:
    """
    9.3 - Bias & Eligibility Panel
    Why trade is allowed or blocked
    """

    timestamp: datetime
    market_bias: str  # BULLISH, BEARISH, NEUTRAL
    bias_strength: float  # 0.0 - 1.0
    bias_confidence: str  # LOW, MEDIUM, HIGH

    trade_allowed: TradeAllowance
    block_reasons: List[str]

    # Contributing factors
    oi_bias_score: float
    volume_bias_score: float
    greeks_bias_score: float
    price_action_score: float

    def get_bias_grade(self) -> str:
        """Convert bias strength to grade"""
        if self.bias_strength >= 0.8:
            return "VERY_HIGH"
        elif self.bias_strength >= 0.65:
            return "HIGH"
        elif self.bias_strength >= 0.5:
            return "MEDIUM"
        elif self.bias_strength >= 0.35:
            return "LOW"
        else:
            return "VERY_LOW"

    def get_trade_decision_summary(self) -> Dict:
        """Complete decision breakdown"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "bias": self.market_bias,
            "bias_strength": self.bias_strength,
            "bias_grade": self.get_bias_grade(),
            "trade_allowed": self.trade_allowed.value,
            "block_reasons": self.block_reasons if self.block_reasons else ["None - Trade allowed"],
            "contributing_factors": {
                "oi_bias": self.oi_bias_score,
                "volume_bias": self.volume_bias_score,
                "greeks_bias": self.greeks_bias_score,
                "price_action": self.price_action_score,
            },
        }

    def get_visual_display(self) -> str:
        """Terminal-friendly display"""
        allowed_icon = (
            "✅"
            if self.trade_allowed == TradeAllowance.ALLOWED
            else ("⚠️" if self.trade_allowed == TradeAllowance.CAUTIOUS else "❌")
        )

        bias_icon = "🐂" if self.market_bias == "BULLISH" else ("🐻" if self.market_bias == "BEARISH" else "🦀")

        display = f"""
╔══════════════════════════════════════════════════════════╗
║           BIAS & ELIGIBILITY PANEL                       ║
╚══════════════════════════════════════════════════════════╝

{bias_icon} Market Bias: {self.market_bias}
   Strength: {self.bias_strength:.2f} ({self.get_bias_grade()})
   Confidence: {self.bias_confidence}

{allowed_icon} Trade Status: {self.trade_allowed.value.upper()}
"""

        if self.block_reasons:
            display += "\n⚠️  Block Reasons:\n"
            for reason in self.block_reasons:
                display += f"   • {reason}\n"

        display += f"""
📊 Contributing Factors:
   OI Bias:        {self.oi_bias_score:.2f}
   Volume Bias:    {self.volume_bias_score:.2f}
   Greeks Bias:    {self.greeks_bias_score:.2f}
   Price Action:   {self.price_action_score:.2f}

Updated: {self.timestamp.strftime('%H:%M:%S')}
"""
        return display


@dataclass
class LiveTradeMonitor:
    """
    9.4 - Live Trade Monitor
    Active position tracking
    """

    timestamp: datetime
    has_position: bool

    # Position details (if has_position)
    symbol: Optional[str] = None
    option_type: Optional[str] = None  # CE / PE
    strike: Optional[int] = None
    entry_price: Optional[float] = None
    current_price: Optional[float] = None
    quantity: Optional[int] = None

    # Risk management
    stop_loss: Optional[float] = None
    trailing_sl: Optional[float] = None
    target_price: Optional[float] = None

    # Live Greeks
    current_delta: Optional[float] = None
    current_theta: Optional[float] = None
    current_gamma: Optional[float] = None
    entry_delta: Optional[float] = None
    delta_change: Optional[float] = None

    # Exit triggers
    theta_exit_ready: bool = False
    reversal_exit_ready: bool = False
    time_exit_ready: bool = False

    # PnL
    unrealized_pnl: Optional[float] = None
    pnl_percentage: Optional[float] = None

    def get_position_summary(self) -> Dict:
        """Position details"""
        if not self.has_position:
            return {"status": "NO_POSITION"}

        return {
            "symbol": self.symbol,
            "type": self.option_type,
            "strike": self.strike,
            "entry": self.entry_price,
            "current": self.current_price,
            "quantity": self.quantity,
            "sl": self.stop_loss,
            "trailing_sl": self.trailing_sl,
            "target": self.target_price,
            "pnl": self.unrealized_pnl,
            "pnl_pct": self.pnl_percentage,
        }

    def get_greeks_summary(self) -> Dict:
        """Greeks tracking"""
        if not self.has_position:
            return {}

        return {
            "current_delta": self.current_delta,
            "entry_delta": self.entry_delta,
            "delta_change": self.delta_change,
            "theta": self.current_theta,
            "gamma": self.current_gamma,
        }

    def get_exit_triggers(self) -> Dict:
        """Exit readiness status"""
        return {
            "theta_exit": self.theta_exit_ready,
            "reversal_exit": self.reversal_exit_ready,
            "time_exit": self.time_exit_ready,
        }

    def get_visual_display(self) -> str:
        """Terminal display"""
        if not self.has_position:
            return "\n📭 NO ACTIVE POSITION\n"

        pnl_icon = "🟢" if self.unrealized_pnl and self.unrealized_pnl > 0 else "🔴"

        display = f"""
╔══════════════════════════════════════════════════════════╗
║              LIVE TRADE MONITOR                          ║
╚══════════════════════════════════════════════════════════╝

📍 Position: {self.symbol} {self.strike} {self.option_type}
   Quantity: {self.quantity} lots

💰 Prices:
   Entry:   ₹{self.entry_price:.2f}
   Current: ₹{self.current_price:.2f}
   SL:      ₹{self.stop_loss:.2f}
   Trail:   ₹{self.trailing_sl:.2f}
   Target:  ₹{self.target_price:.2f}

{pnl_icon} PnL: ₹{self.unrealized_pnl:+.2f} ({self.pnl_percentage:+.2f}%)

📊 Live Greeks:
   Delta: {self.current_delta:.3f} (Entry: {self.entry_delta:.3f}, Δ: {self.delta_change:+.3f})
   Theta: {self.current_theta:.2f}
   Gamma: {self.current_gamma:.3f}

🚪 Exit Triggers:
   Theta Exit:    {'🟢 READY' if self.theta_exit_ready else '⚪ Pending'}
   Reversal Exit: {'🟢 READY' if self.reversal_exit_ready else '⚪ Pending'}
   Time Exit:     {'🟢 READY' if self.time_exit_ready else '⚪ Pending'}

Updated: {self.timestamp.strftime('%H:%M:%S')}
"""
        return display


@dataclass
class RiskSafetyPanel:
    """
    9.5 - Risk & Safety Panel
    Capital protection metrics
    """

    timestamp: datetime

    # Daily limits
    trades_taken_today: int
    max_trades_allowed: int
    daily_pnl: float
    max_loss_limit: float
    loss_remaining: float

    # Position limits
    current_exposure: float
    max_exposure_allowed: float

    # Safety status
    cooldown_active: bool

    # Consecutive tracking
    consecutive_wins: int
    consecutive_losses: int

    # Risk state
    current_risk_pct: float
    drawdown_pct: float

    # Optional fields (must come after required fields)
    cooldown_reason: Optional[str] = None
    cooldown_until: Optional[datetime] = None

    def is_at_risk_limit(self) -> bool:
        """Check if approaching limits"""
        return (
            self.trades_taken_today >= self.max_trades_allowed
            or self.daily_pnl <= -self.max_loss_limit
            or self.drawdown_pct >= 15.0
            or self.consecutive_losses >= 2
        )

    def get_safety_status(self) -> str:
        """Overall safety assessment"""
        if self.cooldown_active:
            return "PAUSED"
        elif self.is_at_risk_limit():
            return "CRITICAL"
        elif self.drawdown_pct > 10 or self.consecutive_losses >= 1:
            return "CAUTIOUS"
        else:
            return "HEALTHY"

    def get_visual_display(self) -> str:
        """Terminal display"""
        status = self.get_safety_status()
        status_icon = {"HEALTHY": "🟢", "CAUTIOUS": "🟡", "CRITICAL": "🔴", "PAUSED": "🔵"}.get(status, "⚪")

        pnl_icon = "🟢" if self.daily_pnl >= 0 else "🔴"

        display = f"""
╔══════════════════════════════════════════════════════════╗
║            RISK & SAFETY PANEL                           ║
╚══════════════════════════════════════════════════════════╝

{status_icon} System Status: {status}

📊 Daily Metrics:
   Trades: {self.trades_taken_today} / {self.max_trades_allowed}
   {pnl_icon} PnL: ₹{self.daily_pnl:+,.2f}
   Max Loss: ₹{self.max_loss_limit:,.2f}
   Remaining: ₹{self.loss_remaining:,.2f}

💼 Exposure:
   Current: ₹{self.current_exposure:,.2f}
   Max Allowed: ₹{self.max_exposure_allowed:,.2f}
   Usage: {(self.current_exposure/self.max_exposure_allowed*100):.1f}%

📈 Performance:
   Consecutive Wins: {self.consecutive_wins}
   Consecutive Losses: {self.consecutive_losses}
   Current Risk: {self.current_risk_pct:.2f}%
   Drawdown: {self.drawdown_pct:.2f}%
"""

        if self.cooldown_active:
            display += f"""
⏸️  COOLDOWN ACTIVE
   Reason: {self.cooldown_reason}
   Until: {self.cooldown_until.strftime('%H:%M:%S') if self.cooldown_until else 'N/A'}
"""

        display += f"""
🛑 [KILL SWITCH] - Emergency Stop Available

Updated: {self.timestamp.strftime('%H:%M:%S')}
"""
        return display


class LiveDashboard:
    """
    Master Live Dashboard
    Aggregates all live panels
    """

    def __init__(self):
        self.market_overview: Optional[MarketOverview] = None
        self.option_chain: Optional[OptionChainView] = None
        self.bias_panel: Optional[BiasEligibilityPanel] = None
        self.trade_monitor: Optional[LiveTradeMonitor] = None
        self.risk_panel: Optional[RiskSafetyPanel] = None

        self.last_update: Optional[datetime] = None

    def update_all(
        self,
        market_overview: MarketOverview,
        option_chain: OptionChainView,
        bias_panel: BiasEligibilityPanel,
        trade_monitor: LiveTradeMonitor,
        risk_panel: RiskSafetyPanel,
    ):
        """Update all panels"""
        self.market_overview = market_overview
        self.option_chain = option_chain
        self.bias_panel = bias_panel
        self.trade_monitor = trade_monitor
        self.risk_panel = risk_panel
        self.last_update = datetime.now()

    def get_complete_snapshot(self) -> Dict:
        """Get complete dashboard state"""
        return {
            "timestamp": self.last_update.isoformat() if self.last_update else None,
            "market_overview": self.market_overview.to_dict() if self.market_overview else None,
            "option_chain_summary": self.option_chain.get_dominant_strikes() if self.option_chain else None,
            "bias_decision": self.bias_panel.get_trade_decision_summary() if self.bias_panel else None,
            "position": self.trade_monitor.get_position_summary() if self.trade_monitor else None,
            "risk_status": (
                {
                    "status": self.risk_panel.get_safety_status() if self.risk_panel else None,
                    "daily_pnl": self.risk_panel.daily_pnl if self.risk_panel else 0,
                    "at_risk": self.risk_panel.is_at_risk_limit() if self.risk_panel else False,
                }
                if self.risk_panel
                else None
            ),
        }

    def render_terminal_dashboard(self) -> str:
        """Complete terminal view"""
        output = "\n" + "=" * 100 + "\n"
        output += "🎯 ANGEL-X COMMAND CENTER - LIVE DASHBOARD\n"
        output += "=" * 100 + "\n"

        if self.market_overview:
            output += self.market_overview.get_display_summary()

        if self.bias_panel:
            output += self.bias_panel.get_visual_display()

        if self.trade_monitor:
            output += self.trade_monitor.get_visual_display()

        if self.risk_panel:
            output += self.risk_panel.get_visual_display()

        if self.option_chain:
            output += "\n📊 OPTION CHAIN INTELLIGENCE:\n"
            output += self.option_chain.to_table_format()

        output += "\n" + "=" * 100 + "\n"
        output += f"Last Update: {self.last_update.strftime('%Y-%m-%d %H:%M:%S') if self.last_update else 'Never'}\n"
        output += "=" * 100 + "\n"

        return output

    def save_snapshot(self, filepath: str):
        """Save dashboard state to JSON"""
        snapshot = self.get_complete_snapshot()
        with open(filepath, "w") as f:
            json.dump(snapshot, f, indent=2)

    def should_alert(self) -> Tuple[bool, List[str]]:
        """Check if any alerts needed"""
        alerts = []

        if self.risk_panel:
            if self.risk_panel.get_safety_status() == "CRITICAL":
                alerts.append("🚨 CRITICAL: Risk limits reached")

            if self.risk_panel.cooldown_active:
                alerts.append(f"⏸️  Trading paused: {self.risk_panel.cooldown_reason}")

            if self.risk_panel.consecutive_losses >= 2:
                alerts.append(f"⚠️  {self.risk_panel.consecutive_losses} consecutive losses")

        if self.bias_panel:
            if self.bias_panel.trade_allowed == TradeAllowance.BLOCKED:
                alerts.append(f"🛑 Trading blocked: {', '.join(self.bias_panel.block_reasons)}")

        if self.trade_monitor and self.trade_monitor.has_position:
            if self.trade_monitor.theta_exit_ready:
                alerts.append("🚪 Theta exit signal ready")
            if self.trade_monitor.reversal_exit_ready:
                alerts.append("🔄 Reversal exit signal ready")

        return len(alerts) > 0, alerts
