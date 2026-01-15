"""
PHASE 8: Performance Monitoring System
Tracks latency, signal quality, risk metrics, and system health
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
from pathlib import Path


@dataclass
class LatencyMetrics:
    """Track timing for different operations"""

    data_fetch_times: deque = field(default_factory=lambda: deque(maxlen=100))
    signal_generation_times: deque = field(default_factory=lambda: deque(maxlen=100))
    order_execution_times: deque = field(default_factory=lambda: deque(maxlen=100))
    total_latencies: deque = field(default_factory=lambda: deque(maxlen=100))

    def add_data_fetch(self, latency_ms: float):
        self.data_fetch_times.append(latency_ms)

    def add_signal_gen(self, latency_ms: float):
        self.signal_generation_times.append(latency_ms)

    def add_order_exec(self, latency_ms: float):
        self.order_execution_times.append(latency_ms)

    def add_total(self, latency_ms: float):
        self.total_latencies.append(latency_ms)

    def get_stats(self) -> Dict:
        """Calculate latency statistics"""

        def calc_stats(data):
            if not data:
                return {"avg": 0, "min": 0, "max": 0, "p95": 0}
            sorted_data = sorted(data)
            return {
                "avg": sum(data) / len(data),
                "min": min(data),
                "max": max(data),
                "p95": sorted_data[int(len(sorted_data) * 0.95)] if len(sorted_data) > 0 else 0,
            }

        return {
            "data_fetch": calc_stats(self.data_fetch_times),
            "signal_generation": calc_stats(self.signal_generation_times),
            "order_execution": calc_stats(self.order_execution_times),
            "total_latency": calc_stats(self.total_latencies),
        }


@dataclass
class TradeMetrics:
    """Track trading performance"""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0

    # By time window
    trades_by_hour: Dict[int, Dict] = field(default_factory=lambda: defaultdict(dict))

    # By reason
    exit_reasons: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    # Streak tracking
    current_streak: int = 0
    max_win_streak: int = 0
    max_loss_streak: int = 0

    # Drawdown
    peak_capital: float = 100000.0
    current_drawdown: float = 0.0
    max_drawdown: float = 0.0

    def add_trade(self, pnl: float, exit_reason: str, hour: int):
        """Record a completed trade"""
        self.total_trades += 1
        self.total_pnl += pnl

        if pnl > 0:
            self.winning_trades += 1
            if self.current_streak > 0:
                self.current_streak += 1
            else:
                self.current_streak = 1
            self.max_win_streak = max(self.max_win_streak, self.current_streak)
        else:
            self.losing_trades += 1
            if self.current_streak < 0:
                self.current_streak -= 1
            else:
                self.current_streak = -1
            self.max_loss_streak = max(self.max_loss_streak, abs(self.current_streak))

        # Track by hour
        if hour not in self.trades_by_hour:
            self.trades_by_hour[hour] = {"trades": 0, "wins": 0, "pnl": 0.0}
        self.trades_by_hour[hour]["trades"] += 1
        if pnl > 0:
            self.trades_by_hour[hour]["wins"] += 1
        self.trades_by_hour[hour]["pnl"] += pnl

        # Track exit reason
        self.exit_reasons[exit_reason] += 1

        # Update drawdown
        current_capital = self.peak_capital + self.total_pnl
        if current_capital > self.peak_capital:
            self.peak_capital = current_capital
        self.current_drawdown = (self.peak_capital - current_capital) / self.peak_capital * 100
        self.max_drawdown = max(self.max_drawdown, self.current_drawdown)

    def get_win_rate(self) -> float:
        """Calculate overall win rate"""
        if self.total_trades == 0:
            return 0.0
        return (self.winning_trades / self.total_trades) * 100

    def get_hourly_stats(self) -> Dict:
        """Get performance by hour"""
        hourly = {}
        for hour, data in self.trades_by_hour.items():
            win_rate = (data["wins"] / data["trades"] * 100) if data["trades"] > 0 else 0
            hourly[hour] = {
                "trades": data["trades"],
                "win_rate": win_rate,
                "avg_pnl": data["pnl"] / data["trades"] if data["trades"] > 0 else 0,
            }
        return hourly


@dataclass
class SignalQualityMetrics:
    """Track signal accuracy and quality"""

    signals_generated: int = 0
    signals_acted_on: int = 0
    false_signals: int = 0

    # Bias conviction vs outcome
    bias_accuracy: Dict[str, Dict] = field(default_factory=lambda: defaultdict(lambda: {"correct": 0, "total": 0}))

    # Greeks accuracy
    greeks_predictions: List[Dict] = field(default_factory=list)

    def add_signal(self, acted_on: bool):
        """Record a signal"""
        self.signals_generated += 1
        if acted_on:
            self.signals_acted_on += 1

    def add_bias_outcome(self, bias_strength: str, was_correct: bool):
        """Track if bias prediction was correct"""
        self.bias_accuracy[bias_strength]["total"] += 1
        if was_correct:
            self.bias_accuracy[bias_strength]["correct"] += 1

    def get_signal_efficiency(self) -> float:
        """What % of signals result in trades"""
        if self.signals_generated == 0:
            return 0.0
        return (self.signals_acted_on / self.signals_generated) * 100

    def get_bias_accuracy_rate(self) -> Dict:
        """Get accuracy by bias strength"""
        accuracy = {}
        for strength, data in self.bias_accuracy.items():
            if data["total"] > 0:
                accuracy[strength] = (data["correct"] / data["total"]) * 100
            else:
                accuracy[strength] = 0.0
        return accuracy


class PerformanceMonitor:
    """
    Central performance monitoring and metrics tracking
    Institutional-grade observability
    """

    def __init__(self, metrics_dir: str = "logs/metrics"):
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)

        # Core metrics
        self.latency = LatencyMetrics()
        self.trades = TradeMetrics()
        self.signals = SignalQualityMetrics()

        # System health
        self.errors_count = defaultdict(int)
        self.recoveries_count = 0
        self.uptime_start = datetime.now()

        # Session tracking
        self.session_start = datetime.now()
        self.session_id = self.session_start.strftime("%Y%m%d_%H%M%S")

        # Real-time tracking
        self.last_snapshot_time = None
        self.snapshot_intervals: deque = deque(maxlen=100)

    def track_latency(self, operation: str, start_time: float):
        """Track operation latency"""
        latency_ms = (time.time() - start_time) * 1000

        if operation == "data_fetch":
            self.latency.add_data_fetch(latency_ms)
        elif operation == "signal_generation":
            self.latency.add_signal_gen(latency_ms)
        elif operation == "order_execution":
            self.latency.add_order_exec(latency_ms)
        elif operation == "total":
            self.latency.add_total(latency_ms)

        return latency_ms

    def record_trade(self, pnl: float, exit_reason: str):
        """Record completed trade"""
        hour = datetime.now().hour
        self.trades.add_trade(pnl, exit_reason, hour)

    def record_signal(self, acted_on: bool):
        """Record signal generation"""
        self.signals.add_signal(acted_on)

    def record_bias_accuracy(self, bias_strength: str, was_correct: bool):
        """Track bias prediction accuracy"""
        self.signals.add_bias_outcome(bias_strength, was_correct)

    def record_error(self, error_type: str):
        """Track errors by type"""
        self.errors_count[error_type] += 1

    def record_recovery(self):
        """Track successful auto-recovery"""
        self.recoveries_count += 1

    def track_snapshot_interval(self):
        """Track time between data snapshots"""
        now = time.time()
        if self.last_snapshot_time:
            interval_ms = (now - self.last_snapshot_time) * 1000
            self.snapshot_intervals.append(interval_ms)
        self.last_snapshot_time = now

    def get_performance_summary(self) -> Dict:
        """Get comprehensive performance summary"""
        uptime = (datetime.now() - self.uptime_start).total_seconds()

        summary = {
            "session": {
                "id": self.session_id,
                "uptime_hours": uptime / 3600,
                "start_time": self.session_start.isoformat(),
            },
            "latency": self.latency.get_stats(),
            "trading": {
                "total_trades": self.trades.total_trades,
                "win_rate": self.trades.get_win_rate(),
                "total_pnl": self.trades.total_pnl,
                "current_streak": self.trades.current_streak,
                "max_drawdown": self.trades.max_drawdown,
                "current_drawdown": self.trades.current_drawdown,
                "hourly_performance": self.trades.get_hourly_stats(),
            },
            "signals": {
                "generated": self.signals.signals_generated,
                "efficiency": self.signals.get_signal_efficiency(),
                "bias_accuracy": self.signals.get_bias_accuracy_rate(),
            },
            "system": {
                "errors": dict(self.errors_count),
                "recoveries": self.recoveries_count,
                "error_rate": sum(self.errors_count.values()) / max(uptime / 3600, 1),
            },
            "data_quality": {
                "avg_snapshot_interval_ms": (
                    sum(self.snapshot_intervals) / len(self.snapshot_intervals) if self.snapshot_intervals else 0
                )
            },
        }

        return summary

    def get_health_status(self) -> Tuple[str, List[str]]:
        """
        Assess system health
        Returns: (status, issues_list)
        Status: HEALTHY, DEGRADED, CRITICAL
        """
        issues = []

        # Check latency
        latency_stats = self.latency.get_stats()
        if latency_stats["total_latency"]["avg"] > 1000:  # >1s
            issues.append("HIGH_LATENCY: Avg total latency > 1s")

        # Check drawdown
        if self.trades.current_drawdown > 10:
            issues.append(f"HIGH_DRAWDOWN: {self.trades.current_drawdown:.2f}%")

        # Check error rate
        uptime_hours = (datetime.now() - self.uptime_start).total_seconds() / 3600
        error_rate = sum(self.errors_count.values()) / max(uptime_hours, 1)
        if error_rate > 5:  # >5 errors/hour
            issues.append(f"HIGH_ERROR_RATE: {error_rate:.1f} errors/hour")

        # Check win rate (if enough trades)
        if self.trades.total_trades >= 10:
            win_rate = self.trades.get_win_rate()
            if win_rate < 40:
                issues.append(f"LOW_WIN_RATE: {win_rate:.1f}%")

        # Check losing streak
        if self.trades.current_streak < -3:
            issues.append(f"LOSING_STREAK: {abs(self.trades.current_streak)} consecutive losses")

        # Determine status
        if not issues:
            status = "HEALTHY"
        elif len(issues) <= 2 and self.trades.current_drawdown < 15:
            status = "DEGRADED"
        else:
            status = "CRITICAL"

        return status, issues

    def save_metrics(self):
        """Save metrics to file"""
        summary = self.get_performance_summary()

        filename = f"metrics_{self.session_id}.json"
        filepath = self.metrics_dir / filename

        with open(filepath, "w") as f:
            json.dump(summary, f, indent=2)

        return filepath

    def get_optimization_insights(self) -> Dict:
        """
        Generate insights for optimization
        Evidence-based tuning recommendations
        """
        insights = {"latency": [], "signal_quality": [], "risk": [], "timing": []}

        # Latency insights
        latency_stats = self.latency.get_stats()
        if latency_stats["data_fetch"]["avg"] > 500:
            insights["latency"].append("Consider batching option chain fetches")
        if latency_stats["signal_generation"]["avg"] > 200:
            insights["latency"].append("Signal generation is slow - optimize Greeks calculations")

        # Signal quality
        efficiency = self.signals.get_signal_efficiency()
        if efficiency < 30:
            insights["signal_quality"].append(f"Low signal efficiency ({efficiency:.1f}%) - tighten filters")

        # Risk insights
        if self.trades.max_drawdown > 8:
            insights["risk"].append(f"Max drawdown {self.trades.max_drawdown:.1f}% - reduce position sizes")

        # Timing insights
        hourly = self.trades.get_hourly_stats()
        best_hours = sorted(hourly.items(), key=lambda x: x[1]["win_rate"], reverse=True)[:3]
        worst_hours = sorted(hourly.items(), key=lambda x: x[1]["win_rate"])[:3]

        if best_hours and worst_hours:
            insights["timing"].append(f"Best hours: {[h for h, _ in best_hours]}")
            insights["timing"].append(f"Worst hours: {[h for h, _ in worst_hours]}")

        return insights

    def generate_daily_report(self) -> str:
        """Generate end-of-day performance report"""
        summary = self.get_performance_summary()
        status, issues = self.get_health_status()
        insights = self.get_optimization_insights()

        report = f"""
