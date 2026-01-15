"""
ML Data Pipeline

- Collects data from API or CSVs
- Preprocesses with normalization and feature engineering
- Provides train/test splits and batch generators
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import pandas as pd
import numpy as np
import os
from pathlib import Path

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)

DEFAULT_FEATURES: Tuple[str, ...] = ("close", "volume", "SMA_20", "RSI_14", "ATR_14")


@dataclass
class PipelineConfig:
    lookback: int = 60
    forecast_horizon: int = 10
    normalize: bool = True
    features: Tuple[str, ...] = DEFAULT_FEATURES

    @property
    def horizon(self) -> int:
        """Backward-compatible alias."""
        return self.forecast_horizon


class DataPipeline:
    def __init__(
        self,
        lookback: int = 60,
        forecast_horizon: int = 10,
        normalize: bool = True,
        features: Optional[Tuple[str, ...]] = None,
        config: Optional[PipelineConfig] = None,
    ):
        if config is not None:
            self.config = config
        else:
            self.config = PipelineConfig(
                lookback=lookback,
                forecast_horizon=forecast_horizon,
                normalize=normalize,
                features=tuple(features) if features is not None else DEFAULT_FEATURES,
            )
        # Expose commonly-used parameters directly
        self.lookback = self.config.lookback
        self.forecast_horizon = self.config.forecast_horizon

        logger.info(f"ML DataPipeline initialized (lookback={self.lookback}, horizon={self.forecast_horizon})")

    def load_csv(self, path: str) -> pd.DataFrame:
        """Load market data from CSV file.
        
        Args:
            path: Absolute or relative path to CSV file
            
        Returns:
            DataFrame with market data
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        df = pd.read_csv(path)
        logger.info(f"Loaded CSV with {len(df)} rows: {path}")
        return df

    def from_api(self, data: List[Dict]) -> pd.DataFrame:
        """Convert API response data to DataFrame.
        
        Args:
            data: List of dictionaries from API response
            
        Returns:
            DataFrame with market data
        """
        df = pd.DataFrame(data)
        logger.info(f"Loaded API data rows: {len(df)}")
        return df

    def calculate_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate technical indicators and features for ML.
        
        Adds SMA_20, RSI_14, ATR_14, moving averages, and normalizes data.
        
        Args:
            df: Raw market data DataFrame
            
        Returns:
            DataFrame with calculated features and normalized values
        """
        cfg = self.config
        df = df.copy()

        # Fill missing and ensure numerical stability
        df = df.ffill().bfill()

        # Ensure optional option Greeks exist to avoid KeyErrors during normalization
        for col in ["delta", "gamma", "theta", "vega", "iv"]:
            if col not in df.columns:
                df[col] = 0.0

        # Core price-based indicators
        df["SMA_20"] = df["close"].rolling(20).mean().bfill()
        df["RSI_14"] = self._rsi(df["close"], 14)

        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["ATR_14"] = true_range.rolling(14).mean().bfill()

        # Additional short/long horizon helpers
        df["return"] = df["close"].pct_change().fillna(0.0)
        df["ma_5"] = df["close"].rolling(5).mean().bfill()
        df["ma_20"] = df["close"].rolling(20).mean().bfill()
        df["rsi_14"] = self._rsi(df["close"], 14)

        # Ensure configured feature columns exist (fall back to zeros)
        for col in cfg.features:
            if col not in df.columns:
                df[col] = 0.0

        if cfg.normalize:
            numeric_cols = ["close", "volume", "delta", "gamma", "theta", "vega", "iv", "ma_5", "ma_20", "rsi_14"]
            for col in numeric_cols:
                df[col] = (df[col] - df[col].mean()) / (df[col].std() + 1e-9)

        return df

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        # Backwards-compatible wrapper
        return self.calculate_features(df)

    def create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Create input sequences for time series prediction.
        
        Args:
            df: Market data DataFrame
            
        Returns:
            Tuple of (X, y) where X is 3D array of sequences (samples, lookback, features)
            and y is 1D array of binary labels (1 for positive return, 0 for negative)
        """
        cfg = self.config
        df = self.calculate_features(df)
        feature_cols = list(cfg.features) + ["ma_5", "ma_20", "rsi_14", "return"]
        values = df[feature_cols].values
        X, y = [], []
        for i in range(cfg.lookback, len(values) - cfg.forecast_horizon):
            X.append(values[i - cfg.lookback : i])
            # Predict future return sum over horizon (direction)
            future_returns = df["return"].iloc[i : i + cfg.forecast_horizon].sum()
            y.append(1 if future_returns > 0 else 0)
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64)
        logger.info(f"Sequences created: X={X.shape}, y={y.shape}")
        return X, y

    def train_test_split(
        self, X: np.ndarray, y: np.ndarray, test_size: float = 0.2
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Split data into training and testing sets.
        
        Args:
            X: Feature array
            y: Label array
            test_size: Fraction of data to use for testing (default 0.2)
            
        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        n = len(X)
        split = int(n * (1 - test_size))
        X_train, X_test = X[:split], X[split:]
        y_train, y_test = y[:split], y[split:]
        return X_train, X_test, y_train, y_test

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -1 * delta.clip(upper=0)
        ma_up = up.rolling(window=period).mean()
        ma_down = down.rolling(window=period).mean()
        rs = ma_up / (ma_down + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi.bfill()
