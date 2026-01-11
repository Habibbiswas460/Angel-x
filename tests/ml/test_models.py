import pytest
import numpy as np
from src.ml.models.lstm_predictor import LSTMPredictor
from src.ml.models.pattern_recognition import PatternRecognition


class TestLSTMPredictor:
    
    @pytest.fixture
    def sample_sequences(self):
        """Create sample sequences for testing."""
        X = np.random.randn(50, 20, 11).astype(np.float32)  # 50 samples, 20 lookback, 11 features
        y = np.random.randn(50).astype(np.float32)
        return X, y
    
    def test_lstm_initialization(self):
        """Test LSTM model initializes."""
        model = LSTMPredictor(lookback=20, num_features=11)
        assert model.lookback == 20
        assert model.num_features == 11
    
    def test_lstm_predict_shape(self, sample_sequences):
        """Test LSTM predict returns correct shape."""
        X, y = sample_sequences
        model = LSTMPredictor(lookback=20, num_features=11)
        
        predictions = model.predict(X[:10])
        assert predictions.shape == (10,)
    
    def test_lstm_fallback_when_no_tf(self, sample_sequences):
        """Test LSTM falls back to MA when TensorFlow unavailable."""
        X, y = sample_sequences
        model = LSTMPredictor(lookback=20, num_features=11)
        
        # Even without TF, predict should return moving average fallback
        predictions = model.predict(X[:5])
        assert len(predictions) == 5
        assert not np.isnan(predictions).all()


class TestPatternRecognition:
    
    @pytest.fixture
    def sample_features(self):
        """Create sample feature data for testing."""
        X = np.random.randn(100, 50)  # 100 samples, 50 features
        y = np.random.randint(0, 2, 100)  # Binary classification
        return X, y
    
    def test_pattern_recognition_initialization(self):
        """Test PatternRecognition model initializes."""
        model = PatternRecognition(n_estimators=10)
        assert model.n_estimators == 10
    
    def test_pattern_recognition_fit(self, sample_features):
        """Test model fitting."""
        X, y = sample_features
        model = PatternRecognition(n_estimators=10)
        
        # Fit should not raise
        model.fit(X, y)
        assert model.model is not None
    
    def test_pattern_recognition_predict(self, sample_features):
        """Test model predictions."""
        X, y = sample_features
        model = PatternRecognition(n_estimators=10)
        model.fit(X, y)
        
        predictions = model.predict(X[:10])
        assert predictions.shape == (10,)
        assert np.all((predictions == 0) | (predictions == 1))
    
    def test_pattern_recognition_predict_proba(self, sample_features):
        """Test probability predictions."""
        X, y = sample_features
        model = PatternRecognition(n_estimators=10)
        model.fit(X, y)
        
        proba = model.predict_proba(X[:10])
        assert proba.shape == (10, 2)
        assert np.all(proba >= 0) and np.all(proba <= 1)
        assert np.allclose(proba.sum(axis=1), 1.0)
