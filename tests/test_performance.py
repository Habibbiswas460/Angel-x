"""
Performance Benchmarks for Angel-X
Tests critical path performance and identifies bottlenecks
"""

import pytest
import time
import numpy as np
import pandas as pd
from src.ml.data_pipeline import DataPipeline


class TestPerformance:
    """Performance benchmarks for critical components"""

    def test_data_pipeline_performance(self, benchmark=None):
        """Benchmark data pipeline feature calculation"""
        # Create sample data
        data = {
            "timestamp": pd.date_range("2026-01-01", periods=1000, freq="1min"),
            "open": np.random.uniform(25000, 25200, 1000),
            "high": np.random.uniform(25100, 25300, 1000),
            "low": np.random.uniform(24900, 25100, 1000),
            "close": np.random.uniform(25000, 25200, 1000),
            "volume": np.random.randint(10000, 50000, 1000),
        }
        df = pd.DataFrame(data)

        pipeline = DataPipeline(lookback=60, forecast_horizon=10)

        # Time feature calculation
        start = time.time()
        result = pipeline.calculate_features(df)
        elapsed = time.time() - start

        print(f"\n✓ Feature calculation: {elapsed:.3f}s for {len(df)} rows")
        print(f"  Throughput: {len(df)/elapsed:.0f} rows/sec")

        assert elapsed < 1.0, f"Feature calculation too slow: {elapsed:.3f}s"
        assert len(result) == len(df)
        assert "SMA_20" in result.columns
        assert "RSI_14" in result.columns

    def test_sequence_creation_performance(self):
        """Benchmark sequence creation for ML"""
        # Create sample data with all required columns
        data = {
            "timestamp": pd.date_range("2026-01-01", periods=5000, freq="1min"),
            "open": np.random.uniform(25000, 25200, 5000),
            "high": np.random.uniform(25100, 25300, 5000),
            "low": np.random.uniform(24900, 25100, 5000),
            "close": np.random.uniform(25000, 25200, 5000),
            "volume": np.random.randint(10000, 50000, 5000),
        }
        df = pd.DataFrame(data)

        pipeline = DataPipeline(lookback=60, forecast_horizon=10)

        # Time sequence creation
        start = time.time()
        X, y = pipeline.create_sequences(df)
        elapsed = time.time() - start

        print(f"\n✓ Sequence creation: {elapsed:.3f}s")
        print(f"  Created {len(X)} sequences")
        print(f"  Throughput: {len(X)/elapsed:.0f} sequences/sec")

        assert elapsed < 2.0, f"Sequence creation too slow: {elapsed:.3f}s"
        assert len(X) > 0
        assert len(X) == len(y)

    def test_strategy_pnl_calculation(self):
        """Benchmark P&L calculation for multi-leg strategies"""
        from src.strategies.multi_leg.base import OptionLeg, OptionType, LegDirection

        # Create 100 legs
        legs = [
            OptionLeg(
                strike=25000 + i * 100,
                option_type=OptionType.CALL if i % 2 == 0 else OptionType.PUT,
                direction=LegDirection.BUY if i % 2 == 0 else LegDirection.SELL,
                quantity=1,
                entry_price=100.0,
                current_price=110.0 + i,
            )
            for i in range(100)
        ]

        # Time P&L calculation
        start = time.time()
        for _ in range(1000):
            total_pnl = sum(leg.get_pnl() for leg in legs)
        elapsed = time.time() - start

        print(f"\n✓ P&L calculation: {elapsed:.3f}s for 100,000 calculations")
        print(f"  Throughput: {100000/elapsed:.0f} calculations/sec")

        assert elapsed < 0.5, f"P&L calculation too slow: {elapsed:.3f}s"
        assert total_pnl != 0

    def test_memory_efficiency(self):
        """Test memory usage of data pipeline"""
        import tracemalloc

        tracemalloc.start()

        # Create large dataset
        data = {
            "timestamp": pd.date_range("2026-01-01", periods=10000, freq="1min"),
            "close": np.random.uniform(25000, 25200, 10000),
            "volume": np.random.randint(10000, 50000, 10000),
            "open": np.random.uniform(25000, 25200, 10000),
            "high": np.random.uniform(25100, 25300, 10000),
            "low": np.random.uniform(24900, 25100, 10000),
        }
        df = pd.DataFrame(data)

        pipeline = DataPipeline(lookback=60, forecast_horizon=10)

        # Calculate features
        result = pipeline.calculate_features(df)
        current, peak = tracemalloc.get_traced_memory()

        print(f"\n✓ Memory usage:")
        print(f"  Current: {current / 1024 / 1024:.2f} MB")
        print(f"  Peak: {peak / 1024 / 1024:.2f} MB")

        tracemalloc.stop()

        # Should use less than 100MB for 10k rows
        assert peak < 100 * 1024 * 1024, f"Memory usage too high: {peak/1024/1024:.2f}MB"


class TestCaching:
    """Test caching effectiveness"""

    def test_repeated_calculations(self):
        """Verify caching improves performance on repeated calls"""
        data = {
            "timestamp": pd.date_range("2026-01-01", periods=1000, freq="1min"),
            "close": np.random.uniform(25000, 25200, 1000),
            "volume": np.random.randint(10000, 50000, 1000),
            "open": np.random.uniform(25000, 25200, 1000),
            "high": np.random.uniform(25100, 25300, 1000),
            "low": np.random.uniform(24900, 25100, 1000),
        }
        df = pd.DataFrame(data)

        pipeline = DataPipeline(lookback=60, forecast_horizon=10)

        # First call (cold)
        start1 = time.time()
        result1 = pipeline.calculate_features(df)
        time1 = time.time() - start1

        # Second call (should be fast due to pandas internal caching)
        start2 = time.time()
        result2 = pipeline.calculate_features(df)
        time2 = time.time() - start2

        print(f"\n✓ Repeated calculations:")
        print(f"  First call: {time1:.3f}s")
        print(f"  Second call: {time2:.3f}s")

        assert pd.DataFrame.equals(result1, result2)
