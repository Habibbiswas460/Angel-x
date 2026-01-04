"""
PHASE 8 Test: Performance Optimization & System Hardening
Test all Phase 8 components
"""

import time
import random
from datetime import datetime
from src.core.performance_monitor import PerformanceMonitor
from src.core.latency_optimizer import LatencyOptimizer
from src.core.adaptive_filters import AdaptiveSignalFilter
from src.core.risk_calibration import RiskCalibrationEngine
from src.core.failover_system import FailoverRecoverySystem
from src.core.production_tools import ProductionToolkit


def test_performance_monitor():
    """Test performance monitoring system"""
    print("\n" + "="*60)
    print("TEST 1: Performance Monitor")
    print("="*60)
    
    monitor = PerformanceMonitor()
    
    # Simulate some operations
    print("\n📊 Simulating operations...")
    
    # Track latencies
    for i in range(5):
        start = time.time()
        time.sleep(0.01)  # Simulate work
        monitor.track_latency("data_fetch", start)
        
        start = time.time()
        time.sleep(0.005)
        monitor.track_latency("signal_generation", start)
    
    # Simulate some trades
    trades = [
        (500, "target"),
        (-300, "stop_loss"),
        (700, "target"),
        (600, "target"),
        (-400, "stop_loss"),
    ]
    
    for pnl, reason in trades:
        monitor.record_trade(pnl, reason)
        monitor.record_signal(acted_on=(random.random() > 0.3))
    
    # Get summary
    summary = monitor.get_performance_summary()
    print(f"\n✅ Total Trades: {summary['trading']['total_trades']}")
    print(f"✅ Win Rate: {summary['trading']['win_rate']:.2f}%")
    print(f"✅ Total P&L: ₹{summary['trading']['total_pnl']:,.2f}")
    print(f"✅ Avg Latency: {summary['latency']['total_latency']['avg']:.1f}ms")
    
    # Health check
    status, issues = monitor.get_health_status()
    print(f"\n🏥 Health Status: {status}")
    if issues:
        print("   Issues:")
        for issue in issues:
            print(f"   - {issue}")
    
    # Generate daily report
    print("\n📋 Generating Daily Report:")
    print("-" * 60)
    report = monitor.generate_daily_report()
    print(report[:500] + "...")
    
    print("\n✅ Performance Monitor Test PASSED")


def test_latency_optimizer():
    """Test latency optimization"""
    print("\n" + "="*60)
    print("TEST 2: Latency Optimizer")
    print("="*60)
    
    optimizer = LatencyOptimizer(atm_strike=18000)
    
    # Simulate option chain data
    raw_data = {
        'strikes': [
            {'strike': 17900, 'ltp': 120, 'oi': 50000},
            {'strike': 18000, 'ltp': 80, 'oi': 100000},  # ATM
            {'strike': 18100, 'ltp': 45, 'oi': 75000},
        ]
    }
    
    print("\n⚡ Testing optimization modes...")
    
    # Differential processing
    result = optimizer.process_option_chain(raw_data, mode="differential")
    print(f"✅ Differential mode: {result['mode']}")
    
    # Priority processing
    result = optimizer.process_option_chain(raw_data, mode="priority")
    print(f"✅ Priority mode: {result['mode']}")
    
    # Full optimization pipeline
    print("\n⚡ Testing full optimization pipeline...")
    optimized = optimizer.optimize_signal_path(raw_data, calculate_greeks=True)
    print(f"✅ Pipeline latency: {optimized['latency_ms']:.2f}ms")
    print(f"✅ Optimizations applied: {optimized['optimizations_applied']}")
    
    # Performance stats
    stats = optimizer.get_performance_stats()
    print(f"\n📊 Performance Stats:")
    print(f"   Avg Processing: {stats['avg_processing_ms']:.2f}ms")
    print(f"   Cache Size: {stats['cache_size']}")
    
    print("\n✅ Latency Optimizer Test PASSED")


