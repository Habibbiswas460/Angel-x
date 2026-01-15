"""
PHASE 9 - PART B: Post-Trade Analytics Components
Learning from completed trades
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
import statistics
import json


class ExitReason(Enum):
    """Trade exit classification"""

    THETA_DECAY = "theta_decay"
    REVERSAL = "reversal"
    STOP_LOSS = "stop_loss"
    TARGET = "target"
    TIME_EXIT = "time_exit"
    EXHAUSTION = "exhaustion"
    MANUAL = "manual"


@dataclass
class CompletedTrade:
    """Single trade record for analytics"""

    trade_id: str
    timestamp: datetime
    symbol: str
    option_type: str  # CE / PE
    strike: int

    # Entry/Exit
    entry_price: float
    exit_price: float
    entry_time: datetime
    exit_time: datetime
    holding_minutes: int

    # PnL
    pnl: float
    pnl_percentage: float
    won: bool

    # Exit classification
    exit_reason: ExitReason

    # Greeks
    entry_delta: float
    entry_theta: float
    entry_gamma: float
    exit_delta: Optional[float] = None

    # Market context
    entry_bias: str = "NEUTRAL"
    bias_strength: float = 0.0
    oi_conviction: str = "MEDIUM"
    volume_conviction: str = "MEDIUM"

    # Session
    session: str = "UNKNOWN"


@dataclass
class PnLAnalytics:
    """
    9.6 - PnL Analytics
    Survival scorecard
    """

    period: str  # DAY, WEEK, MONTH
    start_date: datetime
    end_date: datetime

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    total_pnl: float = 0.0
    winning_pnl: float = 0.0
    losing_pnl: float = 0.0

    avg_win: float = 0.0
    avg_loss: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0

    win_rate: float = 0.0
    avg_rr: float = 0.0  # Risk:Reward

    # Drawdown tracking
    peak_pnl: float = 0.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0

    # Streak tracking
    current_streak: int = 0
    longest_winning_streak: int = 0
    longest_losing_streak: int = 0

    def calculate_metrics(self, trades: List[CompletedTrade]):
        """Calculate all PnL metrics"""
        if not trades:
            return

        self.total_trades = len(trades)
        winning = [t for t in trades if t.won]
        losing = [t for t in trades if not t.won]

        self.winning_trades = len(winning)
        self.losing_trades = len(losing)

        self.winning_pnl = sum(t.pnl for t in winning)
        self.losing_pnl = sum(t.pnl for t in losing)
        self.total_pnl = self.winning_pnl + self.losing_pnl

        if winning:
            self.avg_win = self.winning_pnl / len(winning)
            self.largest_win = max(t.pnl for t in winning)

        if losing:
            self.avg_loss = self.losing_pnl / len(losing)
            self.largest_loss = min(t.pnl for t in losing)

        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100

        if self.avg_loss != 0:
            self.avg_rr = abs(self.avg_win / self.avg_loss)

        # Calculate drawdown
        self._calculate_drawdown(trades)

        # Calculate streaks
        self._calculate_streaks(trades)

    def _calculate_drawdown(self, trades: List[CompletedTrade]):
        """Calculate drawdown curve"""
        running_pnl = 0.0
        peak = 0.0
        max_dd = 0.0

        for trade in sorted(trades, key=lambda t: t.timestamp):
            running_pnl += trade.pnl

            if running_pnl > peak:
                peak = running_pnl

            drawdown = peak - running_pnl
            if drawdown > max_dd:
                max_dd = drawdown

        self.peak_pnl = peak
        self.max_drawdown = max_dd
        self.current_drawdown = peak - running_pnl

    def _calculate_streaks(self, trades: List[CompletedTrade]):
        """Calculate winning/losing streaks"""
        if not trades:
            return

        current = 0
        max_win = 0
        max_loss = 0

        for trade in sorted(trades, key=lambda t: t.timestamp):
            if trade.won:
                current = current + 1 if current > 0 else 1
                max_win = max(max_win, current)
            else:
                current = current - 1 if current < 0 else -1
                max_loss = max(max_loss, abs(current))

        self.current_streak = current
        self.longest_winning_streak = max_win
        self.longest_losing_streak = max_loss

    def get_summary_report(self) -> str:
        """Human-readable summary"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║              PnL ANALYTICS - {self.period}                      
╚══════════════════════════════════════════════════════════╝

Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}

📊 Overview:
   Total Trades: {self.total_trades}
   Win Rate: {self.win_rate:.1f}%
   Total PnL: ₹{self.total_pnl:+,.2f}

