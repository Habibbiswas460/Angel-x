"""
Unit tests for Market Bias Engine
Tests: Market state detection, bias calculation, permission logic
"""

import pytest
from src.engines.market_bias.engine import BiasEngine, BiasState
from tests.fixtures.market_data import MockTick, MockGreeks


@pytest.mark.unit
class TestBiasEngine:
    """Test market bias detection engine"""
    
    def test_bullish_bias_detection(self):
        """Test detection of bullish market bias"""
        engine = BiasEngine()
        
        greeks = MockGreeks.sample(
            delta=0.55,      # > 0.45 threshold
            gamma=0.004,     # Rising
            iv=25.0
        )
        tick = MockTick.sample(ltp=101.0, volume=1100, oi=510000)
        prev_tick = MockTick.sample(ltp=100.0, volume=1000, oi=500000)
        
        bias = engine.detect_bias(
            current_tick=tick,
            previous_tick=prev_tick,
            greeks=greeks
        )
        
        assert bias == BiasState.BULLISH or bias == "BULLISH"
    
    def test_bearish_bias_detection(self):
        """Test detection of bearish market bias"""
        engine = BiasEngine()
        
        greeks = MockGreeks.sample(
            delta=-0.55,     # < -0.45 threshold
            gamma=0.004,
            iv=25.0
        )
        tick = MockTick.sample(ltp=99.0, volume=1100, oi=510000)
        prev_tick = MockTick.sample(ltp=100.0, volume=1000, oi=500000)
        
        bias = engine.detect_bias(
            current_tick=tick,
            previous_tick=prev_tick,
            greeks=greeks
        )
        
        assert bias == BiasState.BEARISH or bias == "BEARISH"
    
    def test_no_bias_on_weak_delta(self):
        """Test no trade signal when delta is weak"""
        engine = BiasEngine()
        
        greeks = MockGreeks.sample(delta=0.35)  # < 0.45 threshold
        tick = MockTick.sample(ltp=101.0)
        prev_tick = MockTick.sample(ltp=100.0)
        
        bias = engine.detect_bias(
            current_tick=tick,
            previous_tick=prev_tick,
            greeks=greeks
        )
        
        assert bias == "NO_BIAS"  # No trade signal expected
    
    def test_oi_price_mismatch_detection(self):
        """Test trap detection: OI rising but price flat"""
        engine = BiasEngine()
        
        tick = MockTick.sample(ltp=100.0, oi=520000)
        prev_tick = MockTick.sample(ltp=100.0, oi=500000)
        
        greeks = MockGreeks.sample(delta=0.55, gamma=0.001)
        
        has_trap = engine.detect_oi_trap(
            current_tick=tick,
            previous_tick=prev_tick,
            greeks=greeks
        )
        
        # OI rising but price flat = trap signal
        assert has_trap is True
    
    def test_gamma_rising_requirement(self):
        """Test gamma must be rising for valid bias"""
        engine = BiasEngine()
        
        greeks_prev = MockGreeks.sample(gamma=0.004)
        greeks_curr = MockGreeks.sample(gamma=0.003)  # Falling
        
        is_gamma_rising = engine.is_gamma_rising(
            current_gamma=greeks_curr.gamma,
            previous_gamma=greeks_prev.gamma
        )
        
        assert is_gamma_rising is False
    
    def test_volatility_threshold_filters(self):
        """Test IV extremes cause no trade"""
        engine = BiasEngine()
        
        # Very low IV
        greeks_low = MockGreeks.sample(iv=12.0)
        allowed_low = engine.is_volatility_acceptable(iv=greeks_low.iv)
        assert allowed_low is False
        
        # Very high IV
        greeks_high = MockGreeks.sample(iv=55.0)
        allowed_high = engine.is_volatility_acceptable(iv=greeks_high.iv)
        assert allowed_high is False
        
        # Safe zone
        greeks_safe = MockGreeks.sample(iv=25.0)
        allowed_safe = engine.is_volatility_acceptable(iv=greeks_safe.iv)
        assert allowed_safe is True
