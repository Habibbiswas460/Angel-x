"""
PHASE 5 — Comprehensive Test Suite (19+ Tests)

Tests all components:
1. Market Bias Constructor (3 tests)
2. Time Intelligence Gate (3 tests)
3. Theta & Volatility Guard (2 tests)
4. Trade Eligibility Engine (3 tests)
5. Direction & Strike Selector (2 tests)
6. Full Pipeline Integration (3 tests)
7. Edge Cases & Safety (3 tests)
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import unittest
from datetime import datetime, time
from src.utils.phase5_market_bias_models import (
    BiasType, BiasStrength, TimeWindow, DataHealthStatus,
    DirectionType, Phase5Config,
)
from src.utils.phase5_market_bias_constructor import MarketBiasConstructor
from src.utils.phase5_time_and_greeks_gate import (
    TimeIntelligenceGate, VolatilityAndThetaGuard, CombinedTimeAndGreeksGate
)
from src.utils.phase5_eligibility_and_selector import (
    TradeEligibilityEngine, DirectionAndStrikeSelector
)
from src.utils.phase5_market_bias_engine import MarketBiasAndEligibilityEngine


class TestMarketBiasConstructor(unittest.TestCase):
    """Test market bias detection"""
    
    def setUp(self):
        self.constructor = MarketBiasConstructor()
    
    def test_1_bullish_bias_detection(self):
        """Test BULLISH bias detection"""
        # Setup: Strong CE dominance
        bias = self.constructor.detect_bias(
            ce_dominance=0.65,         # CE dominant
            delta_ce=0.6,              # CE delta up
            delta_pe=-0.3,             # PE delta moderate
            gamma_ce=0.025,            # CE gamma higher
            gamma_pe=0.015,            # PE gamma lower
            oi_conviction=0.75,        # Strong OI
            volume_aggression=0.70,    # High volume
            primary_buildup="LONG_BUILD_UP",
        )
        
        # Verify
        self.assertEqual(bias.bias_type, BiasType.BULLISH)
        self.assertGreaterEqual(bias.bias_strength, BiasStrength.MEDIUM)
        self.assertGreaterEqual(bias.conviction_score, 0.5)
        print(f"✓ Bullish bias detected: {bias.reasoning}")
    
    def test_2_bearish_bias_detection(self):
        """Test BEARISH bias detection"""
        # Setup: Strong PE dominance
        bias = self.constructor.detect_bias(
            ce_dominance=0.35,         # PE dominant
            delta_ce=0.2,              # CE delta low
            delta_pe=-0.65,            # PE delta down
            gamma_ce=0.015,            # CE gamma lower
            gamma_pe=0.025,            # PE gamma higher
            oi_conviction=0.75,        # Strong OI
            volume_aggression=0.70,    # High volume
            primary_buildup="SHORT_BUILD_UP",
        )
        
        # Verify
        self.assertEqual(bias.bias_type, BiasType.BEARISH)
        self.assertGreaterEqual(bias.bias_strength, BiasStrength.MEDIUM)
        self.assertGreaterEqual(bias.conviction_score, 0.5)
        print(f"✓ Bearish bias detected: {bias.reasoning}")
    
    def test_3_neutral_bias_detection(self):
        """Test NEUTRAL bias detection (NO-TRADE)"""
        # Setup: Balanced, low conviction
        bias = self.constructor.detect_bias(
            ce_dominance=0.50,         # Balanced
            delta_ce=0.05,             # Very low delta
            delta_pe=-0.05,            # Very low delta
            gamma_ce=0.015,            # Normal gamma
            gamma_pe=0.015,            # Normal gamma
            oi_conviction=0.1,         # Very weak OI
            volume_aggression=0.1,     # Very low volume
            primary_buildup=None,
        )
        
        # Verify
        self.assertEqual(bias.bias_type, BiasType.NEUTRAL)
        self.assertEqual(bias.bias_strength, BiasStrength.LOW)
        self.assertLess(bias.conviction_score, 0.5)
        print(f"✓ Neutral bias detected (NO-TRADE): {bias.reasoning}")


class TestTimeIntelligenceGate(unittest.TestCase):
    """Test time window analysis"""
    
    def setUp(self):
        self.time_gate = TimeIntelligenceGate()
    
    def test_1_morning_window_allowed(self):
        """Test trading allowed in morning (9:20-11:15)"""
        window, allowed, reason = self.time_gate.analyze_time_window(time(10, 0))
        
        self.assertEqual(window, TimeWindow.ALLOWED)
        self.assertTrue(allowed)
        print(f"✓ Morning window: {reason}")
    
    def test_2_caution_window_filtered(self):
        """Test caution window (11:15-12:00)"""
        window, allowed, reason = self.time_gate.analyze_time_window(time(11, 30))
        
        self.assertEqual(window, TimeWindow.CAUTION)
        self.assertTrue(allowed)  # Still allowed but filtered
        strictness = self.time_gate.get_time_filter_strictness(window)
        self.assertGreater(strictness, 0.5)
        print(f"✓ Caution window: {reason}, strictness={strictness:.0%}")
    
    def test_3_theta_danger_blocked(self):
        """Test theta danger zone (post 12:00)"""
        window, allowed, reason = self.time_gate.analyze_time_window(time(14, 0))
        
        self.assertEqual(window, TimeWindow.THETA_DANGER)
        self.assertFalse(allowed)
        print(f"✓ Theta danger blocked: {reason}")


class TestThetaAndVolatilityGuard(unittest.TestCase):
    """Test Greeks safety checks"""
    
    def setUp(self):
        self.guard = VolatilityAndThetaGuard()
    
    def test_1_theta_spike_detection(self):
        """Test rapid theta worsening"""
        alert = self.guard.analyze_theta_velocity(
            theta_current=-0.8,         # Very negative (bad)
            theta_previous=-0.6,        # Previous was better
            gamma_current=0.02,
            iv_current=0.25,
            iv_previous=0.26,
        )
        
        self.assertTrue(alert.theta_spike_detected)
        self.assertFalse(alert.safe_to_trade)
        print(f"✓ Theta spike detected: {len(alert.warnings)} warnings")
    
    def test_2_gamma_exhaustion_detection(self):
        """Test gamma exhaustion"""
        alert = self.guard.analyze_theta_velocity(
            theta_current=-0.5,
            theta_previous=-0.5,
            gamma_current=0.001,        # Too low
            iv_current=0.25,
            iv_previous=0.25,
        )
        
        self.assertTrue(alert.gamma_exhausted)
        self.assertFalse(alert.safe_to_trade)
        print(f"✓ Gamma exhaustion detected: {len(alert.warnings)} warnings")


class TestTradeEligibilityEngine(unittest.TestCase):
    """Test eligibility gate"""
    
    def setUp(self):
        self.eligibility = TradeEligibilityEngine()
    
    def test_1_all_checks_pass(self):
        """Test all eligibility checks pass"""
        analysis = self.eligibility.check_eligibility(
            bias_type=BiasType.BULLISH,
            bias_strength=BiasStrength.HIGH,
            time_window=TimeWindow.ALLOWED,
            trap_probability=0.2,       # Low trap risk
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,       # Fresh data
            time_allowed=True,
            greeks_safe=True,
        )
        
        self.assertTrue(analysis.trade_eligible)
        self.assertTrue(analysis.bias_check.passed)
        self.assertTrue(analysis.strength_check.passed)
        self.assertTrue(analysis.time_check.passed)
        self.assertTrue(analysis.trap_check.passed)
        self.assertTrue(analysis.data_health_check.passed)
        print(f"✓ All eligibility checks passed: {analysis.eligibility_score:.0%}")
    
    def test_2_neutral_bias_blocks(self):
        """Test neutral bias blocks trade"""
        analysis = self.eligibility.check_eligibility(
            bias_type=BiasType.NEUTRAL,    # NO-TRADE
            bias_strength=BiasStrength.LOW,
            time_window=TimeWindow.ALLOWED,
            trap_probability=0.2,
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
            time_allowed=True,
            greeks_safe=True,
        )
        
        self.assertFalse(analysis.trade_eligible)
        self.assertFalse(analysis.bias_check.passed)
        print(f"✓ Neutral bias blocked: {analysis.block_reason}")
    
    def test_3_low_strength_blocks(self):
        """Test low bias strength blocks trade"""
        analysis = self.eligibility.check_eligibility(
            bias_type=BiasType.BULLISH,
            bias_strength=BiasStrength.LOW,   # Too weak
            time_window=TimeWindow.ALLOWED,
            trap_probability=0.2,
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
            time_allowed=True,
            greeks_safe=True,
        )
        
        self.assertFalse(analysis.trade_eligible)
        self.assertFalse(analysis.strength_check.passed)
        print(f"✓ Low strength blocked: {analysis.block_reason}")


class TestDirectionAndStrikeSelector(unittest.TestCase):
    """Test strike selection"""
    
    def setUp(self):
        self.selector = DirectionAndStrikeSelector()
    
    def test_1_bullish_call_selection(self):
        """Test BULLISH selects best CALL"""
        selection = self.selector.select_direction_and_strike(
            bias_type=BiasType.BULLISH,
            atm_strike=20000,
            # CE data
            ce_atm_gamma=0.02,
            ce_atm_fresh_oi=0.5,
            ce_atm_volume=500,
            ce_atm_plus1_gamma=0.018,
            ce_atm_plus1_fresh_oi=0.3,
            ce_atm_plus1_volume=300,
            # PE data (not used for bullish)
            pe_atm_gamma=0.01,
            pe_atm_fresh_oi=0.2,
            pe_atm_volume=200,
        )
        
        self.assertEqual(selection.direction, DirectionType.CALL)
        self.assertIn(selection.strike_offset, [0, 1])
        print(f"✓ Bullish CALL selected: {selection.reason.selection_reason}")
    
    def test_2_bearish_put_selection(self):
        """Test BEARISH selects best PUT"""
        selection = self.selector.select_direction_and_strike(
            bias_type=BiasType.BEARISH,
            atm_strike=20000,
            # CE data (not used for bearish)
            ce_atm_gamma=0.01,
            ce_atm_fresh_oi=0.2,
            ce_atm_volume=200,
            # PE data
            pe_atm_gamma=0.02,
            pe_atm_fresh_oi=0.5,
            pe_atm_volume=500,
            pe_atm_minus1_gamma=0.022,
            pe_atm_minus1_fresh_oi=0.6,
            pe_atm_minus1_volume=600,
        )
        
        self.assertEqual(selection.direction, DirectionType.PUT)
        self.assertIn(selection.strike_offset, [-1, 0])
        print(f"✓ Bearish PUT selected: {selection.reason.selection_reason}")


class TestFullPipelineIntegration(unittest.TestCase):
    """Test complete Phase 5 pipeline"""
    
    def setUp(self):
        self.engine = MarketBiasAndEligibilityEngine()
        self.engine.set_universe("NIFTY", 20000, 7.0)
    
    def test_1_bullish_setup_produces_signal(self):
        """Test bullish market produces valid signal"""
        signal = self.engine.generate_signal(
            # Bullish indicators
            ce_dominance=0.65,
            delta_ce=0.6,
            delta_pe=-0.3,
            gamma_ce=0.025,
            gamma_pe=0.015,
            theta_ce=-0.5,
            theta_pe=-0.4,
            theta_ce_prev=-0.45,
            theta_pe_prev=-0.35,
            iv_current=0.25,
            iv_previous=0.25,
            oi_conviction=0.75,
            volume_aggression=0.70,
            trap_probability=0.15,
            primary_buildup="LONG_BUILD_UP",
            # Strike data
            ce_atm_gamma=0.025,
            ce_atm_fresh_oi=0.5,
            ce_atm_volume=500,
            pe_atm_gamma=0.015,
            pe_atm_fresh_oi=0.3,
            pe_atm_volume=300,
            # Timing
            current_time=time(10, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
        )
        
        self.assertTrue(signal.trade_allowed)
        self.assertEqual(signal.direction, DirectionType.CALL)
        self.assertEqual(signal.market_bias, BiasType.BULLISH)
        print(f"✓ Bullish signal generated: {signal.reasoning_brief}")
    
    def test_2_theta_danger_blocks_signal(self):
        """Test theta danger zone blocks all trades"""
        signal = self.engine.generate_signal(
            # Even perfect setup blocked by time
            ce_dominance=0.65,
            delta_ce=0.6,
            delta_pe=-0.3,
            gamma_ce=0.025,
            gamma_pe=0.015,
            theta_ce=-0.5,
            theta_pe=-0.4,
            theta_ce_prev=-0.45,
            theta_pe_prev=-0.35,
            iv_current=0.25,
            iv_previous=0.25,
            oi_conviction=0.75,
            volume_aggression=0.70,
            trap_probability=0.15,
            primary_buildup="LONG_BUILD_UP",
            # Timing - POST 12:00 (theta danger)
            current_time=time(14, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
        )
        
        self.assertFalse(signal.trade_allowed)
        self.assertIn("THETA_DANGER", str(signal.block_reason))
        print(f"✓ Theta danger blocked: {signal.block_reason}")
    
    def test_3_neutral_market_no_trade(self):
        """Test neutral market doesn't generate signal"""
        signal = self.engine.generate_signal(
            # Neutral setup
            ce_dominance=0.50,
            delta_ce=0.1,
            delta_pe=-0.1,
            gamma_ce=0.015,
            gamma_pe=0.015,
            theta_ce=-0.4,
            theta_pe=-0.4,
            theta_ce_prev=-0.4,
            theta_pe_prev=-0.4,
            iv_current=0.25,
            iv_previous=0.25,
            oi_conviction=0.2,
            volume_aggression=0.2,
            trap_probability=0.5,
            primary_buildup=None,
            current_time=time(10, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
        )
        
        self.assertFalse(signal.trade_allowed)
        print(f"✓ Neutral market: no trade allowed")


class TestEdgeCasesAndSafety(unittest.TestCase):
    """Test safety guardrails"""
    
    def setUp(self):
        self.engine = MarketBiasAndEligibilityEngine()
        self.engine.set_universe("NIFTY", 20000, 7.0)
    
    def test_1_trap_probability_blocks(self):
        """Test high trap probability blocks"""
        signal = self.engine.generate_signal(
            # Good setup but HIGH trap risk
            ce_dominance=0.65,
            delta_ce=0.6,
            delta_pe=-0.3,
            gamma_ce=0.025,
            gamma_pe=0.015,
            theta_ce=-0.5,
            theta_pe=-0.4,
            theta_ce_prev=-0.45,
            theta_pe_prev=-0.35,
            iv_current=0.25,
            iv_previous=0.25,
            oi_conviction=0.75,
            volume_aggression=0.70,
            trap_probability=0.60,        # TOO HIGH
            primary_buildup="LONG_BUILD_UP",
            current_time=time(10, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
        )
        
        self.assertFalse(signal.trade_allowed)
        print(f"✓ High trap probability blocked")
    
    def test_2_stale_data_blocks(self):
        """Test stale data blocks trade"""
        signal = self.engine.generate_signal(
            # Good setup but STALE data
            ce_dominance=0.65,
            delta_ce=0.6,
            delta_pe=-0.3,
            gamma_ce=0.025,
            gamma_pe=0.015,
            theta_ce=-0.5,
            theta_pe=-0.4,
            theta_ce_prev=-0.45,
            theta_pe_prev=-0.35,
            iv_current=0.25,
            iv_previous=0.25,
            oi_conviction=0.75,
            volume_aggression=0.70,
            trap_probability=0.15,
            primary_buildup="LONG_BUILD_UP",
            current_time=time(10, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=30.0,       # TOO OLD
        )
        
        self.assertFalse(signal.trade_allowed)
        print(f"✓ Stale data blocked")
    
    def test_3_iv_crush_blocks(self):
        """Test IV crush detected and blocks"""
        signal = self.engine.generate_signal(
            # Good setup but IV CRUSHING
            ce_dominance=0.65,
            delta_ce=0.6,
            delta_pe=-0.3,
            gamma_ce=0.025,
            gamma_pe=0.015,
            theta_ce=-0.5,
            theta_pe=-0.4,
            theta_ce_prev=-0.45,
            theta_pe_prev=-0.35,
            iv_current=0.20,             # Dropped
            iv_previous=0.30,            # Was higher
            oi_conviction=0.75,
            volume_aggression=0.70,
            trap_probability=0.15,
            primary_buildup="LONG_BUILD_UP",
            current_time=time(10, 0),
            data_health=DataHealthStatus.GREEN,
            data_age_seconds=1.0,
        )
        
        self.assertFalse(signal.trade_allowed)
        print(f"✓ IV crush detected and blocked")


def run_tests():
    """Run all Phase 5 tests"""
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMarketBiasConstructor))
    suite.addTests(loader.loadTestsFromTestCase(TestTimeIntelligenceGate))
    suite.addTests(loader.loadTestsFromTestCase(TestThetaAndVolatilityGuard))
    suite.addTests(loader.loadTestsFromTestCase(TestTradeEligibilityEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestDirectionAndStrikeSelector))
    suite.addTests(loader.loadTestsFromTestCase(TestFullPipelineIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCasesAndSafety))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "="*80)
    print("PHASE 5 TEST SUMMARY")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print(f"\n✓ ALL {result.testsRun} TESTS PASSING ✓\n")
        print("🎊 PHASE 5 COMPLETE 🎊\n")
    else:
        print(f"\n✗ {len(result.failures) + len(result.errors)} TESTS FAILED\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    exit(0 if success else 1)