💰 Win/Loss Breakdown:
   Winning Trades: {self.winning_trades} (₹{self.winning_pnl:+,.2f})
   Losing Trades: {self.losing_trades} (₹{self.losing_pnl:+,.2f})
   
   Avg Win: ₹{self.avg_win:,.2f}
   Avg Loss: ₹{self.avg_loss:,.2f}
   Avg R:R: {self.avg_rr:.2f}

🏆 Best/Worst:
   Largest Win: ₹{self.largest_win:+,.2f}
   Largest Loss: ₹{self.largest_loss:+,.2f}

📉 Drawdown:
   Peak PnL: ₹{self.peak_pnl:,.2f}
   Max Drawdown: ₹{self.max_drawdown:,.2f}
   Current DD: ₹{self.current_drawdown:,.2f}

🔥 Streaks:
   Current: {self.current_streak:+d}
   Longest Win Streak: {self.longest_winning_streak}
   Longest Loss Streak: {self.longest_losing_streak}
"""


@dataclass
class ExitReasonAnalysis:
    """
    9.7 - Exit Reason Analysis
    Which exit strategy works best
    """

    exit_reason: ExitReason
    trade_count: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_pnl: float = 0.0
    avg_holding_time: float = 0.0

    def calculate_from_trades(self, trades: List[CompletedTrade]):
        """Calculate metrics for this exit reason"""
        filtered = [t for t in trades if t.exit_reason == self.exit_reason]

        if not filtered:
            return

        self.trade_count = len(filtered)
        self.winning_trades = sum(1 for t in filtered if t.won)
        self.losing_trades = sum(1 for t in filtered if not t.won)

        self.total_pnl = sum(t.pnl for t in filtered)
        self.win_rate = (self.winning_trades / self.trade_count) * 100 if self.trade_count > 0 else 0
        self.avg_pnl = self.total_pnl / self.trade_count if self.trade_count > 0 else 0
        self.avg_holding_time = statistics.mean([t.holding_minutes for t in filtered]) if filtered else 0


class ExitReasonReport:
    """Complete exit reason breakdown"""

    def __init__(self):
        self.analyses: Dict[ExitReason, ExitReasonAnalysis] = {}

    def analyze_all_exits(self, trades: List[CompletedTrade]):
        """Analyze all exit reasons"""
        for reason in ExitReason:
            analysis = ExitReasonAnalysis(exit_reason=reason)
            analysis.calculate_from_trades(trades)
            if analysis.trade_count > 0:
                self.analyses[reason] = analysis

    def get_best_exit_strategy(self) -> Optional[ExitReasonAnalysis]:
        """Find most profitable exit"""
        if not self.analyses:
            return None

        return max(self.analyses.values(), key=lambda a: a.win_rate)

    def get_worst_exit_strategy(self) -> Optional[ExitReasonAnalysis]:
        """Find least profitable exit"""
        if not self.analyses:
            return None

        return min(self.analyses.values(), key=lambda a: a.win_rate)

    def get_summary_report(self) -> str:
        """Formatted report"""
        report = """
╔══════════════════════════════════════════════════════════╗
║           EXIT REASON ANALYSIS                           ║
╚══════════════════════════════════════════════════════════╝

