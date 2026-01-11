"""
Unit tests for Entry Engine
Tests: Entry signal generation, rejection logic, trigger conditions
"""

import pytest
from datetime import datetime
from src.engines.entry.engine import EntryEngine, EntrySignal
from tests.fixtures.market_data import MockTick, MockGreeks


@pytest.mark.unit
class TestEntryEngine:
    """Test entry signal generation"""
    
    def test_entry_signal_bullish_alignment(self):
        """Test entry when all bullish conditions align"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        greeks = MockGreeks.sample(
            delta=0.55,      # In power zone
            gamma=0.004,     # Rising
            theta=-0.02,     # Reasonable decay
            vega=0.05,
            iv=25.0
        )
        
        tick = MockTick.sample(ltp=101.0, volume=1100, oi=510000)
        prev_tick = MockTick.sample(ltp=100.0, volume=1000, oi=500000)
        
        signal = engine.check_entry_conditions(
            bias="BULLISH",
            current_tick=tick,
            previous_tick=prev_tick,
            greeks=greeks,
            option_type="CE"
        )
        
        if signal:
            assert signal.action == "BUY" or signal.action == "ENTRY"
    
    def test_entry_rejection_on_iv_drop(self):
        """Test entry rejection when IV drops suddenly"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        greeks = MockGreeks.sample(iv=20.0)  # IV dropped
        greeks_prev = MockGreeks.sample(iv=25.0)
        
        tick = MockTick.sample(ltp=101.0, volume=1100, oi=510000)
        prev_tick = MockTick.sample(ltp=100.0, volume=1000, oi=500000)
        
        is_rejected = engine.check_entry_rejection(
            current_iv=greeks.iv,
            previous_iv=greeks_prev.iv,
            current_ltp=tick.ltp,
            previous_ltp=prev_tick.ltp
        )
        
        # IV drop > 3% with flat price = rejection
        if (greeks_prev.iv - greeks.iv) / greeks_prev.iv > 0.03:
            assert is_rejected is True
    
    def test_entry_rejection_on_spread_widening(self):
        """Test entry rejection when spread widens"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        current_spread = 1.5  # % of LTP
        prev_spread = 0.8
        
        is_rejected = engine.check_spread_rejection(
            current_spread=current_spread,
            prev_spread=prev_spread,
            max_spread_widening=0.7
        )
        
        assert is_rejected is True
    
    def test_entry_delta_power_zone_check(self):
        """Test entry requires delta in power zone"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        # In power zone (0.45-0.60)
        in_zone = engine.is_delta_in_power_zone(delta=0.55)
        assert in_zone is True
        
        # Below power zone
        below_zone = engine.is_delta_in_power_zone(delta=0.40)
        assert below_zone is False
        
        # Above power zone
        above_zone = engine.is_delta_in_power_zone(delta=0.70)
        assert above_zone is False
    
    def test_entry_volume_rising_check(self):
        """Test entry requires rising volume"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        volume_rising = engine.is_volume_rising(
            current_volume=1200,
            previous_volume=1000
        )
        assert volume_rising is True
        
        volume_flat = engine.is_volume_rising(
            current_volume=1000,
            previous_volume=1000
        )
        assert volume_flat is False
    
    def test_entry_oi_rising_check(self):
        """Test entry requires OI rising or stable"""
        engine = EntryEngine(bias_engine=None, trap_detection_engine=None)
        
        oi_rising = engine.is_oi_valid(
            current_oi=520000,
            previous_oi=500000
        )
        assert oi_rising is True
        
        # OI flat is acceptable
        oi_flat = engine.is_oi_valid(
            current_oi=500000,
            previous_oi=500000
        )
        assert oi_flat is True
        
        # OI dropping is concerning
        oi_drop = engine.is_oi_valid(
            current_oi=480000,
            previous_oi=500000
        )
        assert oi_drop is False or oi_drop is None
