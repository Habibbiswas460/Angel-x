"""
Professional Paper Trading Journal
Trade logging with detailed analytics and performance metrics
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import json

from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class PaperTradingJournal:
    """Professional trading journal for paper trading"""

    def __init__(self, journal_dir: Optional[str] = None):
        """
        Initialize trading journal

        Args:
            journal_dir: Directory to store journal files
        """
        if journal_dir is None:
            journal_dir = getattr(config, "JOURNAL_DIR", "./journal")

        self.journal_dir = Path(journal_dir)
        self.journal_dir.mkdir(parents=True, exist_ok=True)

        self.trades: List[Dict] = []
        self.session_start = datetime.now()

        logger.info(f"PaperTradingJournal initialized | Directory: {self.journal_dir}")

    def log_trade(
        self,
        trade_id: str,
        symbol: str,
        option_type: str,
        strike: int,
        entry_time: datetime,
        entry_price: float,
        entry_delta: Optional[float] = None,
        entry_gamma: Optional[float] = None,
        entry_theta: Optional[float] = None,
        entry_vega: Optional[float] = None,
        entry_iv: Optional[float] = None,
        exit_time: Optional[datetime] = None,
        exit_price: Optional[float] = None,
        exit_delta: Optional[float] = None,
        exit_gamma: Optional[float] = None,
        exit_reason: Optional[str] = None,
        quantity: int = 75,
        pnl_amount: float = 0.0,
        pnl_percent: float = 0.0,
        time_in_trade_seconds: int = 0,
        entry_spread: float = 0.0,
        exit_spread: float = 0.0,
        entry_reason_tags: Optional[List[str]] = None,
        exit_reason_tags: Optional[List[str]] = None,
        slippage: float = 0.0,
    ):
        """
        Log a trade to the journal

        Args:
            trade_id: Unique trade identifier
            symbol: Option symbol
            option_type: CE or PE
            strike: Strike price
            entry_time: Entry timestamp
            entry_price: Entry price
            quantity: Trade quantity
            exit_time: Exit timestamp
            exit_price: Exit price
            pnl_amount: P&L in rupees
            pnl_percent: P&L in percentage
            time_in_trade_seconds: Trade duration
            ... and more detailed metrics
        """
        trade_record = {
            "trade_id": trade_id,
            "symbol": symbol,
            "option_type": option_type,
            "strike": strike,
            "quantity": quantity,
            "entry_time": entry_time.isoformat() if entry_time else None,
            "entry_price": entry_price,
            "entry_delta": entry_delta,
            "entry_gamma": entry_gamma,
            "entry_theta": entry_theta,
            "entry_vega": entry_vega,
            "entry_iv": entry_iv,
            "exit_time": exit_time.isoformat() if exit_time else None,
            "exit_price": exit_price,
            "exit_delta": exit_delta,
            "exit_gamma": exit_gamma,
            "exit_reason": exit_reason,
            "pnl_amount": pnl_amount,
            "pnl_percent": pnl_percent,
            "time_in_trade_seconds": time_in_trade_seconds,
            "entry_spread": entry_spread,
            "exit_spread": exit_spread,
            "entry_reason_tags": entry_reason_tags or [],
            "exit_reason_tags": exit_reason_tags or [],
            "slippage": slippage,
        }

        self.trades.append(trade_record)

        # Log to console
        logger.info(
            f"📔 Trade Logged | {symbol} | P&L: ₹{pnl_amount:+.2f} ({pnl_percent:+.2f}%) | "
            f"Time: {time_in_trade_seconds}s"
        )

    def export_csv(self, filename: Optional[str] = None) -> str:
        """Export trades to CSV file"""
        if not self.trades:
            logger.warning("No trades to export")
            return ""

        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        filepath = self.journal_dir / filename

        # CSV headers
        headers = [
            "trade_id",
            "timestamp",
            "symbol",
            "option_type",
            "strike",
            "quantity",
            "entry_time",
            "entry_price",
            "entry_delta",
            "entry_gamma",
            "entry_theta",
            "entry_vega",
            "entry_iv",
            "exit_time",
            "exit_price",
            "exit_delta",
            "exit_gamma",
            "exit_reason",
            "pnl_amount",
            "pnl_percent",
            "time_in_trade_seconds",
            "entry_spread",
            "exit_spread",
            "entry_reason_tags",
            "exit_reason_tags",
            "slippage",
        ]

        with open(filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()

            for trade in self.trades:
                row = {
                    "trade_id": trade["trade_id"],
                    "timestamp": datetime.now().isoformat(),
                    "symbol": trade["symbol"],
                    "option_type": trade["option_type"],
                    "strike": trade["strike"],
                    "quantity": trade["quantity"],
                    "entry_time": trade["entry_time"],
                    "entry_price": trade["entry_price"],
                    "entry_delta": trade["entry_delta"],
                    "entry_gamma": trade["entry_gamma"],
                    "entry_theta": trade["entry_theta"],
                    "entry_vega": trade["entry_vega"],
                    "entry_iv": trade["entry_iv"],
                    "exit_time": trade["exit_time"],
                    "exit_price": trade["exit_price"],
                    "exit_delta": trade["exit_delta"],
                    "exit_gamma": trade["exit_gamma"],
                    "exit_reason": trade["exit_reason"],
                    "pnl_amount": trade["pnl_amount"],
                    "pnl_percent": trade["pnl_percent"],
                    "time_in_trade_seconds": trade["time_in_trade_seconds"],
                    "entry_spread": trade["entry_spread"],
                    "exit_spread": trade["exit_spread"],
                    "entry_reason_tags": "|".join(trade["entry_reason_tags"]),
                    "exit_reason_tags": "|".join(trade["exit_reason_tags"]),
                    "slippage": trade["slippage"],
                }
                writer.writerow(row)

        logger.info(f"✓ Trades exported to {filepath} ({len(self.trades)} trades)")
        return str(filepath)

    def export_json(self, filename: Optional[str] = None) -> str:
        """Export trades to JSON file"""
        if filename is None:
            filename = f"trades_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        filepath = self.journal_dir / filename

        with open(filepath, "w") as f:
            json.dump(
                {
                    "session_start": self.session_start.isoformat(),
                    "export_time": datetime.now().isoformat(),
                    "total_trades": len(self.trades),
                    "trades": self.trades,
                },
                f,
                indent=2,
            )

        logger.info(f"✓ Trades exported to {filepath}")
        return str(filepath)

    def export_performance_report(self, filename: Optional[str] = None) -> str:
        """Generate detailed performance report"""
        if filename is None:
            filename = f"performance_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

        filepath = self.journal_dir / filename

        # Calculate statistics
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t["pnl_amount"] > 0])
        losing_trades = len([t for t in self.trades if t["pnl_amount"] < 0])
        breakeven_trades = len([t for t in self.trades if t["pnl_amount"] == 0])

        total_pnl = sum(t["pnl_amount"] for t in self.trades)
        avg_win = sum(t["pnl_amount"] for t in self.trades if t["pnl_amount"] > 0) / max(winning_trades, 1)
        avg_loss = sum(t["pnl_amount"] for t in self.trades if t["pnl_amount"] < 0) / max(losing_trades, 1)

        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        profit_factor = abs(
            sum(t["pnl_amount"] for t in self.trades if t["pnl_amount"] > 0)
            / max(sum(t["pnl_amount"] for t in self.trades if t["pnl_amount"] < 0), 0.01)
        )

        avg_time_in_trade = sum(t["time_in_trade_seconds"] for t in self.trades) / max(total_trades, 1)

        # Generate report
        report = f"""
