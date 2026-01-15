"""
PHASE 8.6: Performance Metrics Tracking
Track everything for evidence-based improvement
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class TradeRecord:
    """Detailed trade record"""

    trade_id: str
    timestamp: datetime
    symbol: str
    entry_price: float
    exit_price: float
    quantity: int
    pnl: float
    holding_time_seconds: int
    exit_reason: str  # THETA, REVERSAL, STOP_LOSS, TARGET

    # Market context
    entry_iv: float
    exit_iv: float
    entry_time: str  # Market session

    # Greeks at entry
    entry_delta: float
    entry_theta: float
    entry_gamma: float

    # OI conviction
    oi_delta: int
    oi_conviction: str  # HIGH, MEDIUM, LOW

    # Bias strength
    bias_strength: float
    bias_direction: str  # BULLISH, BEARISH


class PerformanceTracker:
    """
    Comprehensive performance metrics tracking
    Evidence-based improvement
    """

    def __init__(self):
        self.trades: List[TradeRecord] = []

        # Time-based analysis
        self.trades_by_session: Dict[str, List] = defaultdict(list)
        self.trades_by_hour: Dict[int, List] = defaultdict(list)

        # Exit reason analysis
        self.exit_reasons: Dict[str, int] = defaultdict(int)

        # Greeks accuracy
        self.greeks_vs_outcome: List[Dict] = []

        # OI conviction analysis
        self.oi_vs_pnl: List[Dict] = []

    def record_trade(self, trade: TradeRecord):
        """Record completed trade"""
        self.trades.append(trade)

        # Session analysis
        self.trades_by_session[trade.entry_time].append(trade)

        # Hour analysis
        hour = trade.timestamp.hour
        self.trades_by_hour[hour].append(trade)

        # Exit reason
        self.exit_reasons[trade.exit_reason] += 1

        # Greeks accuracy
        self.greeks_vs_outcome.append(
            {
                "entry_theta": trade.entry_theta,
                "holding_time": trade.holding_time_seconds,
                "pnl": trade.pnl,
                "outcome": "WIN" if trade.pnl > 0 else "LOSS",
            }
        )

        # OI conviction
        self.oi_vs_pnl.append(
            {
                "oi_delta": trade.oi_delta,
                "oi_conviction": trade.oi_conviction,
                "pnl": trade.pnl,
                "outcome": "WIN" if trade.pnl > 0 else "LOSS",
            }
        )

    def get_win_rate_by_time(self) -> Dict:
        """
        Analyze win rate by time of day
        Identify best/worst trading windows
        """
        session_stats = {}

        for session, trades in self.trades_by_session.items():
            if not trades:
                continue

            wins = sum(1 for t in trades if t.pnl > 0)
            total = len(trades)
            win_rate = (wins / total) * 100 if total > 0 else 0

            avg_pnl = sum(t.pnl for t in trades) / total

            session_stats[session] = {
                "total_trades": total,
                "wins": wins,
                "losses": total - wins,
                "win_rate": win_rate,
                "avg_pnl": avg_pnl,
            }

        return session_stats

    def get_hourly_performance(self) -> Dict:
        """Win rate by hour"""
        hourly_stats = {}

        for hour, trades in self.trades_by_hour.items():
            if not trades:
                continue

            wins = sum(1 for t in trades if t.pnl > 0)
            total = len(trades)
            win_rate = (wins / total) * 100 if total > 0 else 0

            hourly_stats[hour] = {
                "total_trades": total,
                "win_rate": win_rate,
                "avg_pnl": sum(t.pnl for t in trades) / total,
            }

        return hourly_stats

    def get_avg_holding_time(self) -> Dict:
        """
        Average holding time analysis
        By outcome (win vs loss)
        """
        if not self.trades:
            return {}

        wins = [t for t in self.trades if t.pnl > 0]
        losses = [t for t in self.trades if t.pnl <= 0]

        avg_holding_win = sum(t.holding_time_seconds for t in wins) / len(wins) if wins else 0
        avg_holding_loss = sum(t.holding_time_seconds for t in losses) / len(losses) if losses else 0

        return {
            "avg_holding_time_win_seconds": avg_holding_win,
            "avg_holding_time_loss_seconds": avg_holding_loss,
            "avg_holding_time_win_minutes": avg_holding_win / 60,
            "avg_holding_time_loss_minutes": avg_holding_loss / 60,
        }

    def get_exit_reason_distribution(self) -> Dict:
        """
        Distribution of exit reasons
        Understand why trades are being closed
        """
        total = sum(self.exit_reasons.values())

        if total == 0:
            return {}

        distribution = {}
        for reason, count in self.exit_reasons.items():
            distribution[reason] = {"count": count, "percentage": (count / total) * 100}

        return distribution

    def get_greeks_accuracy_analysis(self) -> Dict:
        """
        Analyze if Greeks predictions matched outcome

        Theta decay → Should be profitable if held long enough
        """
        if not self.greeks_vs_outcome:
            return {}

        # Group by theta decay expectation
        high_theta = [g for g in self.greeks_vs_outcome if abs(g["entry_theta"]) > 0.5]
        low_theta = [g for g in self.greeks_vs_outcome if abs(g["entry_theta"]) <= 0.5]

        def calc_win_rate(group):
            if not group:
                return 0
            wins = sum(1 for g in group if g["outcome"] == "WIN")
            return (wins / len(group)) * 100

        return {
            "high_theta_decay_trades": len(high_theta),
            "high_theta_win_rate": calc_win_rate(high_theta),
            "low_theta_decay_trades": len(low_theta),
            "low_theta_win_rate": calc_win_rate(low_theta),
        }

    def get_oi_conviction_analysis(self) -> Dict:
        """
        Analyze OI conviction vs outcome
        Does higher OI conviction = better results?
        """
        if not self.oi_vs_pnl:
            return {}

        # Group by conviction level
        high_conviction = [o for o in self.oi_vs_pnl if o["oi_conviction"] == "HIGH"]
        medium_conviction = [o for o in self.oi_vs_pnl if o["oi_conviction"] == "MEDIUM"]
        low_conviction = [o for o in self.oi_vs_pnl if o["oi_conviction"] == "LOW"]

        def calc_metrics(group):
            if not group:
                return {"trades": 0, "win_rate": 0, "avg_pnl": 0}

            wins = sum(1 for o in group if o["outcome"] == "WIN")
            win_rate = (wins / len(group)) * 100
            avg_pnl = sum(o["pnl"] for o in group) / len(group)

            return {"trades": len(group), "win_rate": win_rate, "avg_pnl": avg_pnl}

        return {
            "high_conviction": calc_metrics(high_conviction),
            "medium_conviction": calc_metrics(medium_conviction),
            "low_conviction": calc_metrics(low_conviction),
        }

    def get_comprehensive_report(self) -> Dict:
        """
        Generate comprehensive performance report
        All metrics in one place
        """
        return {
            "total_trades": len(self.trades),
            "overall_win_rate": self._calc_overall_win_rate(),
            "overall_pnl": sum(t.pnl for t in self.trades),
            "time_analysis": {
                "by_session": self.get_win_rate_by_time(),
                "by_hour": self.get_hourly_performance(),
                "holding_time": self.get_avg_holding_time(),
            },
            "exit_reasons": self.get_exit_reason_distribution(),
            "greeks_accuracy": self.get_greeks_accuracy_analysis(),
            "oi_conviction": self.get_oi_conviction_analysis(),
            "insights": self._generate_insights(),
        }

    def _calc_overall_win_rate(self) -> float:
        """Calculate overall win rate"""
        if not self.trades:
            return 0.0

        wins = sum(1 for t in self.trades if t.pnl > 0)
        return (wins / len(self.trades)) * 100

    def _generate_insights(self) -> List[str]:
        """
        Auto-generate actionable insights
        Evidence-based recommendations
        """
        insights = []

        # Time-based insights
        session_stats = self.get_win_rate_by_time()
        if session_stats:
            best_session = max(session_stats.items(), key=lambda x: x[1]["win_rate"])
            worst_session = min(session_stats.items(), key=lambda x: x[1]["win_rate"])

            insights.append(f"Best trading session: {best_session[0]} ({best_session[1]['win_rate']:.1f}% win rate)")
            insights.append(f"Worst trading session: {worst_session[0]} ({worst_session[1]['win_rate']:.1f}% win rate)")

        # Exit reason insights
        exit_dist = self.get_exit_reason_distribution()
        if exit_dist:
            most_common = max(exit_dist.items(), key=lambda x: x[1]["count"])
            insights.append(f"Most common exit: {most_common[0]} ({most_common[1]['percentage']:.1f}%)")

        # OI conviction insights
        oi_analysis = self.get_oi_conviction_analysis()
        if oi_analysis:
            high_conv = oi_analysis.get("high_conviction", {})
            low_conv = oi_analysis.get("low_conviction", {})

            if high_conv.get("win_rate", 0) > low_conv.get("win_rate", 0) + 10:
                insights.append(
                    f"High OI conviction significantly better: {high_conv['win_rate']:.1f}% vs {low_conv['win_rate']:.1f}%"
                )

        # Greeks insights
        greeks_analysis = self.get_greeks_accuracy_analysis()
        if greeks_analysis:
            high_theta_wr = greeks_analysis.get("high_theta_win_rate", 0)
            if high_theta_wr > 60:
                insights.append(f"High theta decay trades performing well: {high_theta_wr:.1f}% win rate")

        return insights

    def export_trades_to_json(self, filepath: str):
        """Export all trades to JSON for analysis"""
        trades_data = []

        for trade in self.trades:
            trades_data.append(
                {
                    "trade_id": trade.trade_id,
                    "timestamp": trade.timestamp.isoformat(),
                    "symbol": trade.symbol,
                    "pnl": trade.pnl,
                    "holding_time_seconds": trade.holding_time_seconds,
                    "exit_reason": trade.exit_reason,
                    "entry_time": trade.entry_time,
                    "oi_conviction": trade.oi_conviction,
                    "bias_strength": trade.bias_strength,
                }
            )

        with open(filepath, "w") as f:
            json.dump(trades_data, f, indent=2)