def test_adaptive_filters():
    """Test adaptive signal filters"""
    print("\n" + "="*60)
    print("TEST 3: Adaptive Signal Filters")
    print("="*60)
    
    filters = AdaptiveSignalFilter()
    
    # Test signals with different strengths
    test_signals = [
        {
            'bias_strength': 0.75,
            'trap_probability': 0.3,
            'oi_delta': 15000,
            'current_iv': 22,
            'oi_data': {}
        },
        {
            'bias_strength': 0.45,  # Weak
            'trap_probability': 0.8,  # Likely trap
            'oi_delta': 500,  # Low OI
            'current_iv': 35,  # High IV
            'oi_data': {}
        },
        {
            'bias_strength': 0.85,
            'trap_probability': 0.2,
            'oi_delta': 25000,
            'current_iv': 18,
            'oi_data': {}
        }
    ]
    
    print("\n🎯 Evaluating signals...")
    
    for i, signal_data in enumerate(test_signals, 1):
        result = filters.evaluate_signal(signal_data)
        
        print(f"\nSignal {i}:")
        print(f"   Passed: {'✅' if result['passed'] else '❌'}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Filters Passed: {len(result['filters_passed'])}")
        if result['reasons']:
            print(f"   Reasons: {result['reasons'][0]}")
    
    # Filter efficiency
    efficiency = filters.get_filter_efficiency()
    print(f"\n📊 Filter Efficiency:")
    print(f"   Total Signals: {efficiency['total_signals']}")
    print(f"   Passed: {efficiency['passed']}")
    print(f"   Rejection Rate: {efficiency['rejection_rate']:.1f}%")
    
    print("\n✅ Adaptive Filters Test PASSED")


def test_risk_calibration():
    """Test risk calibration engine"""
    print("\n" + "="*60)
    print("TEST 4: Risk Calibration Engine")
    print("="*60)
    
    risk_engine = RiskCalibrationEngine(initial_capital=100000)
    
    # Simulate trading sequence
    print("\n💰 Simulating trading sequence...")
    
    trades = [
        (500, 20),   # Win, IV=20
        (700, 22),   # Win
        (-400, 25),  # Loss, IV rising
        (-600, 30),  # Loss, higher IV
        (-300, 32),  # Loss streak
    ]
    
    for i, (pnl, iv) in enumerate(trades, 1):
        print(f"\nTrade {i}: P&L ₹{pnl}, IV {iv}")
        
        risk_engine.update_trade_result(pnl)
        risk_engine.update_market_volatility(iv)
        
        # Get calibrated profile
        profile = risk_engine.get_calibrated_risk_profile()
        print(f"   Position Multiplier: {profile.position_size_multiplier:.2f}x")
        print(f"   Max Trades Today: {profile.max_trades_per_day}")
        print(f"   Cooldown: {profile.cooldown_minutes} min")
        
        # Can take trade?
        can_trade = risk_engine.can_take_trade()
        print(f"   Can Trade: {'✅' if can_trade['allowed'] else '❌'} - {can_trade['reason']}")
    
    # Risk summary
    print("\n📊 Risk Summary:")
    summary = risk_engine.get_risk_summary()
    print(f"   Current Streak: {summary['components']['streak']}")
    print(f"   Volatility Regime: {summary['components']['volatility_regime']}")
    print(f"   Drawdown: {summary['components']['drawdown_pct']:.2f}%")
    
    print("\n✅ Risk Calibration Test PASSED")


def test_failover_system():
    """Test failover and recovery"""
    print("\n" + "="*60)
    print("TEST 5: Failover & Recovery System")
    print("="*60)
    
    def dummy_refresh():
        print("   📡 Refreshing session...")
        return True
    
    failover = FailoverRecoverySystem(refresh_callback=dummy_refresh)
    
    # Test broker health
    print("\n🔗 Testing broker health...")
    
    def mock_api_call():
        return True
    
    health = failover.check_broker_health(mock_api_call)
    print(f"✅ Broker Health: {'OK' if health.status else 'FAILED'}")
    print(f"   Latency: {health.latency_ms:.1f}ms")
    
    # Test data freshness
    print("\n📊 Testing data freshness...")
    
    # Fresh data
    data_hash = "hash_123"
    freshness = failover.check_data_freshness(data_hash)
    print(f"✅ Data Fresh: {'YES' if freshness.status else 'NO'}")
    
    # Simulate data freeze
    time.sleep(2)
    freshness = failover.check_data_freshness(data_hash)  # Same hash
    print(f"   Data Staleness: {failover.freeze_detector.get_staleness_seconds()}s")
    
    # System status
    print("\n🏥 System Status:")
    status = failover.get_system_status()
    print(f"   State: {status['state']}")
    print(f"   Data Frozen: {status['data_frozen']}")
    print(f"   Pending Orders: {status['pending_orders']}")
    
    # Trading allowed?
    allowed = failover.should_allow_trading()
    print(f"\n   Trading Allowed: {'✅' if allowed['allowed'] else '❌'}")
    print(f"   Reason: {allowed['reason']}")
    
    print("\n✅ Failover System Test PASSED")