╔════════════════════════════════════════════════════════════════╗
║          PAPER TRADING PERFORMANCE REPORT                      ║
║          Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}                     ║
╚════════════════════════════════════════════════════════════════╝

📊 TRADE STATISTICS
─────────────────────────────────────────────────────────────────
  Total Trades:          {total_trades}
  Winning Trades:        {winning_trades}
  Losing Trades:         {losing_trades}
  Breakeven Trades:      {breakeven_trades}
  Win Rate:              {win_rate:.2f}%

💰 PROFIT & LOSS
─────────────────────────────────────────────────────────────────
  Total P&L:             ₹{total_pnl:+,.2f}
  Average Win:           ₹{avg_win:+,.2f}
  Average Loss:          ₹{avg_loss:+,.2f}
  Profit Factor:         {profit_factor:.2f}

⏱️  TIME METRICS
─────────────────────────────────────────────────────────────────
  Average Trade Duration: {avg_time_in_trade:.0f} seconds
  Session Duration:       {(datetime.now() - self.session_start).total_seconds() / 3600:.2f} hours

📈 TRADE ANALYSIS
─────────────────────────────────────────────────────────────────
"""

        # Add top performing trades
        sorted_trades = sorted(self.trades, key=lambda x: x["pnl_amount"], reverse=True)

        if sorted_trades:
            report += f"\nTop 5 Winning Trades:\n"
            for i, trade in enumerate(sorted_trades[:5], 1):
                report += (
                    f"  {i}. {trade['symbol']} | P&L: ₹{trade['pnl_amount']:+,.2f} ({trade['pnl_percent']:+.2f}%)\n"
                )

        bottom_trades = sorted(self.trades, key=lambda x: x["pnl_amount"])
        if bottom_trades:
            report += f"\nTop 5 Losing Trades:\n"
            for i, trade in enumerate(bottom_trades[:5], 1):
                report += (
                    f"  {i}. {trade['symbol']} | P&L: ₹{trade['pnl_amount']:+,.2f} ({trade['pnl_percent']:+.2f}%)\n"
                )

        report += f"\n{'='*63}\n"

        with open(filepath, "w") as f:
            f.write(report)

        logger.info(f"✓ Performance report generated: {filepath}")
        return str(filepath)

    def get_summary(self) -> Dict:
        """Get trading summary"""
        if not self.trades:
            return {}

        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t["pnl_amount"] > 0])
        losing_trades = len([t for t in self.trades if t["pnl_amount"] < 0])
        total_pnl = sum(t["pnl_amount"] for t in self.trades)

        return {
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": (winning_trades / total_trades * 100) if total_trades > 0 else 0,
            "total_pnl": total_pnl,
            "avg_trade_pnl": total_pnl / total_trades if total_trades > 0 else 0,
            "best_trade": max([t["pnl_amount"] for t in self.trades], default=0),
            "worst_trade": min([t["pnl_amount"] for t in self.trades], default=0),
        }
