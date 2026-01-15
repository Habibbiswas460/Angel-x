"""
Trade Journal Analytics Engine
Generates insights from historical trade data
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from pathlib import Path

logger = None  # Will be set by caller


class TradeJournalAnalytics:
    """
    Analyzes trade journal data for:
    - Win/loss patterns
    - Best entry/exit times
    - Greeks correlation
    - Time-of-day analysis
    - Volatility regime analysis
    """

    def __init__(self, journal_dir: str = "./journal"):
        self.journal_dir = Path(journal_dir)
        self.trades = []
        self._load_trades()

    def _load_trades(self):
        """Load all trades from journal"""
        json_files = list(self.journal_dir.glob("trades_*.json"))

        for file in json_files:
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.trades.extend(data)
            except Exception as e:
                print(f"Error loading {file}: {e}")

    def get_entry_analysis(self) -> Dict:
        """Analyze which entry reasons work best"""
        entry_stats = {}

        for trade in self.trades:
            for reason in trade.get("entry_reason_tags", []):
                if reason not in entry_stats:
                    entry_stats[reason] = {"count": 0, "wins": 0, "total_pnl": 0, "avg_pnl": 0}

                entry_stats[reason]["count"] += 1
                entry_stats[reason]["total_pnl"] += trade.get("pnl_amount", 0)

                if trade.get("pnl_amount", 0) > 0:
                    entry_stats[reason]["wins"] += 1

        # Calculate averages and win rates
        for reason in entry_stats:
            entry_stats[reason]["avg_pnl"] = entry_stats[reason]["total_pnl"] / entry_stats[reason]["count"]
            entry_stats[reason]["win_rate"] = entry_stats[reason]["wins"] / entry_stats[reason]["count"] * 100

        return entry_stats

    def get_exit_analysis(self) -> Dict:
        """Analyze which exit reasons are most profitable"""
        exit_stats = {}

        for trade in self.trades:
            for reason in trade.get("exit_reason_tags", []):
                if reason not in exit_stats:
                    exit_stats[reason] = {"count": 0, "wins": 0, "total_pnl": 0, "avg_hold_sec": 0}

                exit_stats[reason]["count"] += 1
                exit_stats[reason]["total_pnl"] += trade.get("pnl_amount", 0)
                exit_stats[reason]["avg_hold_sec"] += trade.get("duration_seconds", 0)

                if trade.get("pnl_amount", 0) > 0:
                    exit_stats[reason]["wins"] += 1

        # Calculate averages
        for reason in exit_stats:
            exit_stats[reason]["avg_hold_sec"] = int(exit_stats[reason]["avg_hold_sec"] / exit_stats[reason]["count"])
            exit_stats[reason]["win_rate"] = exit_stats[reason]["wins"] / exit_stats[reason]["count"] * 100

        return exit_stats

    def get_time_analysis(self) -> Dict:
        """Analyze performance by time of day"""
        hour_stats = {}

        for trade in self.trades:
            entry_time = datetime.fromisoformat(trade["timestamp_entry"])
            hour = entry_time.hour

            if hour not in hour_stats:
                hour_stats[hour] = {"count": 0, "wins": 0, "total_pnl": 0, "avg_pnl": 0, "time_slot": f"{hour:02d}:00"}

            hour_stats[hour]["count"] += 1
            hour_stats[hour]["total_pnl"] += trade.get("pnl_amount", 0)

            if trade.get("pnl_amount", 0) > 0:
                hour_stats[hour]["wins"] += 1

        # Calculate averages
        for hour in hour_stats:
            hour_stats[hour]["avg_pnl"] = hour_stats[hour]["total_pnl"] / hour_stats[hour]["count"]
            hour_stats[hour]["win_rate"] = hour_stats[hour]["wins"] / hour_stats[hour]["count"] * 100

        return dict(sorted(hour_stats.items()))

    def get_greeks_correlation(self) -> Dict:
        """Analyze Greeks at entry vs profitability"""
        delta_buckets = {}
        gamma_buckets = {}

        for trade in self.trades:
            entry_delta = abs(trade.get("entry_delta", 0))
            entry_gamma = trade.get("entry_gamma", 0)
            pnl = trade.get("pnl_amount", 0)

            # Delta analysis (0.1 buckets)
            delta_bucket = int(entry_delta * 10) / 10
            if delta_bucket not in delta_buckets:
                delta_buckets[delta_bucket] = {"count": 0, "wins": 0, "total_pnl": 0}

            delta_buckets[delta_bucket]["count"] += 1
            delta_buckets[delta_bucket]["total_pnl"] += pnl
            if pnl > 0:
                delta_buckets[delta_bucket]["wins"] += 1

            # Gamma analysis (0.001 buckets)
            gamma_bucket = int(entry_gamma * 1000) / 1000
            if gamma_bucket not in gamma_buckets:
                gamma_buckets[gamma_bucket] = {"count": 0, "wins": 0, "total_pnl": 0}

            gamma_buckets[gamma_bucket]["count"] += 1
            gamma_buckets[gamma_bucket]["total_pnl"] += pnl
            if pnl > 0:
                gamma_buckets[gamma_bucket]["wins"] += 1

        return {
            "delta_analysis": dict(sorted(delta_buckets.items())),
            "gamma_analysis": dict(sorted(gamma_buckets.items())),
        }

    def get_holding_time_analysis(self) -> Dict:
        """Analyze profit vs holding duration"""
        duration_buckets = {}

        for trade in self.trades:
            duration = trade.get("duration_seconds", 0)
            pnl = trade.get("pnl_amount", 0)

            # Group into 1-minute buckets
            bucket = (duration // 60) * 60
            if bucket not in duration_buckets:
                duration_buckets[bucket] = {
                    "count": 0,
                    "wins": 0,
                    "total_pnl": 0,
                    "avg_pnl": 0,
                    "duration_min": duration // 60,
                }

            duration_buckets[bucket]["count"] += 1
            duration_buckets[bucket]["total_pnl"] += pnl
            if pnl > 0:
                duration_buckets[bucket]["wins"] += 1

        # Calculate averages
        for bucket in duration_buckets:
            duration_buckets[bucket]["avg_pnl"] = (
                duration_buckets[bucket]["total_pnl"] / duration_buckets[bucket]["count"]
            )
            duration_buckets[bucket]["win_rate"] = (
                duration_buckets[bucket]["wins"] / duration_buckets[bucket]["count"] * 100
            )

        return dict(sorted(duration_buckets.items()))

    def get_strike_selection_analysis(self) -> Dict:
        """Analyze which strikes (ATM, OTM, ITM) work best"""
        strike_stats = {}

        for trade in self.trades:
            strike = trade.get("strike", "UNKNOWN")
            pnl = trade.get("pnl_amount", 0)

            if strike not in strike_stats:
                strike_stats[strike] = {"count": 0, "wins": 0, "total_pnl": 0, "avg_pnl": 0}

            strike_stats[strike]["count"] += 1
            strike_stats[strike]["total_pnl"] += pnl
            if pnl > 0:
                strike_stats[strike]["wins"] += 1

        # Calculate averages
        for strike in strike_stats:
            strike_stats[strike]["avg_pnl"] = strike_stats[strike]["total_pnl"] / strike_stats[strike]["count"]
            strike_stats[strike]["win_rate"] = strike_stats[strike]["wins"] / strike_stats[strike]["count"] * 100

        return strike_stats

    def get_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        if not self.trades:
            return {"error": "No trades in journal"}

        total_trades = len(self.trades)
        wins = sum(1 for t in self.trades if t.get("pnl_amount", 0) > 0)
        losses = sum(1 for t in self.trades if t.get("pnl_amount", 0) < 0)
        total_pnl = sum(t.get("pnl_amount", 0) for t in self.trades)
        avg_pnl = total_pnl / total_trades if total_trades > 0 else 0

        best_trade = max(self.trades, key=lambda t: t.get("pnl_amount", 0))
        worst_trade = min(self.trades, key=lambda t: t.get("pnl_amount", 0))

        avg_holding = sum(t.get("duration_seconds", 0) for t in self.trades) / total_trades if total_trades > 0 else 0

        return {
            "total_trades": total_trades,
            "wins": wins,
            "losses": losses,
            "win_rate_percent": round(wins / total_trades * 100, 1) if total_trades > 0 else 0,
            "total_pnl": round(total_pnl, 2),
            "avg_pnl_per_trade": round(avg_pnl, 2),
            "best_trade_pnl": round(best_trade.get("pnl_amount", 0), 2),
            "worst_trade_pnl": round(worst_trade.get("pnl_amount", 0), 2),
            "avg_holding_minutes": round(avg_holding / 60, 1),
            "avg_entry_delta": round(sum(t.get("entry_delta", 0) for t in self.trades) / total_trades, 3),
            "avg_entry_gamma": round(sum(t.get("entry_gamma", 0) for t in self.trades) / total_trades, 4),
        }

    def export_analytics_report(self, output_file: str = None) -> str:
        """Export comprehensive analytics report"""
        if not output_file:
            output_file = f"journal/analytics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        report = []
        report.append("=" * 80)
        report.append("ANGEL-X TRADE JOURNAL ANALYTICS REPORT")
        report.append("=" * 80)
        report.append("")

        # Summary
        summary = self.get_summary_report()
        report.append("SUMMARY")
        report.append("-" * 80)
        for key, value in summary.items():
            report.append(f"{key}: {value}")
        report.append("")

        # Entry analysis
        report.append("ENTRY REASON ANALYSIS")
        report.append("-" * 80)
        entry_analysis = self.get_entry_analysis()
        for reason, stats in sorted(entry_analysis.items(), key=lambda x: x[1]["avg_pnl"], reverse=True):
            report.append(
                f"{reason}: {stats['count']} trades, "
                f"Win Rate: {stats['win_rate']:.1f}%, "
                f"Avg P&L: ₹{stats['avg_pnl']:.2f}"
            )
        report.append("")

        # Exit analysis
        report.append("EXIT REASON ANALYSIS")
        report.append("-" * 80)
        exit_analysis = self.get_exit_analysis()
        for reason, stats in sorted(exit_analysis.items(), key=lambda x: x[1]["total_pnl"], reverse=True):
            report.append(
                f"{reason}: {stats['count']} times, "
                f"Win Rate: {stats['win_rate']:.1f}%, "
                f"Total P&L: ₹{stats['total_pnl']:.2f}, "
                f"Avg Hold: {stats['avg_hold_sec']}s"
            )
        report.append("")

        # Time analysis
        report.append("TIME-OF-DAY ANALYSIS")
        report.append("-" * 80)
        time_analysis = self.get_time_analysis()
        for hour, stats in time_analysis.items():
            report.append(
                f"{stats['time_slot']}: {stats['count']} trades, "
                f"Win Rate: {stats['win_rate']:.1f}%, "
                f"Avg P&L: ₹{stats['avg_pnl']:.2f}"
            )
        report.append("")

        # Greeks analysis
        report.append("GREEKS CORRELATION")
        report.append("-" * 80)
        greeks = self.get_greeks_correlation()
        report.append("Delta Buckets:")
        for delta, stats in list(greeks["delta_analysis"].items())[:10]:
            if stats["count"] > 0:
                report.append(
                    f"  Δ {delta:.1f}: {stats['count']} trades, "
                    f"Win: {stats['wins']}, "
                    f"Avg: ₹{stats['total_pnl']/stats['count']:.2f}"
                )
        report.append("")

        # Write report
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as f:
            f.write("\n".join(report))

        return output_file
