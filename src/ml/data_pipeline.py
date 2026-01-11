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


@dataclass
class PipelineConfig:
    lookback: int = 60
    horizon: int = 10
    normalize: bool = True
    features: Tuple[str, ...] = (
        'close', 'volume', 'delta', 'gamma', 'theta', 'vega', 'iv'
    )


class DataPipeline:
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        logger.info("ML DataPipeline initialized")
    
    def load_csv(self, path: str) -> pd.DataFrame:
        if not os.path.exists(path):
            raise FileNotFoundError(f"CSV not found: {path}")
        df = pd.read_csv(path)
        logger.info(f"Loaded CSV with {len(df)} rows: {path}")
        return df
    
    def from_api(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)
        logger.info(f"Loaded API data rows: {len(df)}")
        return df
    
    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        cfg = self.config
        df = df.copy()
        
        # Fill missing
        df = df.ffill().bfill()
        
        # Ensure required features
        for col in cfg.features:
            if col not in df.columns:
                df[col] = 0.0
        
        # Add technical features
        df['return'] = df['close'].pct_change().fillna(0.0)
        df['ma_5'] = df['close'].rolling(5).mean().bfill()
        df['ma_20'] = df['close'].rolling(20).mean().bfill()
        df['rsi_14'] = self._rsi(df['close'], 14)
        
        # Normalize if requested
        if cfg.normalize:
            for col in ['close','volume','delta','gamma','theta','vega','iv','ma_5','ma_20','rsi_14']:
                df[col] = (df[col] - df[col].mean()) / (df[col].std() + 1e-9)
        
        return df
    
    def create_sequences(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        cfg = self.config
        feature_cols = list(cfg.features) + ['ma_5','ma_20','rsi_14','return']
        values = df[feature_cols].values
        X, y = [], []
        for i in range(cfg.lookback, len(values) - cfg.horizon):
            X.append(values[i - cfg.lookback:i])
            # Predict future return sum over horizon (direction)
            future_returns = df['return'].iloc[i:i+cfg.horizon].sum()
            y.append(1 if future_returns > 0 else 0)
        X = np.array(X, dtype=np.float32)
        y = np.array(y, dtype=np.int64)
        logger.info(f"Sequences created: X={X.shape}, y={y.shape}")
        return X, y
    
    def train_test_split(self, X: np.ndarray, y: np.ndarray, test_ratio: float = 0.2):
        n = len(X)
        split = int(n * (1 - test_ratio))
        return (X[:split], y[:split]), (X[split:], y[split:])
    
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
