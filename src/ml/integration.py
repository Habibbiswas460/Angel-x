"""
ML Integration with Trading Engine

- Combines DataPipeline, LSTMPredictor, and PatternRecognizer
- Provides signals to trading engine via a simple interface
"""

from typing import Dict, Any
import numpy as np

from src.utils.logger import StrategyLogger
from .data_pipeline import DataPipeline, PipelineConfig
from .models.lstm_predictor import LSTMPredictor
from .models.pattern_recognition import PatternRecognizer

logger = StrategyLogger.get_logger(__name__)


class MLIntegration:
    def __init__(self):
        self.pipeline = DataPipeline(PipelineConfig())
        self.lstm: LSTMPredictor | None = None
        self.patterns: PatternRecognizer | None = None
    
    def initialize_models(self, input_size: int):
        self.lstm = LSTMPredictor(input_size=input_size)
        self.patterns = PatternRecognizer()
        logger.info("ML models initialized")
    
    def train(self, df) -> Dict[str, Any]:
        """Train ML models on data. Skip if sequences empty."""
        dfp = self.pipeline.preprocess(df)
        X, y = self.pipeline.create_sequences(dfp)
        
        # Guard: skip training on empty sequences
        if len(X) == 0:
            logger.warning("ML train: empty sequences, skipping")
            return {
                "lstm": None,
                "patterns": None,
                "train_samples": 0,
                "test_samples": 0,
                "skipped": True
            }
        
        (Xtr, ytr), (Xte, yte) = self.pipeline.train_test_split(X, y)
        
        self.initialize_models(input_size=X.shape[-1])
        lstm_info = self.lstm.fit(Xtr, ytr, epochs=2, batch_size=32)
        pat_info = self.patterns.fit(Xtr.reshape((len(Xtr), -1)), ytr)
        
        return {
            "lstm": lstm_info,
            "patterns": pat_info,
            "train_samples": len(Xtr),
            "test_samples": len(Xte),
            "skipped": False
        }
    
    def infer(self, df) -> Dict[str, Any]:
        """Infer predictions. Return empty if models not trained."""
        # Guard: no-op if models missing
        if self.lstm is None or self.patterns is None:
            logger.warning("ML infer: models not trained, returning empty")
            return {
                "direction_preds": [],
                "class_preds": [],
                "skipped": True
            }
        
        try:
            dfp = self.pipeline.preprocess(df)
            X, y = self.pipeline.create_sequences(dfp)
            
            # Guard: skip on empty sequences
            if len(X) == 0:
                logger.debug("ML infer: empty sequences")
                return {
                    "direction_preds": [],
                    "class_preds": [],
                    "skipped": True
                }
            
            preds_dir = self.lstm.predict(X)
            preds_cls = self.patterns.predict(X.reshape((len(X), -1)))
            
            return {
                "direction_preds": preds_dir.tolist(),
                "class_preds": preds_cls.tolist(),
                "skipped": False
            }
        except Exception as e:
            logger.error(f"ML infer error: {e}")
            return {
                "direction_preds": [],
                "class_preds": [],
                "error": str(e),
                "skipped": True
            }
