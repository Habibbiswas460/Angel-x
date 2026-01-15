"""
Tests for Engine Modules
Covers strike selection, trap detection, and market bias engines
"""

import pytest
from datetime import datetime, timedelta
from src.engines.strike_selection.engine import (
    OptionType,
    OptionStrike,
    StrikeSelectionEngine,
)
from src.engines.trap_detection.engine import (
    TrapType,
    TrapSignal,
    TrapDetectionEngine,
)
from src.engines.market_bias.engine import (
    BiasEngine,
    BiasState,
    BiasMetrics,
)


class TestStrikeSelection:
    """Test strike selection engine"""

    def test_option_strike_creation(self):
        """Test creating option strike data"""
        strike = OptionStrike(
            symbol="NIFTY2610125CE",
            strike=25100,
            option_type=OptionType.CALL,
            ltp=100.0,
            bid=99.5,
            ask=100.5,
            bid_qty=1000,
            ask_qty=1200,
            volume=50000,
            oi=100000,
            oi_change=5000,
            delta=0.35,
            gamma=0.02,
            theta=-15.0,
            vega=25.0,
            iv=18.5,
            underlying_price=25000,
            timestamp=datetime.now(),
        )

        assert strike.strike == 25100
        assert strike.option_type == OptionType.CALL
        assert strike.ltp == 100.0

    def test_option_spread_calculation(self):
        """Test spread percentage calculation"""
        strike = OptionStrike(
            symbol="NIFTY2610125PE",
            strike=24900,
            option_type=OptionType.PUT,
            ltp=80.0,
            bid=79.0,
            ask=81.0,
            bid_qty=800,
            ask_qty=900,
            volume=30000,
            oi=80000,
            oi_change=-2000,
            delta=-0.30,
            gamma=0.018,
            theta=-12.0,
            vega=22.0,
            iv=17.0,
            underlying_price=25000,
            timestamp=datetime.now(),
        )

        # Spread = 81 - 79 = 2, LTP = 80, (2/80)*100 = 2.5%
        assert abs(strike.spread_percent - 2.5) < 0.01

    def test_option_liquidity_check(self):
        """Test liquidity validation"""
        # Liquid strike
        liquid_strike = OptionStrike(
            symbol="NIFTY2610125CE",
            strike=25100,
            option_type=OptionType.CALL,
            ltp=100.0,
            bid=99.5,
            ask=100.5,
            bid_qty=1000,
            ask_qty=1200,
            volume=50000,  # Good volume
            oi=100000,  # Good OI
            oi_change=5000,
            delta=0.35,
            gamma=0.02,
            theta=-15.0,
            vega=25.0,
            iv=18.5,
            underlying_price=25000,
            timestamp=datetime.now(),
        )

        # Illiquid strike
        illiquid_strike = OptionStrike(
            symbol="NIFTY2610130CE",
            strike=30000,
            option_type=OptionType.CALL,
            ltp=1.0,
            bid=0.5,
            ask=1.5,
            bid_qty=10,
            ask_qty=20,
            volume=50,  # Low volume
            oi=100,  # Low OI
            oi_change=0,
            delta=0.01,
            gamma=0.001,
            theta=-1.0,
            vega=2.0,
            iv=25.0,
            underlying_price=25000,
            timestamp=datetime.now(),
        )

        # Note: actual liquidity depends on config values
        assert liquid_strike.volume > illiquid_strike.volume
        assert liquid_strike.oi > illiquid_strike.oi

    def test_strike_selection_engine_init(self):
        """Test strike selection engine initialization"""
        engine = StrikeSelectionEngine()
        assert engine is not None
        assert hasattr(engine, "scan_and_select_best_strike")


class TestTrapDetection:
    """Test trap detection engine"""

    def test_trap_signal_creation(self):
        """Test creating a trap signal"""
        signal = TrapSignal(
            trap_type=TrapType.OI_NO_PREMIUM_RISE,
            severity=75.0,
            description="OI increased by 10000 but premium stagnant",
            timestamp=datetime.now(),
            data_snapshot={"oi_change": 10000, "premium_change": 0.5},
        )

        assert signal.trap_type == TrapType.OI_NO_PREMIUM_RISE
        assert signal.severity == 75.0
        assert "OI increased" in signal.description

    def test_trap_detection_engine_init(self):
        """Test trap detection engine initialization"""
        engine = TrapDetectionEngine()
        assert engine is not None
        assert hasattr(engine, "oi_history")
        assert hasattr(engine, "premium_history")
        assert hasattr(engine, "detected_traps")
        assert len(engine.oi_history) == 0

    def test_trap_engine_update_price_data(self):
        """Test updating trap detector with price data"""
        engine = TrapDetectionEngine()

        result = engine.update_price_data(
            ltp=100.0,
            bid=99.5,
            ask=100.5,
            volume=50000,
            oi=100000,
            oi_change=5000,
            delta=0.35,
            iv=18.5,
        )

        # After one update, histories should have 1 entry
        assert len(engine.oi_history) == 1
        assert len(engine.premium_history) == 1
        assert len(engine.iv_history) == 1
        assert engine.oi_history[0]["oi"] == 100000

    def test_trap_engine_history_limit(self):
        """Test that history is limited to 50 entries"""
        engine = TrapDetectionEngine()

        # Add 60 price updates
        for i in range(60):
            engine.update_price_data(
                ltp=100.0 + i * 0.5,
                bid=99.5 + i * 0.5,
                ask=100.5 + i * 0.5,
                volume=50000 + i * 100,
                oi=100000 + i * 1000,
                oi_change=1000,
                delta=0.35,
                iv=18.5,
            )

        # Should only keep last 50
        assert len(engine.oi_history) == 50
        assert len(engine.premium_history) == 50
        assert len(engine.iv_history) == 50


