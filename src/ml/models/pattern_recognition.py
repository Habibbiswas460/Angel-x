"""
Pattern Recognition Models

Uses scikit-learn (RandomForest) and optionally XGBoost.
Falls back to LogisticRegression if advanced models are unavailable.
"""

from typing import Optional, Dict
import numpy as np

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class PatternRecognizer:
    def __init__(self):
        self.model = None
        self.mode = "unknown"
        try:
            from sklearn.ensemble import RandomForestClassifier
            self.model = RandomForestClassifier(n_estimators=200, random_state=42)
            self.mode = "random_forest"
            logger.info("PatternRecognizer using RandomForestClassifier")
        except Exception as e:
            logger.warning(f"scikit-learn not available: {e}")
        
        if self.model is None:
            try:
                from sklearn.linear_model import LogisticRegression
                self.model = LogisticRegression(max_iter=1000)
                self.mode = "logistic_regression"
                logger.info("PatternRecognizer using LogisticRegression fallback")
            except Exception as e:
                logger.error(f"No ML models available: {e}")
                self.mode = "none"
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> Dict:
        if self.mode == "none" or self.model is None:
            return {"status": "error", "reason": "No model available"}
        self.model.fit(X, y)
        return {"status": "ok", "mode": self.mode}
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        if self.mode == "none" or self.model is None:
            return np.zeros((len(X),), dtype=np.int64)
        return self.model.predict(X)