"""

        if not self.analyses:
            return report + "No data available\n"

        # Sort by win rate
        sorted_analyses = sorted(self.analyses.values(), key=lambda a: a.win_rate, reverse=True)

        report += f"{'Exit Reason':<20} | {'Trades':<8} | {'Win%':<8} | {'Avg PnL':<12} | {'Avg Time':<10}\n"
        report += "-" * 80 + "\n"

        for analysis in sorted_analyses:
            report += f"{analysis.exit_reason.value:<20} | "
            report += f"{analysis.trade_count:<8} | "
            report += f"{analysis.win_rate:<8.1f} | "
            report += f"₹{analysis.avg_pnl:<11,.2f} | "
            report += f"{analysis.avg_holding_time:<10.1f}m\n"

        best = self.get_best_exit_strategy()
        worst = self.get_worst_exit_strategy()

        report += "\n"
        if best:
            report += f"🏆 Best Strategy: {best.exit_reason.value} ({best.win_rate:.1f}% win rate)\n"
        if worst:
            report += f"⚠️  Worst Strategy: {worst.exit_reason.value} ({worst.win_rate:.1f}% win rate)\n"

        return report


@dataclass
class GreeksAccuracyMetrics:
    """
    9.8 - Greeks Accuracy Report
    How well Greeks predictions worked
    """

    greek_name: str  # DELTA, GAMMA, THETA

    total_predictions: int = 0
    accurate_predictions: int = 0
    accuracy_pct: float = 0.0

    # For delta
    avg_delta_entry: float = 0.0
    profitable_high_delta_pct: float = 0.0  # High delta (>0.5) profitability

    # For theta
    theta_exit_win_rate: float = 0.0
    avg_theta_decay_realized: float = 0.0

    # For gamma
    gamma_spike_success_pct: float = 0.0  # High gamma + big move = profit


class GreeksAccuracyReport:
    """Complete Greeks performance analysis"""

    def __init__(self):
        self.delta_metrics = GreeksAccuracyMetrics(greek_name="DELTA")
        self.theta_metrics = GreeksAccuracyMetrics(greek_name="THETA")
        self.gamma_metrics = GreeksAccuracyMetrics(greek_name="GAMMA")

    def analyze_greeks(self, trades: List[CompletedTrade]):
        """Analyze Greeks accuracy"""
        if not trades:
            return

        # Delta analysis
        high_delta_trades = [t for t in trades if abs(t.entry_delta) > 0.5]
        if high_delta_trades:
            high_delta_wins = sum(1 for t in high_delta_trades if t.won)
            self.delta_metrics.profitable_high_delta_pct = (high_delta_wins / len(high_delta_trades)) * 100
            self.delta_metrics.avg_delta_entry = statistics.mean([abs(t.entry_delta) for t in trades])

        # Theta analysis
        theta_exits = [t for t in trades if t.exit_reason == ExitReason.THETA_DECAY]
        if theta_exits:
            theta_wins = sum(1 for t in theta_exits if t.won)
            self.theta_metrics.theta_exit_win_rate = (theta_wins / len(theta_exits)) * 100
            self.theta_metrics.total_predictions = len(theta_exits)
            self.theta_metrics.accurate_predictions = theta_wins

        # Gamma analysis (high gamma + quick profit)
        high_gamma_trades = [t for t in trades if abs(t.entry_gamma) > 0.05 and t.holding_minutes < 30]
        if high_gamma_trades:
            gamma_wins = sum(1 for t in high_gamma_trades if t.won)
            self.gamma_metrics.gamma_spike_success_pct = (gamma_wins / len(high_gamma_trades)) * 100

    def get_summary_report(self) -> str:
        """Formatted Greeks report"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║          GREEKS ACCURACY REPORT                          ║
╚══════════════════════════════════════════════════════════╝

📊 DELTA Performance:
   Avg Entry Delta: {self.delta_metrics.avg_delta_entry:.3f}
   High Delta (>0.5) Win Rate: {self.delta_metrics.profitable_high_delta_pct:.1f}%

⏱️  THETA Performance:
   Theta Exit Trades: {self.theta_metrics.total_predictions}
   Theta Exit Win Rate: {self.theta_metrics.theta_exit_win_rate:.1f}%

⚡ GAMMA Performance:
   High Gamma Quick Trades: {len([1])} 
   Gamma Spike Success: {self.gamma_metrics.gamma_spike_success_pct:.1f}%

💡 Insight: {'✅ Greeks working well' if self.theta_metrics.theta_exit_win_rate > 60 else '⚠️ Greeks need tuning'}
"""


@dataclass
class OIVolumeConvictionReport:
    """
    9.9 - OI + Volume Conviction Analysis
    Smart money detector accuracy
    """

    high_oi_trades: int = 0
    high_oi_wins: int = 0
    high_oi_win_rate: float = 0.0
    high_oi_avg_pnl: float = 0.0

    medium_oi_trades: int = 0
    medium_oi_win_rate: float = 0.0

    low_oi_trades: int = 0
    low_oi_win_rate: float = 0.0

    volume_fakeout_losses: int = 0
    volume_fakeout_pct: float = 0.0

    ce_dominant_accuracy: float = 0.0
    pe_dominant_accuracy: float = 0.0

    def analyze_conviction(self, trades: List[CompletedTrade]):
        """Analyze OI/volume conviction"""
        if not trades:
            return

        # High OI conviction
        high_oi = [t for t in trades if t.oi_conviction == "HIGH"]
        if high_oi:
            self.high_oi_trades = len(high_oi)
            self.high_oi_wins = sum(1 for t in high_oi if t.won)
            self.high_oi_win_rate = (self.high_oi_wins / self.high_oi_trades) * 100
            self.high_oi_avg_pnl = statistics.mean([t.pnl for t in high_oi])

        # Medium OI
        medium_oi = [t for t in trades if t.oi_conviction == "MEDIUM"]
        if medium_oi:
            self.medium_oi_trades = len(medium_oi)
            medium_wins = sum(1 for t in medium_oi if t.won)
            self.medium_oi_win_rate = (medium_wins / self.medium_oi_trades) * 100

        # Low OI
        low_oi = [t for t in trades if t.oi_conviction == "LOW"]
        if low_oi:
            self.low_oi_trades = len(low_oi)
            low_wins = sum(1 for t in low_oi if t.won)
            self.low_oi_win_rate = (low_wins / self.low_oi_trades) * 100

        # Volume fakeouts (high volume but loss)
        high_vol_losses = [t for t in trades if t.volume_conviction == "HIGH" and not t.won]
        self.volume_fakeout_losses = len(high_vol_losses)
        if trades:
            self.volume_fakeout_pct = (self.volume_fakeout_losses / len(trades)) * 100

    def get_summary_report(self) -> str:
        """Formatted conviction report"""
        return f"""