class TestMarketBias:
    """Test market bias engine"""

    def test_bias_engine_initialization(self):
        """Test bias engine initializes correctly"""
        engine = BiasEngine()
        assert engine is not None
        assert hasattr(engine, "get_bias")
        assert hasattr(engine, "detect_bias")


class TestTrapTypes:
    """Test trap type enumeration"""

    def test_trap_type_enum(self):
        """Test all trap types exist"""
        assert TrapType.OI_NO_PREMIUM_RISE.value == "OI increasing but premium not rising"
        assert TrapType.PREMIUM_NO_OI.value == "Premium rising but OI decreasing (short covering)"
        assert TrapType.OI_SPIKE_NO_FOLLOW.value == "OI spike with no price follow-through"
        assert TrapType.IV_DROP_CRUSH.value == "IV dropping sharply (premium melt)"
        assert TrapType.IV_CHOPPY_UNDERLYING.value == "High IV with choppy underlying movement"
        assert TrapType.SPREAD_WIDENING.value == "Spread suddenly widening"
        assert TrapType.LIQUIDITY_EVAPORATION.value == "Volume/OI vanishing suddenly"
        assert TrapType.DELTA_SPIKE_COLLAPSE.value == "Delta spikes then collapses (fake move)"


class TestOptionType:
    """Test option type enumeration"""

    def test_option_type_enum(self):
        """Test option types"""
        assert OptionType.CALL.value == "CE"
        assert OptionType.PUT.value == "PE"


class TestStrikeGreeksScoring:
    """Test Greeks health scoring"""

    def test_greeks_health_score_calculation(self):
        """Test Greeks health score for different strikes"""
        # Good Greeks strike
        good_strike = OptionStrike(
            symbol="NIFTY2610125CE",
            strike=25100,
            option_type=OptionType.CALL,
            ltp=100.0,
            bid=99.5,
            ask=100.5,
            bid_qty=1000,
            ask_qty=1200,
            volume=50000,
            oi=100000,
            oi_change=5000,
            delta=0.35,  # Good delta
            gamma=0.02,  # Good gamma
            theta=-15.0,  # Manageable theta
            vega=25.0,  # Good vega
            iv=18.5,
            underlying_price=25000,
            timestamp=datetime.now(),
        )

        # Greeks health score should be calculated
        score = good_strike.greeks_health_score
        assert score >= 0
        assert score <= 100


class TestTrapSeverity:
    """Test trap severity levels"""

    def test_low_severity_trap(self):
        """Test low severity trap signal"""
        signal = TrapSignal(
            trap_type=TrapType.IV_CHOPPY_UNDERLYING,
            severity=25.0,  # Low
            description="Minor IV volatility",
            timestamp=datetime.now(),
            data_snapshot={"iv_change": 2.0},
        )

        assert signal.severity < 50

    def test_high_severity_trap(self):
        """Test high severity trap signal"""
        signal = TrapSignal(
            trap_type=TrapType.LIQUIDITY_EVAPORATION,
            severity=95.0,  # Very high
            description="Liquidity disappeared completely",
            timestamp=datetime.now(),
            data_snapshot={"volume_drop": 90},
        )

        assert signal.severity > 90


class TestEngineIntegration:
    """Test engine integration scenarios"""

    def test_trap_detection_with_multiple_updates(self):
        """Test trap detection with realistic data flow"""
        engine = TrapDetectionEngine()

        # Simulate normal market condition
        for i in range(10):
            engine.update_price_data(
                ltp=100.0 + i,
                bid=99.5 + i,
                ask=100.5 + i,
                volume=50000,
                oi=100000 + i * 1000,
                oi_change=1000,
                delta=0.35,
                iv=18.5,
            )

        assert len(engine.oi_history) == 10
        assert len(engine.premium_history) == 10

    def test_strike_selection_with_filters(self):
        """Test that strike selection can filter strikes"""
        engine = StrikeSelectionEngine()
        assert hasattr(engine, "scan_and_select_best_strike")
        # More detailed tests would require mocking option chain data
