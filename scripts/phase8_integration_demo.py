"""
PHASE 8 REFINED - Integration Example
Demonstrates how all components work together in a trading cycle
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.noise_reduction import DataNoiseReducer
from src.core.adaptive_strictness import AdaptiveStrictnessEngine
from src.core.metrics_tracker import PerformanceTracker, TradeRecord
from src.core.production_readiness import OverOptimizationGuard, LiveReadinessChecklist
from src.core.failover_system import DataFreezeDetector
# from src.core.latency_optimizer import LatencyOptimizer  # Not used in demo
from datetime import datetime
import hashlib


def hash_data(data):
    """Create hash of data for freeze detection"""
    return hashlib.md5(str(data).encode()).hexdigest()


def run_integrated_trading_cycle():
    """
    Demonstrates a complete trading cycle using all Phase 8 refined components
    """
    
    print("="*70)
    print("PHASE 8 REFINED - INTEGRATED TRADING CYCLE DEMONSTRATION")
    print("="*70)
    
    # ============================================================
    # STEP 1: PRE-MARKET - Live Readiness Check
    # ============================================================
    print("\n[STEP 1] Running Pre-Market Checklist...")
    
    guard = OverOptimizationGuard()
    guard.lock_parameters("Live trading active")
    
    checklist = LiveReadinessChecklist()
    
    readiness = checklist.run_full_checklist(
        guard=guard,
        kill_switch_callback=lambda dry_run: True,  # Mock
        broker_test_func=lambda: True,  # Mock
        data_test_func=lambda: True,  # Mock
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
    
    if not readiness['ready_for_live']:
        print(f"❌ NOT READY: {readiness['failed_items']}")
        return
    
    print("✅ Pre-market checklist PASSED - System ready")
    
    # ============================================================
    # STEP 2: INITIALIZE COMPONENTS
    # ============================================================
    print("\n[STEP 2] Initializing Trading Components...")
    
    noise_reducer = DataNoiseReducer()
    strictness_engine = AdaptiveStrictnessEngine()
    metrics_tracker = PerformanceTracker()
    data_freeze_detector = DataFreezeDetector(max_staleness_seconds=10)
    # latency_optimizer = LatencyOptimizer()  # Skipped in demo (requires ATM strike)
    
    print("✅ All components initialized")
    
    # ============================================================
    # STEP 3: PROCESS MARKET DATA
    # ============================================================
    print("\n[STEP 3] Processing Market Data...")
    
    # Simulate incoming market data
    raw_market_data = {
        'NIFTY_CE_18000': {
            'oi': 50000,
            'volume': 5000,
            'delta': 0.52,
            'theta': -50,
            'gamma': 0.05,
            'ltp': 125.50
        }
    }
    
    # Update data freeze detector
    data_hash = hash_data(raw_market_data)
    data_freeze_detector.update_data(data_hash)
    
    # Check data freshness (CRITICAL)
    freshness_check = data_freeze_detector.can_trade()
    if not freshness_check['allowed']:
        print(f"❌ Data not fresh: {freshness_check['reason']}")
        return
    
    print(f"✅ Data freshness OK: {freshness_check['reason']}")
    
    # Apply noise reduction
    cleaned = noise_reducer.process_option_data(
        "NIFTY_CE_18000",
        raw_market_data['NIFTY_CE_18000']
    )
    
    print(f"   Filters applied: {cleaned['filters_applied']}")
    if 'noise_detected' in cleaned:
        print(f"   Noise detected: {cleaned['noise_detected']}")
    
    # ============================================================
    # STEP 4: EVALUATE TRADING CONDITIONS
    # ============================================================
    print("\n[STEP 4] Evaluating Trading Conditions...")
    
    current_iv = 26.5  # Current implied volatility
    recent_pnl = -300  # Recent loss
    
    conditions = strictness_engine.evaluate_trading_conditions(
        current_iv=current_iv,
        recent_pnl=recent_pnl
    )
    
    print(f"   Can trade: {conditions['can_trade']}")
    if 'session' in conditions:
        print(f"   Session: {conditions['session']}")
    if 'volatility' in conditions:
        print(f"   Volatility: {conditions['volatility']}")
    if 'risk_multiplier' in conditions:
        print(f"   Risk multiplier: {conditions['risk_multiplier']:.2f}")
    
    if not conditions['can_trade']:
        print(f"   ⚠️ Pause reasons: {conditions.get('pause_reasons', [])}")
        print("   Trading paused due to conditions")
        # Continue with demo anyway
    
    # Get signal requirements
    requirements = strictness_engine.get_signal_requirements(current_iv)
    print(f"   Required bias strength: {requirements['min_bias_strength']:.2f}")
    print(f"   Required OI delta: {requirements['min_oi_delta']}")
    print(f"   Max trap probability: {requirements['max_trap_probability']:.2f}")
    
    # ============================================================
    # STEP 5: SIMULATE TRADE
    # ============================================================
    print("\n[STEP 5] Simulating Trade...")
    
    # Assume signal meets requirements and trade executes
    simulated_trade = TradeRecord(
        trade_id="DEMO_001",
        timestamp=datetime.now(),
        symbol="NIFTY_CE_18000",
        entry_price=125.50,
        exit_price=130.25,
        quantity=25,
        pnl=118.75,  # (130.25 - 125.50) * 25
        holding_time_seconds=780,  # 13 minutes
        exit_reason='TARGET',
        entry_iv=26.5,
        exit_iv=26.8,
        entry_time="MORNING",
        entry_delta=0.52,
        entry_theta=-50,
        entry_gamma=0.05,
        oi_delta=2000,
        oi_conviction='HIGH',
        bias_strength=0.78,
        bias_direction='BULLISH'
    )
    
    print(f"   Trade executed: {simulated_trade.symbol}")
    print(f"   Entry: ₹{simulated_trade.entry_price:.2f} → Exit: ₹{simulated_trade.exit_price:.2f}")
    print(f"   PnL: ₹{simulated_trade.pnl:.2f}")
    print(f"   Exit reason: {simulated_trade.exit_reason}")
    
    # ============================================================
    # STEP 6: RECORD METRICS
    # ============================================================
    print("\n[STEP 6] Recording Performance Metrics...")
    
    metrics_tracker.record_trade(simulated_trade)
    
    # Update risk adjuster
    strictness_engine.risk_adjuster.record_trade(pnl=simulated_trade.pnl)
    
    print("✅ Trade recorded in metrics tracker")
    
    # ============================================================
    # STEP 7: POST-TRADE ANALYSIS
    # ============================================================
    print("\n[STEP 7] Post-Trade Analysis...")
    
    # Get session performance
    session_stats = metrics_tracker.get_win_rate_by_time()
    if session_stats:
        print("\nSession Performance:")
        for session, stats in session_stats.items():
            trades_count = stats.get('trades', stats.get('count', 0))
            win_rate = stats.get('win_rate', 0)
            print(f"   {session}: {trades_count} trades, {win_rate:.1f}% win rate")
    
    # Get OI conviction analysis
    oi_stats = metrics_tracker.get_oi_conviction_analysis()
    if oi_stats:
        print("\nOI Conviction Analysis:")
        for conviction, stats in oi_stats.items():
            trades_count = stats.get('trades', stats.get('count', 0))
            if trades_count > 0:
                win_rate = stats.get('win_rate', 0)
                print(f"   {conviction}: {trades_count} trades, {win_rate:.1f}% win rate")
    
    # Get insights (if available)
    print("\n✅ Post-trade analysis complete")
    
    # ============================================================
    # STEP 8: RISK SUMMARY
    # ============================================================
    print("\n[STEP 8] Risk Management Summary...")
    
    risk_summary = strictness_engine.risk_adjuster.get_risk_summary()
    print(f"   Consecutive wins: {risk_summary['consecutive_wins']}")
    print(f"   Consecutive losses: {risk_summary['consecutive_losses']}")
    print(f"   Current risk: {risk_summary['current_risk_pct']:.2f}%")
    print(f"   Recovery mode: {risk_summary['recovery_mode']}")
    
    # ============================================================
    # COMPLETION
    # ============================================================
    print("\n" + "="*70)
    print("TRADING CYCLE COMPLETE")
    print("="*70)
    print("\n✅ All Phase 8 components integrated successfully")
    print("✅ Noise reduction active")
    print("✅ Adaptive strictness applied")
    print("✅ Risk adjustment based on performance")
    print("✅ Metrics tracked for analysis")
    print("✅ Data freshness verified")
    print("\n🚀 System ready for production trading")


def demonstrate_parameter_change_workflow():
    """
    Demonstrates the safe parameter change workflow with over-optimization guard
    """
    
    print("\n\n" + "="*70)
    print("PARAMETER CHANGE WORKFLOW DEMONSTRATION")
    print("="*70)
    
    guard = OverOptimizationGuard(min_review_interval_days=7)
    
    # Lock parameters for live trading
    print("\n[1] Locking parameters for live trading...")
    guard.lock_parameters("Live trading active")
    
    # Try to modify (should be blocked)
    print("\n[2] Attempting to modify parameters (should fail)...")
    result = guard.can_modify_parameters()
    print(f"   Can modify: {result['allowed']}")
    print(f"   Reason: {result['reason']}")
    
    # Unlock for weekly review
    print("\n[3] Weekly review - unlocking parameters...")
    guard.unlock_parameters()
    
    # Simulate review interval passed
    from datetime import timedelta
    guard.last_review_date = datetime.now() - timedelta(days=8)
    
    # Propose parameter change
    print("\n[4] Proposing parameter change...")
    change = guard.propose_parameter_change(
        param_name='bias_threshold',
        new_value=0.70,
        reason='Improve precision based on last week performance'
    )
    print(f"   Approved: {change['approved']}")
    print(f"   Change ID: {change.get('change_id', 'N/A')}")
    
    # Test in paper mode
    print("\n[5] Testing in paper mode...")
    paper_results = {
        'passed': True,
        'win_rate': 68.5,
        'trades': 15,
        'sharpe': 1.8
    }
    
    if change['approved']:
        change_id = change['change_id']
        guard.mark_tested_in_paper(change_id, paper_results)
        print(f"   ✅ Paper test passed - change applied")
    
    # Check for over-tuning
    print("\n[6] Checking for over-optimization...")
    overtuning = guard.detect_overtuning()
    print(f"   Over-tuning detected: {overtuning['overtuning_detected']}")
    print(f"   Recent changes: {overtuning['recent_changes_count']}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # Run integrated trading cycle
    run_integrated_trading_cycle()
    
    # Demonstrate parameter change workflow
    demonstrate_parameter_change_workflow()
    
    print("\n\n🎉 Integration demonstration complete!")
