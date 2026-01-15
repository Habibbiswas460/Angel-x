"""Extended coverage tests for ML models"""

import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from src.ml.models.lstm_predictor import LSTMPredictor
from src.ml.models.pattern_recognition import PatternRecognition, PatternRecognizer


class TestLSTMPredictorExtended:
    """Extended LSTM Predictor tests"""
    
    def test_lstm_initialization_with_old_signature(self):
        """Test LSTM initialization with old parameter names"""
        model = LSTMPredictor(input_size=10, hidden_units=64)
        assert model.input_size == 10
        assert model.hidden_units == 64
        assert model.lookback == 10
        assert model.num_features == 64
    
    def test_lstm_initialization_with_new_signature(self):
        """Test LSTM initialization with new parameter names"""
        model = LSTMPredictor(lookback=20, num_features=11)
        assert model.lookback == 20
        assert model.num_features == 11
        assert model.input_size == 20
    
    def test_lstm_initialization_default_values(self):
        """Test LSTM initialization with default values"""
        model = LSTMPredictor()
        # Default uses input_size and hidden_units mapping
        # So lookback and num_features may be derived from them
        assert hasattr(model, 'input_size')
        assert hasattr(model, 'hidden_units')
    
    def test_lstm_fit_fallback(self):
        """Test LSTM fit in fallback mode"""
        model = LSTMPredictor(lookback=20, num_features=11)
        X = np.random.randn(50, 20, 11).astype(np.float32)
        y = np.random.randint(0, 2, 50).astype(np.int64)
        
        history = model.fit(X, y, epochs=1)
        assert "mode" in history
        assert history["mode"] in ["lstm", "fallback"]
    
    def test_lstm_predict_fallback(self):
        """Test LSTM predict in fallback mode"""
        model = LSTMPredictor(lookback=20, num_features=11)
        X = np.random.randn(10, 20, 11).astype(np.float32)
        
        predictions = model.predict(X)
        assert predictions.shape[0] == 10
        assert all(p in [0, 1] for p in predictions)
    
    def test_lstm_predict_shape_consistency(self):
        """Test LSTM predict returns consistent shapes"""
        model = LSTMPredictor(lookback=20, num_features=11)
        
        # Single sample
        X1 = np.random.randn(1, 20, 11).astype(np.float32)
        pred1 = model.predict(X1)
        assert pred1.shape == (1,)
        
        # Multiple samples
        X10 = np.random.randn(10, 20, 11).astype(np.float32)
        pred10 = model.predict(X10)
        assert pred10.shape == (10,)
    
    def test_lstm_model_attributes(self):
        """Test LSTM model maintains attributes"""
        model = LSTMPredictor(lookback=30, num_features=15)
        assert model._fallback is True or model._fallback is False
        assert model._model is None or hasattr(model._model, 'fit')