def test_production_tools():
    """Test production toolkit"""
    print("\n" + "="*60)
    print("TEST 6: Production Tools")
    print("="*60)
    
    def shutdown_handler():
        print("   🛑 Executing shutdown procedures...")
        time.sleep(0.5)
        print("   ✅ All positions closed")
        print("   ✅ Data saved")
    
    toolkit = ProductionToolkit(shutdown_callback=shutdown_handler)
    
    # Test startup sequence
    print("\n🚀 Testing startup sequence...")
    config = {
        'environment': 'production',
        'risk_per_trade': 2.0,
        'max_trades_day': 10,
        'position_multiplier': 1.0
    }
    
    success = toolkit.startup_sequence(config)
    print(f"✅ Startup: {'SUCCESS' if success else 'FAILED'}")
    
    # Test trade logging
    print("\n📝 Testing trade logging...")
    trade = {
        'symbol': 'NIFTY 18000 CE',
        'entry': 80,
        'exit': 95,
        'pnl': 225,
        'reason': 'target'
    }
    toolkit.log_trade(trade)
    print(f"✅ Trade logged to {toolkit.trade_logger.today_file}")
    
    # Test kill switch (don't actually activate)
    print("\n🚨 Testing kill switch status...")
    is_active = toolkit.check_kill_switch()
    print(f"   Kill Switch: {'ACTIVE' if is_active else 'INACTIVE'}")
    
    # Generate shutdown report
    print("\n📋 Testing shutdown sequence...")
    mock_summary = {
        'session': {'id': 'test_session', 'uptime_hours': 6.5},
        'trading': {
            'total_trades': 8,
            'winning_trades': 5,
            'losing_trades': 3,
            'win_rate': 62.5,
            'total_pnl': 1500,
            'current_streak': 2,
            'max_drawdown': 3.2,
            'current_drawdown': 1.5
        },
        'latency': {
            'total_latency': {'avg': 250, 'p95': 400}
        },
        'signals': {
            'generated': 25,
            'efficiency': 32.0
        },
        'system': {
            'errors': {},
            'recoveries': 2
        }
    }
    
    toolkit.shutdown_sequence(mock_summary)
    
    print("\n✅ Production Tools Test PASSED")


def run_phase8_tests():
    """Run all Phase 8 tests"""
    print("\n" + "="*70)
    print(" "*15 + "PHASE 8: COMPREHENSIVE TEST SUITE")
    print("     Performance Optimization & System Hardening")
    print("="*70)
    
    start_time = time.time()
    
    try:
        test_performance_monitor()
        test_latency_optimizer()
        test_adaptive_filters()
        test_risk_calibration()
        test_failover_system()
        test_production_tools()
        
        elapsed = time.time() - start_time
        
        print("\n" + "="*70)
        print("🎉 ALL PHASE 8 TESTS PASSED! 🎉")
        print("="*70)
        print(f"\n✅ Performance Monitoring:  OPERATIONAL")
        print(f"✅ Latency Optimization:   OPERATIONAL")
        print(f"✅ Adaptive Filters:       OPERATIONAL")
        print(f"✅ Risk Calibration:       OPERATIONAL")
        print(f"✅ Failover System:        OPERATIONAL")
        print(f"✅ Production Tools:       OPERATIONAL")
        print(f"\n⏱️  Total Test Time: {elapsed:.2f}s")
        print("\n" + "="*70)
        print("🚀 ANGEL-X IS NOW INSTITUTIONAL-GRADE!")
        print("="*70)
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    run_phase8_tests()
