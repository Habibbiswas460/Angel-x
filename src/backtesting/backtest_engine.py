"""
Backtesting Framework Foundation (Feature #7)
Lightweight CSV-driven runner to simulate strategy logic on historical data.
"""

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional
from datetime import datetime
from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


@dataclass
class BacktestResult:
    total_trades: int = 0
    wins: int = 0
    losses: int = 0
    win_rate: float = 0.0
    gross_pnl: float = 0.0
    net_pnl: float = 0.0
    max_drawdown: float = 0.0
    equity_curve: List[float] = field(default_factory=list)


class BacktestEngine:
    """Minimal backtesting harness for tick/ltp CSV files"""

    def __init__(self, data_file: str, initial_capital: Optional[float] = None):
        self.data_file = Path(data_file)
        self.initial_capital = initial_capital or getattr(config, 'BACKTEST_DEFAULT_CAPITAL', 100000)
        self.slippage_percent = getattr(config, 'BACKTEST_SLIPPAGE_PERCENT', 0.05)
        self.result = BacktestResult()
        logger.info(f"BacktestEngine initialized: data={self.data_file}, capital={self.initial_capital}")

    def _iter_ticks(self):
        """Yield ticks from CSV. Expected columns: timestamp, ltp, bid, ask, volume, oi"""
        if not self.data_file.exists():
            raise FileNotFoundError(f"Backtest data file not found: {self.data_file}")

        with self.data_file.open() as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield {
                    'timestamp': self._parse_ts(row.get('timestamp')),
                    'ltp': float(row.get('ltp', 0) or 0),
                    'bid': float(row.get('bid', 0) or 0),
                    'ask': float(row.get('ask', 0) or 0),
                    'volume': float(row.get('volume', 0) or 0),
                    'oi': float(row.get('oi', 0) or 0),
                }

    @staticmethod
    def _parse_ts(ts_val):
        if ts_val is None:
            return None
        try:
            return datetime.fromisoformat(ts_val)
        except Exception:
            return ts_val

    def run(self, on_tick: Callable[[Dict], Optional[Dict]]):
        """
        Replay ticks through a user callback.
        The callback can return an execution dict: {'pnl': float}
        """
        equity = self.initial_capital
        peak = equity

        for tick in self._iter_ticks():
            trade_result = on_tick(tick)
            if trade_result and isinstance(trade_result, dict):
                pnl = float(trade_result.get('pnl', 0))
                equity += pnl
                self.result.gross_pnl += pnl
                self.result.net_pnl = equity - self.initial_capital
                self.result.total_trades += 1
                if pnl > 0:
                    self.result.wins += 1
                elif pnl < 0:
                    self.result.losses += 1
                peak = max(peak, equity)
                drawdown = (peak - equity)
                self.result.max_drawdown = max(self.result.max_drawdown, drawdown)
            self.result.equity_curve.append(equity)

        if self.result.total_trades:
            self.result.win_rate = (self.result.wins / self.result.total_trades) * 100

        logger.info(
            f"Backtest complete | Trades: {self.result.total_trades} | "
            f"WinRate: {self.result.win_rate:.1f}% | Net PnL: {self.result.net_pnl:.2f}"
        )
        return self.result