╔══════════════════════════════════════════════════════════╗
║       OI + VOLUME CONVICTION REPORT                      ║
╚══════════════════════════════════════════════════════════╝

📊 OI Conviction Performance:

   HIGH Conviction:
      Trades: {self.high_oi_trades}
      Win Rate: {self.high_oi_win_rate:.1f}%
      Avg PnL: ₹{self.high_oi_avg_pnl:+,.2f}
   
   MEDIUM Conviction:
      Trades: {self.medium_oi_trades}
      Win Rate: {self.medium_oi_win_rate:.1f}%
   
   LOW Conviction:
      Trades: {self.low_oi_trades}
      Win Rate: {self.low_oi_win_rate:.1f}%

⚠️  Volume Fakeouts:
   Losses on High Volume: {self.volume_fakeout_losses}
   Fakeout Rate: {self.volume_fakeout_pct:.1f}%

💡 Insight: {'✅ HIGH OI conviction working' if self.high_oi_win_rate > 70 else '⚠️ OI conviction needs review'}
"""


@dataclass
class TimeOfDayPerformance:
    """
    9.10 - Time-of-Day Performance
    Best trading windows
    """

    session_name: str
    start_time: str
    end_time: str

    trades: int = 0
    wins: int = 0
    win_rate: float = 0.0
    total_pnl: float = 0.0
    avg_pnl: float = 0.0

    def calculate_from_trades(self, trades: List[CompletedTrade]):
        """Calculate session metrics"""
        session_trades = [t for t in trades if t.session == self.session_name]

        if not session_trades:
            return

        self.trades = len(session_trades)
        self.wins = sum(1 for t in session_trades if t.won)
        self.win_rate = (self.wins / self.trades) * 100 if self.trades > 0 else 0
        self.total_pnl = sum(t.pnl for t in session_trades)
        self.avg_pnl = self.total_pnl / self.trades if self.trades > 0 else 0


class TimeOfDayReport:
    """Complete time-based performance analysis"""

    def __init__(self):
        self.sessions = [
            TimeOfDayPerformance("OPENING", "9:15", "10:00"),
            TimeOfDayPerformance("MORNING", "10:00", "11:30"),
            TimeOfDayPerformance("LUNCH", "11:30", "14:00"),
            TimeOfDayPerformance("AFTERNOON", "14:00", "15:00"),
            TimeOfDayPerformance("CLOSING", "15:00", "15:30"),
        ]

    def analyze_sessions(self, trades: List[CompletedTrade]):
        """Analyze all sessions"""
        for session in self.sessions:
            session.calculate_from_trades(trades)

    def get_best_session(self) -> Optional[TimeOfDayPerformance]:
        """Find most profitable session"""
        profitable = [s for s in self.sessions if s.trades > 0]
        if not profitable:
            return None
        return max(profitable, key=lambda s: s.win_rate)

    def get_worst_session(self) -> Optional[TimeOfDayPerformance]:
        """Find least profitable session"""
        profitable = [s for s in self.sessions if s.trades > 0]
        if not profitable:
            return None
        return min(profitable, key=lambda s: s.win_rate)

    def get_summary_report(self) -> str:
        """Formatted time report"""
        report = """
╔══════════════════════════════════════════════════════════╗
║        TIME-OF-DAY PERFORMANCE                           ║
╚══════════════════════════════════════════════════════════╝