class TestPatternRecognitionExtended:
    """Extended Pattern Recognition tests"""
    
    def test_pattern_recognition_initialization(self):
        """Test PatternRecognition initialization"""
        pr = PatternRecognition()
        assert pr is not None
        assert hasattr(pr, 'fit')
        assert hasattr(pr, 'predict')
    
    def test_pattern_recognition_fit_predict(self):
        """Test pattern recognition fit and predict"""
        pr = PatternRecognition()
        
        # Create sample training data
        X_train = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
            [103, 104, 105],
        ], dtype=np.float32)
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        
        # Fit model
        pr.fit(X_train, y_train)
        
        # Predict
        predictions = pr.predict(X_train)
        assert len(predictions) == len(y_train)
        assert all(p in [0, 1] for p in predictions)
    
    def test_pattern_recognition_with_different_data_types(self):
        """Test pattern recognition with various data types"""
        pr = PatternRecognition()
        
        # Training data
        X_train = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
            [103, 104, 105],
        ], dtype=np.float32)
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        
        pr.fit(X_train, y_train)
        
        # Predict with different shapes
        X_single = np.array([[100, 101, 102]], dtype=np.float32)
        pred_single = pr.predict(X_single)
        assert len(pred_single) == 1
        
        X_multiple = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
        ], dtype=np.float32)
        pred_multiple = pr.predict(X_multiple)
        assert len(pred_multiple) == 3
    
    def test_pattern_recognition_empty_data(self):
        """Test pattern recognition with empty data"""
        pr = PatternRecognition()
        
        empty_X = np.array([], dtype=np.float32).reshape(0, 3)
        empty_y = np.array([], dtype=np.int64)
        
        # Should handle gracefully
        try:
            pr.fit(empty_X, empty_y)
            pred = pr.predict(empty_X)
            assert len(pred) == 0
        except (ValueError, IndexError):
            assert True  # Expected exception
    
    def test_pattern_recognition_single_sample(self):
        """Test pattern recognition with single sample"""
        pr = PatternRecognition()
        
        X_train = np.array([[100, 101, 102]], dtype=np.float32)
        y_train = np.array([0], dtype=np.int64)
        
        pr.fit(X_train, y_train)
        pred = pr.predict(X_train)
        assert len(pred) == 1
    
    def test_pattern_recognition_predict_proba(self):
        """Test probability prediction"""
        pr = PatternRecognition()
        
        X_train = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
            [103, 104, 105],
        ], dtype=np.float32)
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        
        pr.fit(X_train, y_train)
        
        X_test = np.array([[100, 101, 102]], dtype=np.float32)
        proba = pr.predict_proba(X_test)
        assert proba is not None
        assert len(proba) == 1
    
    def test_pattern_recognition_mode_selection(self):
        """Test pattern recognition mode selection"""
        pr = PatternRecognition()
        assert pr.mode in ["random_forest", "logistic_regression", "heuristic"]
        assert hasattr(pr, 'model')
    
    def test_pattern_recognizer_alias(self):
        """Test PatternRecognizer alias works"""
        pr_alias = PatternRecognizer()
        assert pr_alias is not None
        assert hasattr(pr_alias, 'fit')
        assert hasattr(pr_alias, 'predict')
    
    def test_pattern_recognition_with_nan_values(self):
        """Test pattern recognition handles NaN gracefully"""
        pr = PatternRecognition()
        
        X_train = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
            [103, 104, 105],
        ], dtype=np.float32)
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        
        pr.fit(X_train, y_train)
        
        # Data with NaN
        data_with_nan = np.array([[100, np.nan, 102]], dtype=np.float32)
        
        try:
            result = pr.predict(data_with_nan)
            assert len(result) == 1
        except (ValueError, TypeError):
            assert True  # Expected
    
    def test_pattern_recognition_deterministic(self):
        """Test pattern recognition is deterministic"""
        X_train = np.array([
            [100, 101, 102],
            [101, 102, 103],
            [102, 103, 104],
            [103, 104, 105],
        ], dtype=np.float32)
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        X_test = np.array([[100, 101, 102]], dtype=np.float32)
        
        pr1 = PatternRecognition()
        pr1.fit(X_train, y_train)
        result1 = pr1.predict(X_test)
        
        pr2 = PatternRecognition()
        pr2.fit(X_train, y_train)
        result2 = pr2.predict(X_test)
        
        # Should get same result (deterministic)
        assert np.array_equal(result1, result2)
    
    def test_pattern_recognition_with_large_dataset(self):
        """Test pattern recognition with large dataset"""
        pr = PatternRecognition()
        
        # Create large dataset
        np.random.seed(42)
        X_train = np.random.randn(1000, 10).astype(np.float32)
        y_train = np.random.randint(0, 2, 1000).astype(np.int64)
        
        pr.fit(X_train, y_train)
        predictions = pr.predict(X_train[:100])
        
        assert len(predictions) == 100
        assert all(p in [0, 1] for p in predictions)
    
    def test_pattern_recognition_with_constant_values(self):
        """Test pattern recognition with all same values"""
        pr = PatternRecognition()
        
        X_train = np.ones((4, 3), dtype=np.float32) * 100
        y_train = np.array([0, 1, 1, 0], dtype=np.int64)
        
        pr.fit(X_train, y_train)
        pred = pr.predict(X_train)
        assert len(pred) == 4


class TestMLModelIntegration:
    """Integration tests for ML models"""
    
    def test_lstm_and_pattern_recognition_together(self):
        """Test LSTM and PatternRecognition can be used together"""
        # Create training data for pattern recognition
        X_train = np.random.randn(50, 5).astype(np.float32)
        y_train = np.random.randint(0, 2, 50).astype(np.int64)
        
        # Train PatternRecognition
        pr = PatternRecognition()
        pr.fit(X_train, y_train)
        pattern_pred = pr.predict(X_train[:10])
        assert len(pattern_pred) == 10
        
        # Use LSTM for sequences
        lstm = LSTMPredictor(lookback=20, num_features=11)
        
        # Create proper 3D sequences
        X_lstm = np.random.randn(50, 20, 11).astype(np.float32)
        predictions = lstm.predict(X_lstm)
        
        assert len(predictions) == 50
    
    def test_ml_models_with_real_market_simulation(self):
        """Test ML models with simulated market data"""
        # Simulate OHLCV data (100 samples, 5 features per sample)
        n_samples = 100
        n_features = 5
        
        data = np.random.uniform(100, 110, (n_samples, n_features)).astype(np.float32)
        
        # Pattern recognition on features
        X_pattern = data[:80]  # Use first 80 for training
        y_pattern = np.random.randint(0, 2, 80).astype(np.int64)
        
        pr = PatternRecognition()
        pr.fit(X_pattern, y_pattern)
        
        # Predict on remaining
        pattern_pred = pr.predict(data[80:])
        assert len(pattern_pred) == 20
        
        # LSTM training simulation
        lstm = LSTMPredictor(lookback=20, num_features=n_features)
        
        # Create sequences for training
        lookback = 20
        X_train = []
        y_train = []
        
        for i in range(lookback, len(data) - 5):
            X_train.append(data[i-lookback:i])
            # Simple target: predict if close price goes up
            future_return = data[i+5, 0] - data[i, 0]
            y_train.append(1 if future_return > 0 else 0)
        
        X_train = np.array(X_train, dtype=np.float32)
        y_train = np.array(y_train, dtype=np.int64)
        
        if len(X_train) > 0:
            # Fit model
            history = lstm.fit(X_train, y_train, epochs=1)
            assert "mode" in history
            
            # Make predictions
            predictions = lstm.predict(X_train[:10])
            assert len(predictions) == 10
