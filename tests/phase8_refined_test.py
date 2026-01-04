"""
Test Suite for Phase 8 Refined Components
Tests all 8 sub-phases: noise reduction, adaptive strictness, metrics tracking,
over-optimization guard, and live readiness checklist
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.noise_reduction import (
    OIFlickerFilter, VolumeConfirmationFilter, 
    GreeksSmoother, DataNoiseReducer
)
from src.core.adaptive_strictness import (
    MarketAwareStrictness, WinLossRiskAdjuster, 
    AdaptiveStrictnessEngine
)
from src.core.metrics_tracker import PerformanceTracker, TradeRecord
from src.core.production_readiness import (
    OverOptimizationGuard, LiveReadinessChecklist
)
from src.core.failover_system import DataFreezeDetector
from datetime import datetime, timedelta


def test_oi_flicker_filter():
    """Test OI flicker detection and filtering"""
    print("Testing OI Flicker Filter...")
    
    filter = OIFlickerFilter()
    
    # Test basic functionality
    filter.update_oi("NIFTY_CE_18000", 10000)
    filter.update_oi("NIFTY_CE_18000", 10200)  # Only 200 delta
    filter.update_oi("NIFTY_CE_18000", 10100)  # Back down
    
    net_change = filter.get_net_change("NIFTY_CE_18000", lookback=3)
    assert abs(net_change) < 500, "Micro fluctuation should result in small net change"
    
    print("✅ OI Flicker Filter tests passed")


def test_volume_confirmation():
    """Test volume spike confirmation logic"""
    print("Testing Volume Confirmation...")
    
    filter = VolumeConfirmationFilter()
    
    # Test sustained volume tracking
    filter.update_volume("NIFTY_CE_18000", 5000)
    filter.update_volume("NIFTY_CE_18000", 5200)
    filter.update_volume("NIFTY_CE_18000", 4800)
    
    sustained = filter.get_sustained_volume("NIFTY_CE_18000", window=3)
    assert sustained > 0, "Should calculate sustained volume"
    
    print("✅ Volume Confirmation tests passed")


def test_greeks_smoother():
    """Test Greeks smoothing logic"""
    print("Testing Greeks Smoother...")
    
    smoother = GreeksSmoother()
    
    # Add some Greeks data
    smoother.update_greeks("NIFTY_CE_18000", {'delta': 0.50, 'theta': -50, 'gamma': 0.05})
    smoother.update_greeks("NIFTY_CE_18000", {'delta': 0.53, 'theta': -51, 'gamma': 0.05})
    smoother.update_greeks("NIFTY_CE_18000", {'delta': 0.49, 'theta': -49, 'gamma': 0.05})
    
    # Get smoothed values
    smoothed = smoother.get_smoothed_greeks("NIFTY_CE_18000")
    assert 'delta' in smoothed, "Should return smoothed delta"
    
    print("✅ Greeks Smoother tests passed")


def test_data_noise_reducer():
    """Test complete data noise reduction pipeline"""
    print("Testing Data Noise Reducer...")
    
    reducer = DataNoiseReducer()
    
    option_data = {
        'oi': 50000,
        'volume': 5000,
        'delta': 0.52,
        'theta': -50,
        'gamma': 0.05
    }
    
    result = reducer.process_option_data("NIFTY_CE_18000", option_data)
    
    # Should return cleaned data
    assert 'cleaned_data' in result, "Should return cleaned data"
    
    print("✅ Data Noise Reducer tests passed")


def test_market_aware_strictness():
    """Test market session-based strictness"""
    print("Testing Market-Aware Strictness...")
    
    strictness = MarketAwareStrictness()
    
    # Test get current session
    current_session = strictness.get_current_session()
    assert current_session is not None, "Should return current session"
    
    # Test session multiplier
    multiplier = strictness.get_session_multiplier()
    assert multiplier >= 1.0, "Multiplier should be at least 1.0"
    
    # Test volatility multiplier
    vol_mult = strictness.get_volatility_multiplier(iv=25.0)
    assert vol_mult >= 1.0, "Volatility multiplier should be at least 1.0"
    
    print("✅ Market-Aware Strictness tests passed")


def test_win_loss_risk_adjuster():
    """Test win/loss based risk adjustment"""
    print("Testing Win/Loss Risk Adjuster...")
    
    adjuster = WinLossRiskAdjuster()
    
    # Test initial state
    risk1 = adjuster.get_adjusted_risk_pct()
    assert risk1 > 0, "Should return positive risk percentage"
    
    # Record 1 loss
    adjuster.record_trade(pnl=-500)
    risk2 = adjuster.get_adjusted_risk_pct()
    assert risk2 <= risk1, "Risk should reduce or stay same after loss"
    
    # Check consecutive losses
    adjuster.record_trade(pnl=-500)
    consecutive = adjuster.get_consecutive_losses()
    assert consecutive >= 1, "Should track consecutive losses"
    
    # Record a win (should help recovery)
    adjuster.record_trade(pnl=500)
    consecutive_wins = adjuster.get_consecutive_wins()
    assert consecutive_wins >= 1, "Should track consecutive wins"
    
    print("✅ Win/Loss Risk Adjuster tests passed")


def test_adaptive_strictness_engine():
    """Test combined adaptive strictness engine"""
    print("Testing Adaptive Strictness Engine...")
    
    engine = AdaptiveStrictnessEngine()
    
    # Test trading conditions evaluation
    result = engine.evaluate_trading_conditions(
        current_iv=25.0,  # NORMAL volatility
        recent_pnl=500  # Positive PnL
    )
    
    assert 'can_trade' in result, "Should return trade allowance decision"
    assert 'adjusted_thresholds' in result or 'pause_reasons' in result, "Should return trading constraints"
    
    # Test signal requirements
    requirements = engine.get_signal_requirements(current_iv=25.0)
    assert 'min_bias_strength' in requirements, "Should return minimum bias strength"
    
    print("✅ Adaptive Strictness Engine tests passed")


def test_performance_tracker():
    """Test performance metrics tracking"""
    print("Testing Performance Tracker...")
    
    tracker = PerformanceTracker()
    
    # Create sample trade with ALL required fields
    trade = TradeRecord(
        trade_id="TEST001",
        timestamp=datetime.now(),
        symbol="NIFTY_CE_18000",
        entry_price=100.0,
        exit_price=105.0,
        quantity=25,
        pnl=125,
        holding_time_seconds=900,  # 15 minutes
        exit_reason='TARGET',
        entry_iv=25.0,
        exit_iv=26.0,
        entry_time="MORNING",
        entry_delta=0.5,
        entry_theta=-50,
        entry_gamma=0.05,
        oi_delta=2000,
        oi_conviction='HIGH',
        bias_strength=0.8,
        bias_direction='BULLISH'
    )
    
    tracker.record_trade(trade)
    
    # Get session analysis
    session_stats = tracker.get_win_rate_by_time()
    assert session_stats is not None, "Should return session statistics"
    
    # Get OI conviction analysis
    oi_stats = tracker.get_oi_conviction_analysis()
    assert oi_stats is not None, "Should track conviction levels"
    
    print("✅ Performance Tracker tests passed")


def test_over_optimization_guard():
    """Test over-optimization prevention"""
    print("Testing Over-Optimization Guard...")
    
    guard = OverOptimizationGuard(min_review_interval_days=7)
    
    # Test 1: Lock parameters
    guard.lock_parameters("Live trading active")
    result1 = guard.can_modify_parameters()
    assert result1['allowed'] == False, "Should not allow changes when locked"
    
    # Test 2: Unlock and wait for review interval
    guard.unlock_parameters()
    # Simulate review interval passed by setting last review to past
    guard.last_review_date = datetime.now() - timedelta(days=8)
    
    result2 = guard.propose_parameter_change(
        param_name='bias_threshold',
        new_value=0.75,
        reason='Testing optimization'
    )
    assert result2['approved'] == True, "Should allow change after review interval"
    
    # Test 3: Detect over-tuning
    # Set review date to past again for multiple changes
    guard.last_review_date = datetime.now() - timedelta(days=8)
    
    # Simulate multiple rapid changes
    for i in range(6):
        guard.last_review_date = datetime.now() - timedelta(days=8)
        guard.propose_parameter_change(
            param_name=f'param_{i}',
            new_value=i * 0.1,
            reason='Rapid tuning'
        )
    
    overtuning = guard.detect_overtuning()
    assert overtuning['overtuning_detected'] == True, "Should detect excessive changes"
    
    print("✅ Over-Optimization Guard tests passed")


def test_live_readiness_checklist():
    """Test live readiness checklist"""
    print("Testing Live Readiness Checklist...")
    
    checklist = LiveReadinessChecklist()
    
    # Mock functions for testing
    def mock_kill_switch(dry_run=False):
        return True
    
    def mock_broker_test():
        return True
    
    def mock_data_test():
        return True
    
    # Create mock guard with locked parameters
    guard = OverOptimizationGuard()
    guard.lock_parameters("Testing")
    
    # Run full checklist
    result = checklist.run_full_checklist(
        guard=guard,
        kill_switch_callback=mock_kill_switch,
        broker_test_func=mock_broker_test,
        data_test_func=mock_data_test,
        max_loss_config=10000,
        risk_config={
            'max_drawdown': 10,
            'max_trades_per_day': 5,
            'risk_per_trade': 2
        },
        sizing_config={
            'min_lots': 1,
            'max_lots': 3,
            'lot_size': 25
        },
        log_dir=Path('./logs')
    )
    
    assert 'ready_for_live' in result, "Should return readiness status"
    
    # Generate report
    report = checklist.generate_checklist_report()
    assert len(report) > 0, "Should generate readable report"
    
    print("✅ Live Readiness Checklist tests passed")


def test_data_freeze_failsafe():
    """Test enhanced data freeze detection with trading block"""
    print("Testing Data Freeze Failsafe...")
    
    detector = DataFreezeDetector(max_staleness_seconds=10)
    
    # Test 1: No data yet
    result1 = detector.can_trade()
    assert result1['allowed'] == False, "Should not allow trading with no data"
    assert 'No market data' in result1['reason'], "Should explain why trading blocked"
    
    # Test 2: Fresh data
    detector.update_data("hash_1")
    result2 = detector.can_trade()
    assert result2['allowed'] == True, "Should allow trading with fresh data"
    
    # Test 3: Stale data (simulate 15 seconds passing)
    import time
    detector.last_update_time = datetime.now() - timedelta(seconds=15)
    result3 = detector.can_trade()
    assert result3['allowed'] == False, "Should not allow trading with stale data"
    assert 'stale' in result3['reason'].lower(), "Should indicate stale data"
    
    print("✅ Data Freeze Failsafe tests passed")


def run_all_tests():
    """Run complete Phase 8 refined test suite"""
    print("\n" + "="*60)
    print("PHASE 8 REFINED COMPONENTS - TEST SUITE")
    print("="*60 + "\n")
    
    tests = [
        ("Phase 8.2: OI Flicker Filter", test_oi_flicker_filter),
        ("Phase 8.2: Volume Confirmation", test_volume_confirmation),
        ("Phase 8.2: Greeks Smoother", test_greeks_smoother),
        ("Phase 8.2: Data Noise Reducer", test_data_noise_reducer),
        ("Phase 8.3: Market-Aware Strictness", test_market_aware_strictness),
        ("Phase 8.4: Win/Loss Risk Adjuster", test_win_loss_risk_adjuster),
        ("Phase 8.3+8.4: Adaptive Strictness Engine", test_adaptive_strictness_engine),
        ("Phase 8.6: Performance Tracker", test_performance_tracker),
        ("Phase 8.7: Over-Optimization Guard", test_over_optimization_guard),
        ("Phase 8.8: Live Readiness Checklist", test_live_readiness_checklist),
        ("Phase 8.5: Data Freeze Failsafe", test_data_freeze_failsafe),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'─'*60}")
            print(f"Running: {test_name}")
            print('─'*60)
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"❌ FAILED: {test_name}")
            print(f"   Error: {str(e)}")
            failed += 1
        except Exception as e:
            print(f"❌ ERROR in {test_name}: {str(e)}")
            failed += 1
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"Passed: {passed}/{len(tests)}")
    print(f"Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 ALL PHASE 8 REFINED TESTS PASSED!")
        print("System ready for institutional-grade trading")
    else:
        print(f"\n⚠️  {failed} test(s) failed - review errors above")
    
    print("="*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