"""

        report += f"{'Session':<15} | {'Time':<15} | {'Trades':<8} | {'Win%':<8} | {'Avg PnL':<12}\n"
        report += "-" * 80 + "\n"

        for session in self.sessions:
            if session.trades > 0:
                report += f"{session.session_name:<15} | "
                report += f"{session.start_time}-{session.end_time:<6} | "
                report += f"{session.trades:<8} | "
                report += f"{session.win_rate:<8.1f} | "
                report += f"₹{session.avg_pnl:<11,.2f}\n"

        best = self.get_best_session()
        worst = self.get_worst_session()

        report += "\n"
        if best:
            report += f"🏆 Best Window: {best.session_name} ({best.win_rate:.1f}% win rate)\n"
        if worst:
            report += f"⚠️  Worst Window: {worst.session_name} ({worst.win_rate:.1f}% win rate)\n"

        report += "\n💡 Recommendation: "
        if best and best.win_rate > 65:
            report += f"Focus on {best.session_name} trades"
        else:
            report += "No clear best window - review strategy"

        return report


class PostTradeAnalytics:
    """
    Master Post-Trade Analytics Engine
    Combines all analytics components
    """

    def __init__(self):
        self.pnl_analytics = None
        self.exit_reason_report = ExitReasonReport()
        self.greeks_accuracy = GreeksAccuracyReport()
        self.oi_conviction_report = OIVolumeConvictionReport()
        self.time_of_day_report = TimeOfDayReport()

        self.all_trades: List[CompletedTrade] = []

    def load_trades(self, trades: List[CompletedTrade]):
        """Load trades for analysis"""
        self.all_trades = trades

    def run_full_analysis(self, period: str = "DAY"):
        """Run complete analytics"""
        if not self.all_trades:
            print("No trades to analyze")
            return

        # PnL Analytics
        start = min(t.timestamp for t in self.all_trades)
        end = max(t.timestamp for t in self.all_trades)
        self.pnl_analytics = PnLAnalytics(period=period, start_date=start, end_date=end)
        self.pnl_analytics.calculate_metrics(self.all_trades)

        # Exit Reason Analysis
        self.exit_reason_report.analyze_all_exits(self.all_trades)

        # Greeks Accuracy
        self.greeks_accuracy.analyze_greeks(self.all_trades)

        # OI/Volume Conviction
        self.oi_conviction_report.analyze_conviction(self.all_trades)

        # Time of Day
        self.time_of_day_report.analyze_sessions(self.all_trades)

    def generate_complete_report(self) -> str:
        """Generate full post-trade report"""
        report = "\n" + "=" * 100 + "\n"
        report += "📊 ANGEL-X POST-TRADE ANALYTICS REPORT\n"
        report += "=" * 100 + "\n\n"

        if self.pnl_analytics:
            report += self.pnl_analytics.get_summary_report() + "\n"

        report += self.exit_reason_report.get_summary_report() + "\n"
        report += self.greeks_accuracy.get_summary_report() + "\n"
        report += self.oi_conviction_report.get_summary_report() + "\n"
        report += self.time_of_day_report.get_summary_report() + "\n"

        report += "=" * 100 + "\n"
        report += "📈 ACTIONABLE INSIGHTS:\n"
        report += "=" * 100 + "\n"

        insights = self._generate_insights()
        for i, insight in enumerate(insights, 1):
            report += f"{i}. {insight}\n"

        return report

    def _generate_insights(self) -> List[str]:
        """Generate actionable insights"""
        insights = []

        # Win rate insight
        if self.pnl_analytics and self.pnl_analytics.win_rate < 50:
            insights.append(f"⚠️ Win rate below 50% ({self.pnl_analytics.win_rate:.1f}%) - review entry criteria")

        # R:R insight
        if self.pnl_analytics and self.pnl_analytics.avg_rr < 1.5:
            insights.append(f"⚠️ R:R ratio low ({self.pnl_analytics.avg_rr:.2f}) - consider wider targets")

        # Exit reason insight
        best_exit = self.exit_reason_report.get_best_exit_strategy()
        if best_exit and best_exit.win_rate > 70:
            insights.append(
                f"✅ {best_exit.exit_reason.value} exits performing well ({best_exit.win_rate:.1f}%) - use more"
            )

        # Time insight
        best_time = self.time_of_day_report.get_best_session()
        worst_time = self.time_of_day_report.get_worst_session()
        if best_time and worst_time:
            insights.append(
                f"✅ Focus on {best_time.session_name} ({best_time.win_rate:.1f}%), avoid {worst_time.session_name} ({worst_time.win_rate:.1f}%)"
            )

        # OI conviction insight
        if self.oi_conviction_report.high_oi_win_rate > 75:
            insights.append(
                f"✅ HIGH OI conviction very effective ({self.oi_conviction_report.high_oi_win_rate:.1f}%) - prioritize these trades"
            )

        return insights

    def save_report(self, filepath: str):
        """Save complete report"""
        report = self.generate_complete_report()
        with open(filepath, "w") as f:
            f.write(report)
