"""
Pattern Recognition Models

Provides a small, dependency-light classifier with graceful fallbacks so tests
can run even when scikit-learn is not installed. When scikit-learn is available
we use a RandomForest (or LogisticRegression fallback); otherwise we fall back
to a simple majority-class heuristic.
"""

from typing import Optional
import numpy as np

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class PatternRecognition:
    """Minimal binary classifier with graceful fallbacks."""

    def __init__(self, n_estimators: int = 100):
        self.n_estimators = n_estimators
        self.model: Optional[object] = None
        self.majority_class: int = 0
        self.mode = "heuristic"

        # Try RandomForest first, then LogisticRegression, otherwise fallback.
        try:
            from sklearn.ensemble import RandomForestClassifier

            self.model = RandomForestClassifier(n_estimators=self.n_estimators, random_state=42)
            self.mode = "random_forest"
            logger.info("PatternRecognition using RandomForestClassifier")
        except Exception as exc:
            logger.warning(f"scikit-learn RandomForest unavailable: {exc}")

        if self.model is None:
            try:
                from sklearn.linear_model import LogisticRegression

                self.model = LogisticRegression(max_iter=500)
                self.mode = "logistic_regression"
                logger.info("PatternRecognition using LogisticRegression fallback")
            except Exception as exc:
                logger.warning(f"LogisticRegression unavailable: {exc}")
                self.mode = "heuristic"

    def fit(self, X: np.ndarray, y: np.ndarray) -> None:
        """Train the pattern recognition model.
        
        Uses RandomForest if available, falls back to LogisticRegression,
        or uses simple majority-class heuristic if scikit-learn unavailable.
        
        Args:
            X: Training features (2D array: samples, features)
            y: Training labels (1D array of binary classes)
        """
        if self.model is not None:
            try:
                self.model.fit(X, y)
                return
            except Exception as exc:
                logger.error(f"PatternRecognition fit failed, falling back: {exc}")

        # Heuristic fallback: store majority class
        self.majority_class = int(np.round(np.mean(y)))
        self.mode = "heuristic"

    def predict(self, X: np.ndarray) -> np.ndarray:
        """Predict class labels."""
        if self.model is not None:
            try:
                return self.model.predict(X)
            except Exception as exc:
                logger.error(f"PatternRecognition predict failed, fallback: {exc}")

        return np.full((len(X),), self.majority_class, dtype=np.int64)

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Predict class probabilities with sensible defaults."""
        if self.model is not None and hasattr(self.model, "predict_proba"):
            try:
                return self.model.predict_proba(X)
            except Exception as exc:
                logger.error(f"PatternRecognition predict_proba failed: {exc}")

        # Heuristic probability: majority class confidence
        proba = np.zeros((len(X), 2), dtype=np.float64)
        maj = self.majority_class
        proba[:, maj] = 1.0
        return proba


# Backwards compatibility alias
PatternRecognizer = PatternRecognition
