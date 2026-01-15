"""
Strategy Backtesting Engine
Simulates strategy execution on historical tick data
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    """Backtest execution result"""

    strategy_name: str
    symbol: str
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    avg_pnl_per_trade: float
    max_drawdown: float
    sharpe_ratio: float
    sortino_ratio: float
    profit_factor: float
    start_date: str
    end_date: str

    def __str__(self) -> str:
        return f"""
╔══ BACKTEST REPORT: {self.strategy_name} ({self.symbol}) ══╗
║ Period: {self.start_date} → {self.end_date}
║ Total Trades: {self.total_trades} ({self.winning_trades}W/{self.losing_trades}L)
║ Win Rate: {self.win_rate:.2%}
║ Total P&L: ₹{self.total_pnl:.2f}
║ Avg P&L/Trade: ₹{self.avg_pnl_per_trade:.2f}
║ Max Drawdown: {self.max_drawdown:.2%}
║ Sharpe Ratio: {self.sharpe_ratio:.2f}
║ Sortino Ratio: {self.sortino_ratio:.2f}
║ Profit Factor: {self.profit_factor:.2f}
╚═══════════════════════════════════════════════╝
        """.strip()


@dataclass
class TradeExecution:
    """Single trade execution"""

    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    qty: int = 1
    pnl: float = 0.0
    pnl_percent: float = 0.0

    def is_open(self) -> bool:
        return self.exit_time is None

    def close(self, exit_price: float, exit_time: datetime):
        """Close trade"""
        self.exit_price = exit_price
        self.exit_time = exit_time
        self.pnl = (exit_price - self.entry_price) * self.qty
        self.pnl_percent = (exit_price - self.entry_price) / self.entry_price * 100


class BacktestEngine:
    """Execute strategy on historical data"""

    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.trades: List[TradeExecution] = []
        self.equity_curve = [initial_capital]
        self.portfolio_values = [initial_capital]

    def run(self, df: pd.DataFrame, strategy_func, symbol: str = "NIFTY") -> BacktestResult:
        """
        Run backtest on DataFrame

        Args:
            df: DataFrame with OHLCV data (columns: open, high, low, close, volume)
            strategy_func: Function(row, trades, capital) -> Dict with 'action', 'price'
            symbol: Symbol name

        Returns:
            BacktestResult
        """
        logger.info(f"Starting backtest: {symbol}")
        self.trades = []
        self.equity_curve = [self.initial_capital]
        self.capital = self.initial_capital

        # Ensure required columns
        if not all(col in df.columns for col in ["open", "high", "low", "close", "volume"]):
            raise ValueError("DataFrame must contain OHLCV columns")

        start_date = df.index[0].strftime("%Y-%m-%d")
        end_date = df.index[-1].strftime("%Y-%m-%d")

        # Simulate each candle
        for idx, (ts, row) in enumerate(df.iterrows()):
            # Call strategy
            signal = strategy_func(row=row, trades=self.trades, capital=self.capital)

            if not signal:
                continue

            action = signal.get("action")  # BUY, SELL, CLOSE
            price = signal.get("price", row["close"])
            qty = signal.get("qty", 1)

            # Execute action
            if action == "BUY" and not self._has_open_trade():
                self._open_trade(ts, price, qty)

            elif action == "SELL" and self._has_open_trade():
                self._close_trade(ts, price)

            elif action == "CLOSE" and self._has_open_trade():
                self._close_trade(ts, price)

            # Mark-to-market (using close price)
            self._update_equity(row["close"])

        # Close any open positions at end
        if self._has_open_trade():
            self._close_trade(df.index[-1], df.iloc[-1]["close"])

        # Calculate metrics
        return self._calculate_metrics(symbol, start_date, end_date)

    def _open_trade(self, ts: datetime, price: float, qty: int = 1):
        """Open a trade"""
        if self.capital < price * qty:
            logger.warning(f"Insufficient capital to open trade at {price}")
            return

        trade = TradeExecution(entry_time=ts, entry_price=price, qty=qty)
        self.trades.append(trade)
        logger.info(f"BUY: {qty}x @ ₹{price} | Capital: ₹{self.capital:.2f}")

    def _close_trade(self, ts: datetime, price: float):
        """Close open trade"""
        if not self._has_open_trade():
            return

        trade = self.trades[-1]  # Close most recent
        if trade.is_open():
            trade.close(price, ts)
            self.capital += trade.pnl
            logger.info(
                f"SELL: {trade.qty}x @ ₹{price} | P&L: ₹{trade.pnl:.2f} ({trade.pnl_percent:.2f}%) | Capital: ₹{self.capital:.2f}"
            )

    def _has_open_trade(self) -> bool:
        """Check if there's an open position"""
        return any(t.is_open() for t in self.trades)

    def _update_equity(self, market_price: float):
        """Update portfolio value with mark-to-market"""
        unrealized = 0
        for trade in self.trades:
            if trade.is_open():
                unrealized += (market_price - trade.entry_price) * trade.qty

        portfolio_value = self.capital + unrealized
        self.equity_curve.append(portfolio_value)
        self.portfolio_values.append(portfolio_value)

    def _calculate_metrics(self, symbol: str, start_date: str, end_date: str) -> BacktestResult:
        """Calculate performance metrics"""
        closed_trades = [t for t in self.trades if not t.is_open()]

        if not closed_trades:
            # No closed trades
            total_pnl = 0
            win_rate = 0
            avg_pnl = 0
            winning = 0
            losing = 0
        else:
            total_pnl = sum(t.pnl for t in closed_trades)
            winning = sum(1 for t in closed_trades if t.pnl > 0)
            losing = len(closed_trades) - winning
            win_rate = winning / len(closed_trades) if closed_trades else 0
            avg_pnl = total_pnl / len(closed_trades)

        # Drawdown
        equity_array = np.array(self.equity_curve)
        running_max = np.maximum.accumulate(equity_array)
        drawdown = (equity_array - running_max) / running_max
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0

        # Sharpe Ratio (assuming 252 trading days, 0% risk-free rate)
        returns = np.diff(equity_array) / equity_array[:-1] if len(equity_array) > 1 else np.array([])
        sharpe = (np.mean(returns) / np.std(returns) * np.sqrt(252)) if len(returns) > 0 and np.std(returns) > 0 else 0

        # Sortino Ratio (downside deviation)
        downside_returns = returns[returns < 0]
        sortino = (np.mean(returns) / np.std(downside_returns) * np.sqrt(252)) if len(downside_returns) > 0 else sharpe

        # Profit Factor
        winning_pnl = sum(t.pnl for t in closed_trades if t.pnl > 0)
        losing_pnl = abs(sum(t.pnl for t in closed_trades if t.pnl < 0))
        profit_factor = winning_pnl / losing_pnl if losing_pnl > 0 else (1.0 if winning_pnl > 0 else 0)

        return BacktestResult(
            strategy_name="Custom Strategy",
            symbol=symbol,
            total_trades=len(closed_trades),
            winning_trades=winning,
            losing_trades=losing,
            win_rate=win_rate,
            total_pnl=total_pnl,
            avg_pnl_per_trade=avg_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe,
            sortino_ratio=sortino,
            profit_factor=profit_factor,
            start_date=start_date,
            end_date=end_date,
        )


def run_strategy_backtest(
    df: pd.DataFrame, strategy_func, symbol: str = "NIFTY", initial_capital: float = 100000
) -> BacktestResult:
    """
    Convenience function to run backtest

    Example:
        result = run_strategy_backtest(df, my_strategy_func, "NIFTY")
        print(result)
    """
    engine = BacktestEngine(initial_capital)
    return engine.run(df, strategy_func, symbol)
