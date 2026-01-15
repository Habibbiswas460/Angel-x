"""
Tick Data Loader
Load and process market data from various sources
"""

from typing import Optional, Dict, List
from pathlib import Path
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TickDataLoader:
    """Load tick data from CSV, JSON, or broker"""

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load tick data from CSV"""
        filepath = self.data_dir / filename

        if not filepath.exists():
            logger.error(f"File not found: {filepath}")
            return pd.DataFrame()

        try:
            df = pd.read_csv(
                filepath, parse_dates=["time"] if "time" in pd.read_csv(filepath, nrows=1).columns else ["timestamp"]
            )
            logger.info(f"Loaded {len(df)} ticks from {filename}")
            return df

        except Exception as e:
            logger.error(f"Error loading CSV: {e}")
            return pd.DataFrame()

    def load_ticks_csv(self, filename: str) -> pd.DataFrame:
        """Load tick data (ticks_YYYYMMDD.csv format)"""
        df = self.load_csv(filename)

        if df.empty:
            return df

        # Standardize columns: timestamp, ltp, bid, ask, volume
        if "ltp" not in df.columns and "price" in df.columns:
            df = df.rename(columns={"price": "ltp"})

        if "timestamp" not in df.columns and "time" in df.columns:
            df = df.rename(columns={"time": "timestamp"})

        # Parse timestamp
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df = df.set_index("timestamp").sort_index()

        logger.info(f"Loaded ticks: {filename} | Rows: {len(df)} | Date: {df.index[0] if len(df) > 0 else 'N/A'}")
        return df

    def convert_ticks_to_ohlcv(self, df: pd.DataFrame, period: str = "1min") -> pd.DataFrame:
        """Convert tick data to OHLCV candles"""
        if df.empty:
            return df

        if "ltp" not in df.columns:
            logger.error("Tick data must have 'ltp' column")
            return pd.DataFrame()

        try:
            ohlcv = (
                df["ltp"]
                .resample(period)
                .agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "count"})
            )

            ohlcv = ohlcv.dropna()
            logger.info(f"Converted to OHLCV ({period}): {len(ohlcv)} candles")
            return ohlcv

        except Exception as e:
            logger.error(f"Error converting ticks to OHLCV: {e}")
            return pd.DataFrame()

    def find_latest_tick_file(self) -> Optional[str]:
        """Find latest ticks_YYYYMMDD.csv file"""
        ticks_dir = Path("ticks")
        if not ticks_dir.exists():
            return None

        tick_files = sorted(ticks_dir.glob("ticks_*.csv"), reverse=True)
        if tick_files:
            return tick_files[0].name
        return None

    def load_latest_ticks(self) -> pd.DataFrame:
        """Load latest tick file from ticks/ directory"""
        latest = self.find_latest_tick_file()
        if not latest:
            logger.warning("No tick files found in ticks/")
            return pd.DataFrame()

        df = self.load_ticks_csv(f"../ticks/{latest}")
        return df

    def find_all_tick_files(self) -> List[str]:
        """Find all tick CSV files"""
        ticks_dir = Path("ticks")
        if not ticks_dir.exists():
            return []

        return sorted([f.name for f in ticks_dir.glob("ticks_*.csv")])

    @staticmethod
    def create_synthetic_ticks(
        num_ticks: int = 100, start_price: float = 20000, volatility: float = 0.005
    ) -> pd.DataFrame:
        """Create synthetic tick data for testing"""
        timestamps = pd.date_range(start="2026-01-10 09:15", periods=num_ticks, freq="1s")
        prices = start_price + np.random.normal(0, start_price * volatility, num_ticks)
        prices = np.maximum(prices, 100)  # Ensure positive

        df = pd.DataFrame(
            {
                "timestamp": timestamps,
                "ltp": prices,
                "bid": prices - 1,
                "ask": prices + 1,
                "volume": np.random.randint(1, 100, num_ticks),
            }
        )

        df = df.set_index("timestamp")
        logger.info(f"Created synthetic ticks: {num_ticks} rows")
        return df


def load_backtest_data(symbol: str = "NIFTY", period: str = "1min") -> pd.DataFrame:
    """
    Convenience function to load backtest data

    Tries multiple sources:
    1. Latest tick file from ticks/
    2. Pre-computed OHLCV from data/
    3. Synthetic data if nothing available
    """
    loader = TickDataLoader()

    # Try loading latest ticks
    df_ticks = loader.load_latest_ticks()
    if not df_ticks.empty:
        df_ohlcv = loader.convert_ticks_to_ohlcv(df_ticks, period)
        if not df_ohlcv.empty:
            logger.info(f"✓ Loaded backtest data from ticks: {len(df_ohlcv)} candles")
            return df_ohlcv

    # Try loading from data/ directory
    try:
        df_csv = pd.read_csv(f"data/{symbol}_ohlcv.csv", parse_dates=["timestamp"])
        df_csv = df_csv.set_index("timestamp")
        logger.info(f"✓ Loaded backtest data from data/: {len(df_csv)} candles")
        return df_csv
    except FileNotFoundError:
        pass

    # Create synthetic data
    logger.warning("No tick data found; using synthetic data for backtest")
    df_synthetic = TickDataLoader.create_synthetic_ticks(500)
    df_ohlcv = loader.convert_ticks_to_ohlcv(df_synthetic, period)
    return df_ohlcv