╔══════════════════════════════════════════════════════════╗
║         ANGEL-X DAILY PERFORMANCE REPORT                 ║
╚══════════════════════════════════════════════════════════╝

📅 Session: {summary['session']['id']}
⏱️  Uptime: {summary['session']['uptime_hours']:.2f} hours
🏥 Status: {status}

═══════════════════════════════════════════════════════════

📊 TRADING METRICS
─────────────────────────────────────────────────────────
Total Trades:     {summary['trading']['total_trades']}
Win Rate:         {summary['trading']['win_rate']:.2f}%
Total P&L:        ₹{summary['trading']['total_pnl']:,.2f}
Current Streak:   {summary['trading']['current_streak']}
Max Drawdown:     {summary['trading']['max_drawdown']:.2f}%
Current Drawdown: {summary['trading']['current_drawdown']:.2f}%

⚡ LATENCY METRICS
─────────────────────────────────────────────────────────
Data Fetch:       {summary['latency']['data_fetch']['avg']:.1f}ms (P95: {summary['latency']['data_fetch']['p95']:.1f}ms)
Signal Gen:       {summary['latency']['signal_generation']['avg']:.1f}ms (P95: {summary['latency']['signal_generation']['p95']:.1f}ms)
Order Exec:       {summary['latency']['order_execution']['avg']:.1f}ms (P95: {summary['latency']['order_execution']['p95']:.1f}ms)
Total Latency:    {summary['latency']['total_latency']['avg']:.1f}ms (P95: {summary['latency']['total_latency']['p95']:.1f}ms)

🎯 SIGNAL QUALITY
─────────────────────────────────────────────────────────
Signals Generated: {summary['signals']['generated']}
Signal Efficiency: {summary['signals']['efficiency']:.2f}%

🔧 SYSTEM HEALTH
─────────────────────────────────────────────────────────
Total Errors:     {sum(summary['system']['errors'].values())}
Auto-Recoveries:  {summary['system']['recoveries']}
Error Rate:       {summary['system']['error_rate']:.2f}/hour

"""

        if issues:
            report += "⚠️  ISSUES DETECTED:\n"
            for issue in issues:
                report += f"   • {issue}\n"
            report += "\n"

        report += "💡 OPTIMIZATION INSIGHTS:\n"
        for category, items in insights.items():
            if items:
                report += f"\n{category.upper()}:\n"
                for item in items:
                    report += f"   • {item}\n"

        report += "\n═══════════════════════════════════════════════════════════\n"

        return report
