"""
LSTM Price Predictor

Attempts to use TensorFlow/Keras; if unavailable, falls back to a simple
moving-average predictor so the system remains functional without heavy deps.
"""

from typing import Optional, Dict
import numpy as np

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class LSTMPredictor:
    def __init__(self, input_size: int = None, hidden_units: int = 64, lookback: int = None, num_features: int = None):
        # Support both old (input_size) and new (lookback/num_features) signatures
        self.lookback = lookback or input_size
        self.num_features = num_features or hidden_units
        self.input_size = input_size or self.lookback
        self.hidden_units = hidden_units if num_features is None else num_features
        self._model = None
        self._fallback = True

        try:
            import tensorflow as tf  # noqa: F401
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense
            from tensorflow.keras.optimizers import Adam

            model = Sequential(
                [LSTM(self.hidden_units, input_shape=(None, self.input_size)), Dense(1, activation="sigmoid")]
            )
            model.compile(optimizer=Adam(1e-3), loss="binary_crossentropy", metrics=["accuracy"])
            self._model = model
            self._fallback = False
            logger.info("LSTM model initialized with TensorFlow/Keras")
        except Exception as e:
            logger.warning(f"TensorFlow/Keras not available. Using fallback MA predictor. ({e})")
            self._model = None
            self._fallback = True

    def fit(self, X: np.ndarray, y: np.ndarray, epochs: int = 5, batch_size: int = 32) -> Dict[str, object]:
        """Train the LSTM model or use fallback.
        
        Args:
            X: Training features (3D array: samples, timesteps, features)
            y: Training labels (1D array)
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Dictionary with training metadata (mode, loss/epochs)
        """
        if self._fallback:
            logger.info("Fallback predictor: no training required")
            return {"mode": "fallback", "epochs": 0}

        history = self._model.fit(X, y, epochs=epochs, batch_size=batch_size, verbose=0)
        return {"mode": "lstm", "loss": float(history.history["loss"][-1])}

    def predict(self, X: np.ndarray) -> np.ndarray:
        if self._fallback:
            # Fallback: predict up if last MA_5 > MA_20 in last step
            # Assuming features include ma_5 and ma_20 at the end
            ma5_idx = -3
            ma20_idx = -2
            last_ma5 = X[:, -1, ma5_idx]
            last_ma20 = X[:, -1, ma20_idx]
            preds = (last_ma5 > last_ma20).astype(np.int64)
            return preds

        probs = self._model.predict(X, verbose=0).reshape(-1)
        return (probs > 0.5).astype(np.int64)
