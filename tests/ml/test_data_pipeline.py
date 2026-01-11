import pytest
import numpy as np
import pandas as pd
from src.ml.data_pipeline import DataPipeline


class TestDataPipeline:
    
    @pytest.fixture
    def sample_data(self):
        """Create sample OHLCV data for testing."""
        dates = pd.date_range("2025-01-01", periods=100, freq="1min")
        data = pd.DataFrame({
            "timestamp": dates,
            "open": np.random.uniform(100, 150, 100),
            "high": np.random.uniform(100, 150, 100),
            "low": np.random.uniform(100, 150, 100),
            "close": np.random.uniform(100, 150, 100),
            "volume": np.random.randint(100, 1000, 100),
        })
        return data
    
    def test_pipeline_initialization(self):
        """Test DataPipeline initializes with correct parameters."""
        pipeline = DataPipeline(lookback=20, forecast_horizon=5)
        assert pipeline.lookback == 20
        assert pipeline.forecast_horizon == 5
    
    def test_calculate_features(self, sample_data):
        """Test feature calculation adds technical indicators."""
        pipeline = DataPipeline(lookback=20, forecast_horizon=5)
        features_df = pipeline.calculate_features(sample_data)
        
        # Check that SMA and RSI columns were added
        assert "SMA_20" in features_df.columns
        assert "RSI_14" in features_df.columns
        assert "ATR_14" in features_df.columns
    
    def test_create_sequences(self, sample_data):
        """Test sequence creation for ML models."""
        pipeline = DataPipeline(lookback=20, forecast_horizon=5)
        X, y = pipeline.create_sequences(sample_data)
        
        # X should be 3D: (samples, lookback, features)
        assert len(X.shape) == 3
        assert X.shape[1] == 20  # lookback window
        
        # y should be 1D: (samples,)
        assert len(y.shape) == 1
        
        # y length should match X length
        assert X.shape[0] == y.shape[0]
    
    def test_train_test_split(self, sample_data):
        """Test train/test split."""
        pipeline = DataPipeline(lookback=20, forecast_horizon=5)
        X, y = pipeline.create_sequences(sample_data)
        
        X_train, X_test, y_train, y_test = pipeline.train_test_split(X, y, test_size=0.2)
        
        assert X_train.shape[0] + X_test.shape[0] == X.shape[0]
        assert y_train.shape[0] + y_test.shape[0] == y.shape[0]
        assert X_train.shape[1] == X.shape[1]  # lookback preserved
    
    def test_pipeline_end_to_end(self, sample_data):
        """Test full pipeline from raw data to sequences."""
        pipeline = DataPipeline(lookback=20, forecast_horizon=5)
        features_df = pipeline.calculate_features(sample_data)
        X, y = pipeline.create_sequences(features_df)
        
        assert X.shape[0] > 0
        assert y.shape[0] > 0
        assert not np.isnan(X).all()
        assert not np.isnan(y).all()
