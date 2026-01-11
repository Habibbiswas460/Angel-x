import pytest
from src.strategies.multi_leg.base import MultiLegStrategy, Leg
from src.strategies.multi_leg.iron_condor import IronCondor
from src.strategies.multi_leg.straddle import ShortStraddle, LongStraddle
from src.strategies.multi_leg.spreads import BullCallSpread, BearPutSpread


class TestMultiLegBase:
    
    def test_leg_creation(self):
        """Test Leg dataclass creation."""
        leg = Leg(
            instrument="NIFTY26JAN22450CE",
            strike=22450,
            kind="CALL",
            expiry="2026-01-22",
            qty=1,
            entry_price=100.5,
            side="BUY"
        )
        assert leg.strike == 22450
        assert leg.kind == "CALL"
        assert leg.qty == 1
    
    def test_base_strategy_interface(self):
        """Test MultiLegStrategy base interface."""
        class DummyStrategy(MultiLegStrategy):
            name = "dummy"
            def build_legs(self, spot):
                return []
        
        strategy = DummyStrategy()
        assert strategy.name == "dummy"
        legs = strategy.build_legs(spot=100)
        assert isinstance(legs, list)
        assert len(legs) == 0


class TestIronCondor:
    
    def test_iron_condor_leg_count(self):
        """Test that Iron Condor creates 4 legs."""
        ic = IronCondor(width=100)
        legs = ic.build_legs(spot=22450)
        assert len(legs) == 4
    
    def test_iron_condor_strike_spacing(self):
        """Test that Iron Condor strikes are properly spaced."""
        ic = IronCondor(width=100)
        legs = ic.build_legs(spot=22500)
        strikes = sorted([l.strike for l in legs])
        
        # Should have 4 distinct strikes
        assert len(set(strikes)) == 4
        
        # Check spacing
        for i in range(len(strikes) - 1):
            assert strikes[i + 1] - strikes[i] >= ic.width
    
    def test_iron_condor_option_types(self):
        """Test that Iron Condor has calls and puts."""
        ic = IronCondor(width=100)
        legs = ic.build_legs(spot=22450)
        
        calls = [l for l in legs if l.kind == "CALL"]
        puts = [l for l in legs if l.kind == "PUT"]
        
        assert len(calls) == 2  # Short call + long call
        assert len(puts) == 2   # Short put + long put


class TestStraddle:
    
    def test_short_straddle_structure(self):
        """Test Short Straddle has same-strike call and put."""
        st = ShortStraddle(spread=0)
        legs = st.build_legs(spot=22500)
        
        assert len(legs) == 2
        calls = [l for l in legs if l.kind == "CALL"]
        puts = [l for l in legs if l.kind == "PUT"]
        
        assert len(calls) == 1
        assert len(puts) == 1
        assert calls[0].strike == puts[0].strike
    
    def test_long_straddle_structure(self):
        """Test Long Straddle has same-strike call and put with BUY side."""
        st = LongStraddle(spread=0)
        legs = st.build_legs(spot=22500)
        
        assert len(legs) == 2
        for leg in legs:
            assert leg.side == "BUY"
    
    def test_straddle_symmetry(self):
        """Test Straddle has symmetric strikes."""
        st = ShortStraddle(spread=50)
        legs = st.build_legs(spot=22450)
        
        for leg in legs:
            assert leg.strike % 50 == 0  # Should be on 50-point intervals


class TestSpreads:
    
    def test_bull_call_spread(self):
        """Test Bull Call Spread has two call legs."""
        bcs = BullCallSpread(width=100)
        legs = bcs.build_legs(spot=22500)
        
        assert len(legs) == 2
        calls = [l for l in legs if l.kind == "CALL"]
        assert len(calls) == 2
        
        # One buy, one sell
        buys = [l for l in calls if l.side == "BUY"]
        sells = [l for l in calls if l.side == "SELL"]
        assert len(buys) == 1
        assert len(sells) == 1
    
    def test_bear_put_spread(self):
        """Test Bear Put Spread has two put legs."""
        bps = BearPutSpread(width=100)
        legs = bps.build_legs(spot=22500)
        
        assert len(legs) == 2
        puts = [l for l in legs if l.kind == "PUT"]
        assert len(puts) == 2
        
        # One sell, one buy
        buys = [l for l in puts if l.side == "BUY"]
        sells = [l for l in puts if l.side == "SELL"]
        assert len(buys) == 1
        assert len(sells) == 1
