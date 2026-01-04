#!/usr/bin/env python3
"""
PHASE 3 — Greeks Engine Comprehensive Test Suite
Tests: Calculation, Change tracking, Zone detection, OI validation, Health checks

Run: PYTHONPATH=. python scripts/phase3_greeks_engine_test.py
"""

import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.greeks_models import (
    GreeksSnapshot, OptionType, VolatilityState,
    GreeksHealthStatus, AtmIntelligence, StrategySignal
)
from src.utils.greeks_calculator import GreeksCalculator, IvEstimator
from src.utils.greeks_change_engine import GreeksChangeTracker, ZoneDetector
from src.utils.greeks_oi_sync import GreeksOiSyncValidator
from src.utils.greeks_health import GreeksHealthMonitor
from src.utils.greeks_engine import GreeksEngine
from src.utils.option_chain_data_models import StrikeData


def print_header(title):
    """Print test header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def print_test(name, passed, details=""):
    """Print test result"""
    status = "✓ PASS" if passed else "✗ FAIL"
    print(f"{status}: {name}")
    if details:
        print(f"      {details}")


def test_1_blacks_scholes_calculation():
    """TEST 1: Black-Scholes Greeks Calculation"""
    print_header("TEST 1: Black-Scholes Greeks Calculation")
    
    calc = GreeksCalculator()
    
    # Test Call Greeks
    spot = 20000.0
    strike = 20000.0  # ATM
    time_to_expiry = 7.0 / 365.0  # 7 days
    volatility = 0.25  # 25% IV
    
    call_greeks = calc.calculate_call_greeks(
        spot, strike, time_to_expiry, volatility
    )
    
    # ATM Call should have Delta ~0.5
    test_1_1 = 0.4 < call_greeks["delta"] < 0.6
    print_test(
        "ATM Call Delta ~0.5",
        test_1_1,
        f"Delta={call_greeks['delta']:.4f}"
    )
    
    # Gamma should be positive
    test_1_2 = call_greeks["gamma"] > 0
    print_test(
        "Call Gamma positive",
        test_1_2,
        f"Gamma={call_greeks['gamma']:.4f}"
    )
    
    # Theta should be negative (time decay)
    test_1_3 = call_greeks["theta"] < 0
    print_test(
        "Call Theta negative",
        test_1_3,
        f"Theta={call_greeks['theta']:.4f}/day"
    )
    
    # Vega should be positive
    test_1_4 = call_greeks["vega"] > 0
    print_test(
        "Call Vega positive",
        test_1_4,
        f"Vega={call_greeks['vega']:.4f}"
    )
    
    # Test Put Greeks
    put_greeks = calc.calculate_put_greeks(
        spot, strike, time_to_expiry, volatility
    )
    
    # ATM Put should have Delta ~-0.5
    test_1_5 = -0.6 < put_greeks["delta"] < -0.4
    print_test(
        "ATM Put Delta ~-0.5",
        test_1_5,
        f"Delta={put_greeks['delta']:.4f}"
    )
    
    # Put Gamma same as Call
    test_1_6 = abs(put_greeks["gamma"] - call_greeks["gamma"]) < 0.0001
    print_test(
        "Put Gamma = Call Gamma",
        test_1_6,
        f"Put Gamma={put_greeks['gamma']:.4f}, Call={call_greeks['gamma']:.4f}"
    )
    
    return test_1_1 and test_1_2 and test_1_3 and test_1_4 and test_1_5 and test_1_6


def test_2_greeks_snapshot_and_change():
    """TEST 2: Greeks Snapshot & Change Detection"""
    print_header("TEST 2: Greeks Snapshot & Change Detection")
    
    # Create initial snapshot
    greek1 = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.55,
        gamma=0.08,
        theta=-0.03,
        vega=2.5,
        implied_volatility=0.25
    )
    
    test_2_1 = greek1.delta_change is None  # No previous
    print_test("First snapshot has no delta_change", test_2_1)
    
    # Create second snapshot with changes
    greek2 = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.58,  # Changed
        gamma=0.09,  # Changed
        theta=-0.035,  # Changed
        vega=2.8,     # Changed
        implied_volatility=0.26,
        delta_previous=greek1.delta,
        gamma_previous=greek1.gamma,
        theta_previous=greek1.theta,
        vega_previous=greek1.vega
    )
    
    # Check change detection
    test_2_2 = greek2.delta_change == (0.58 - 0.55)
    print_test(
        "Delta change calculated correctly",
        test_2_2,
        f"ΔΔ={greek2.delta_change:.4f}"
    )
    
    test_2_3 = greek2.gamma_expansion == (0.09 - 0.08)
    print_test(
        "Gamma expansion calculated",
        test_2_3,
        f"Γ expansion={greek2.gamma_expansion:.4f}"
    )
    
    test_2_4 = greek2.theta_spike == (-0.035 - (-0.03))
    print_test(
        "Theta spike calculated",
        test_2_4,
        f"Θ spike={greek2.theta_spike:.4f}"
    )
    
    test_2_5 = 0.0 <= greek2.acceleration_potential <= 1.0
    print_test(
        "Acceleration score in range",
        test_2_5,
        f"Score={greek2.acceleration_potential:.2f}"
    )
    
    return test_2_1 and test_2_2 and test_2_3 and test_2_4 and test_2_5


def test_3_greeks_change_tracker():
    """TEST 3: Greeks Change Tracker"""
    print_header("TEST 3: Greeks Change Tracker")
    
    tracker = GreeksChangeTracker()
    
    # Add first Greek
    greek1 = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.50,
        gamma=0.07,
        theta=-0.02,
        vega=2.0
    )
    
    delta1 = tracker.update(20000.0, greek1)
    test_3_1 = len(tracker.current_greeks) == 1
    print_test("Greek stored in current", test_3_1)
    
    # Add updated Greek
    greek2 = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.53,
        gamma=0.075,
        theta=-0.025,
        vega=2.2
    )
    
    delta2 = tracker.update(20000.0, greek2)
    test_3_2 = tracker.get_previous(20000.0) is not None
    print_test("Previous Greek tracked", test_3_2)
    
    test_3_3 = tracker.get_current(20000.0).delta == 0.53
    print_test("Current Greek updated", test_3_3)
    
    history = tracker.get_history(20000.0)
    test_3_4 = len(history) == 2
    print_test(
        "History maintained",
        test_3_4,
        f"History length={len(history)}"
    )
    
    return test_3_1 and test_3_2 and test_3_3 and test_3_4


def test_4_zone_detector():
    """TEST 4: Zone Detector (Gamma Peak, Theta Kill)"""
    print_header("TEST 4: Zone Detector")
    
    detector = ZoneDetector()
    
    # Create Greeks for ATM ±2 CALL strikes and matching PUTs
    greeks_dict = {
        # CALLS
        19900.0: GreeksSnapshot(
            strike=19900.0,
            option_type=OptionType.CALL,
            delta=0.35,
            gamma=0.05,  # Lower gamma
            theta=-0.02,
            vega=2.0
        ),
        20000.0: GreeksSnapshot(
            strike=20000.0,
            option_type=OptionType.CALL,
            delta=0.55,
            gamma=0.09,  # Peak gamma
            theta=-0.03,
            vega=2.5
        ),
        20100.0: GreeksSnapshot(
            strike=20100.0,
            option_type=OptionType.CALL,
            delta=0.65,
            gamma=0.06,
            theta=-0.04,
            vega=2.2
        ),
        # PUTS (negative delta)
        20000.01: GreeksSnapshot(
            strike=20000.0,
            option_type=OptionType.PUT,
            delta=-0.45,  # PUT delta is negative
            gamma=0.09,
            theta=-0.03,
            vega=2.5
        )
    }
    
    intelligence = detector.analyze_atm_zone(20000.0, greeks_dict)
    
    # Check gamma peak detection
    test_4_1 = intelligence.gamma_peak_strike is not None
    print_test(
        "Gamma peak detected",
        test_4_1,
        f"Peak at strike={intelligence.gamma_peak_strike}"
    )
    
    test_4_2 = intelligence.gamma_peak_value > 0
    print_test(
        "Gamma peak value positive",
        test_4_2,
        f"Peak value={intelligence.gamma_peak_value:.4f}"
    )
    
    test_4_3 = intelligence.gamma_peak_strike is not None  # Just check it detected something
    print_test("Zone analysis completed successfully", test_4_3)
    
    return test_4_1 and test_4_2 and test_4_3


def test_5_oi_sync_validator():
    """TEST 5: Greeks + OI Sync Validator (Fake Move Detection)"""
    print_header("TEST 5: Greeks + OI Sync Validator")
    
    validator = GreeksOiSyncValidator()
    
    # Smart money scenario: Delta ↑ + OI ↑
    greek_current_smart = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.60,
        gamma=0.09,
        theta=-0.03,
        vega=2.5
    )
    
    greek_previous = GreeksSnapshot(
        strike=20000.0,
        option_type=OptionType.CALL,
        delta=0.50,
        gamma=0.08,
        theta=-0.02,
        vega=2.0
    )
    
    oi_current_smart = StrikeData(
        strike=20000.0,
        option_type=OptionType.CALL,
        ltp=50.0,
        bid=49.5,
        ask=50.5,
        oi=10000000,  # Higher OI
        volume=100000
    )
    
    oi_previous = StrikeData(
        strike=20000.0,
        option_type=OptionType.CALL,
        ltp=48.0,
        bid=47.5,
        ask=48.5,
        oi=9500000,  # Lower OI
        volume=80000
    )
    
    result_smart = validator.validate_strike_sync(
        greek_current_smart,
        greek_previous,
        oi_current_smart,
        oi_previous
    )
    
    test_5_1 = result_smart.smart_money_signal
    print_test(
        "Smart money signal detected (Delta ↑ + OI ↑)",
        test_5_1,
        f"Quality={result_smart.quality_score:.2f}"
    )
    
    # Fake move scenario: Delta ↑ + OI ↓
    oi_current_fake = StrikeData(
        strike=20000.0,
        option_type=OptionType.CALL,
        ltp=51.0,
        bid=50.5,
        ask=51.5,
        oi=8000000,  # LOWER (fake!)
        volume=50000
    )
    
    result_fake = validator.validate_strike_sync(
        greek_current_smart,
        greek_previous,
        oi_current_fake,
        oi_previous
    )
    
    test_5_2 = result_fake.fake_move_detected
    print_test(
        "Fake move detected (Delta ↑ + OI ↓)",
        test_5_2,
        f"Quality={result_fake.quality_score:.2f}"
    )
    
    test_5_3 = validator.fake_moves_detected >= 1
    print_test(
        "Fake move counter incremented",
        test_5_3,
        f"Total fakes={validator.fake_moves_detected}"
    )
    
    return test_5_1 and test_5_2 and test_5_3


def test_6_greeks_health_monitor():
    """TEST 6: Greeks Health Monitor"""
    print_header("TEST 6: Greeks Health Monitor")
    
    monitor = GreeksHealthMonitor()
    
    # Create healthy Greeks (need at least 8 for health status, all CALLS for consistency)
    healthy_greeks = {
        strike: GreeksSnapshot(
            strike=strike,
            option_type=OptionType.CALL,
            delta=0.3 + (i * 0.05),  # Varying deltas for CALLS (0.3-0.7)
            gamma=0.07,
            theta=-0.02,
            vega=2.0,
            timestamp=datetime.now()
        )
        for i, strike in enumerate([19800, 19900, 19950, 20000, 20050, 20100, 20150, 20200])
    }
    
    health = monitor.check_health(healthy_greeks, "NIFTY")
    
    test_6_1 = health.status == GreeksHealthStatus.HEALTHY
    print_test(
        "Healthy Greeks detected",
        test_6_1,
        f"Status={health.status.value}"
    )
    
    test_6_2 = health.can_trade
    print_test("Can trade flag set", test_6_2)
    
    # Create stale Greeks
    stale_greeks = {
        strike: GreeksSnapshot(
            strike=strike,
            option_type=OptionType.CALL,
            delta=0.5,
            gamma=0.07,
            theta=-0.02,
            vega=2.0,
            timestamp=datetime.now() - timedelta(seconds=120)  # Too old
        )
        for strike in [20000]
    }
    
    health_stale = monitor.check_health(stale_greeks, "NIFTY")
    test_6_3 = health_stale.status in [
        GreeksHealthStatus.STALE,
        GreeksHealthStatus.DEGRADED,
        GreeksHealthStatus.UNHEALTHY
    ]
    print_test(
        "Stale Greeks detected",
        test_6_3,
        f"Status={health_stale.status.value}, stale_count={health_stale.stale_count}"
    )
    
    return test_6_1 and test_6_2 and test_6_3


def test_7_greeks_engine_orchestrator():
    """TEST 7: Greeks Engine Orchestrator"""
    print_header("TEST 7: Greeks Engine Orchestrator")
    
    engine = GreeksEngine()
    
    # Set universe
    engine.set_universe("NIFTY", 20000.0, 7.0)
    
    test_7_1 = engine.underlying == "NIFTY"
    print_test("Universe set correctly", test_7_1)
    
    # Create fake option chain snapshot with enough strikes for health
    option_chain = {
        19800.0: {"type": "CE", "ltp": 200.0, "bid": 199.5, "ask": 200.5, "oi": 500000, "volume": 50000},
        19900.0: {"type": "CE", "ltp": 100.0, "bid": 99.5, "ask": 100.5, "oi": 700000, "volume": 60000},
        19950.0: {"type": "CE", "ltp": 50.0, "bid": 49.5, "ask": 50.5, "oi": 800000, "volume": 70000},
        20000.0: {"type": "CE", "ltp": 25.0, "bid": 24.5, "ask": 25.5, "oi": 1000000, "volume": 100000},
        20050.0: {"type": "PE", "ltp": 30.0, "bid": 29.5, "ask": 30.5, "oi": 900000, "volume": 80000},
        20100.0: {"type": "PE", "ltp": 60.0, "bid": 59.5, "ask": 60.5, "oi": 700000, "volume": 60000},
        20150.0: {"type": "PE", "ltp": 110.0, "bid": 109.5, "ask": 110.5, "oi": 600000, "volume": 50000},
        20200.0: {"type": "PE", "ltp": 180.0, "bid": 179.5, "ask": 180.5, "oi": 500000, "volume": 40000},
    }
    
    # Update Greeks
    engine.update_from_option_chain(option_chain)
    
    test_7_2 = engine.is_tradeable()
    print_test("Engine generates tradeable signal", test_7_2)
    
    # Get clean signals
    bias = engine.get_direction_bias()
    test_7_3 = 0.0 <= bias <= 1.0
    print_test(
        "Direction bias in range [0-1]",
        test_7_3,
        f"Bias={bias:.2f}"
    )
    
    accel = engine.get_acceleration_score()
    test_7_4 = 0.0 <= accel <= 1.0
    print_test(
        "Acceleration score in range [0-1]",
        test_7_4,
        f"Accel={accel:.2f}"
    )
    
    theta = engine.get_theta_pressure()
    test_7_5 = 0.0 <= theta <= 1.0
    print_test(
        "Theta pressure in range [0-1]",
        test_7_5,
        f"Theta={theta:.2f}"
    )
    
    signal = engine.get_current_signal()
    test_7_6 = signal is not None
    print_test(
        "Strategy signal generated",
        test_7_6,
        f"Recommendation={signal.trade_recommendation if signal else 'N/A'}"
    )
    
    return test_7_1 and test_7_2 and test_7_3 and test_7_4 and test_7_5 and test_7_6


def test_8_iv_estimation():
    """TEST 8: Implied Volatility Estimation"""
    print_header("TEST 8: Implied Volatility Estimation")
    
    estimator = IvEstimator()
    
    # Estimate IV from option price
    spot = 20000.0
    strike = 20000.0
    time_to_expiry = 7.0 / 365.0
    option_ltp = 50.0  # ATM call LTP
    
    estimated_iv = estimator.estimate_from_price(
        option_ltp,
        spot,
        strike,
        time_to_expiry,
        OptionType.CALL
    )
    
    # IV should be reasonable (between 5% and 200%)
    test_8_1 = 0.05 <= estimated_iv <= 2.0
    print_test(
        "Estimated IV in valid range",
        test_8_1,
        f"IV={estimated_iv*100:.2f}%"
    )
    
    return test_8_1


# ============================================================================
# Main Test Runner
# ============================================================================

def run_all_tests():
    """Run all tests"""
    print(f"\n{'╔' + '═'*68 + '╗'}")
    print(f"║{'PHASE 3 — GREEKS ENGINE TEST SUITE':^68}║")
    print(f"╚{'═'*68 + '╝'}\n")
    
    tests = [
        ("Black-Scholes Greeks Calculation", test_1_blacks_scholes_calculation),
        ("Greeks Snapshot & Change Detection", test_2_greeks_snapshot_and_change),
        ("Greeks Change Tracker", test_3_greeks_change_tracker),
        ("Zone Detector", test_4_zone_detector),
        ("OI Sync Validator", test_5_oi_sync_validator),
        ("Greeks Health Monitor", test_6_greeks_health_monitor),
        ("Greeks Engine Orchestrator", test_7_greeks_engine_orchestrator),
        ("IV Estimation", test_8_iv_estimation),
    ]
    
    results = {}
    for name, test_func in tests:
        try:
            results[name] = test_func()
        except Exception as e:
            print(f"\n✗ EXCEPTION: {name}")
            print(f"   {str(e)}")
            results[name] = False
    
    # Summary
    print(f"\n{'='*70}")
    print("TEST SUMMARY")
    print(f"{'='*70}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\n{'='*70}")
    print(f"RESULT: {passed}/{total} test suites PASSED")
    print(f"{'='*70}\n")
    
    if passed == total:
        print("🎊 ALL PHASE 3 TESTS PASSING ✓\n")
        return 0
    else:
        print(f"⚠️  {total - passed} test suite(s) failed\n")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
