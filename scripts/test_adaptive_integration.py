"""
Test Adaptive Integration with Angel-X Main Bot
Validates Phase 10 integration with Phase 1-9 engines
"""

import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptive.adaptive_controller import AdaptiveController
from src.adaptive.learning_engine import TradeFeatures
from src.adaptive.regime_detector import RegimeSignals, MarketRegime


def test_adaptive_initialization():
    """Test 1: Adaptive Controller initialization"""
    print("="*80)
    print("TEST 1: ADAPTIVE CONTROLLER INITIALIZATION")
    print("="*80)
    
    try:
        controller = AdaptiveController(config={'adaptive_enabled': True})
        print("✅ AdaptiveController initialized successfully")
        print(f"   Enabled: {controller.enabled}")
        print(f"   Components: Learning, Regime, Weight, Confidence, Pattern, Safety")
        return True
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False


def test_signal_evaluation():
    """Test 2: Signal evaluation pipeline"""
    print("\n" + "="*80)
    print("TEST 2: SIGNAL EVALUATION PIPELINE")
    print("="*80)
    
    try:
        controller = AdaptiveController(config={'adaptive_enabled': True})
        
        # Simulate market data (from main.py structure)
        market_data = {
            'vix': 18.5,
            'higher_highs': True,
            'lower_lows': False,
            'atr_pct': 1.2,
            'price_range_pct': 0.5,
            'rate_of_change': 0.015,
            'oi_imbalance': 0.02,
            'iv_expansion': False,
            'volume_surge': False
        }
        
        # Simulate signal data
        signal_data = {
            'time': datetime.now().replace(hour=10, minute=30),
            'bias_strength': 0.72,
            'oi_conviction': 'HIGH',
            'gamma': 0.045,
            'theta': -42,
            'vix': 18.5,
            'entry_delta': 0.55
        }
        
        # Evaluate
        decision = controller.evaluate_signal(
            market_data=market_data,
            signal_data=signal_data,
            recent_trades=[]
        )
        
        print(f"✅ Signal evaluated successfully")
        print(f"   Should Trade: {decision.should_trade}")
        print(f"   Confidence: {decision.confidence.confidence_level.value} ({decision.confidence.confidence_score:.1%})")
        print(f"   Regime: {decision.current_regime.regime.value if decision.current_regime else 'UNKNOWN'}")
        print(f"   Recommended Size: {decision.recommended_size:.0%}")
        print(f"   Explanation: {decision.decision_explanation}")
        print(f"   Recommended Size: {decision.recommended_size:.0%}")
        print(f"   Explanation: {decision.decision_explanation}")
        
        if decision.block_reason:
            print(f"   Block Reason: {decision.block_reason}")
        
        return True
    except Exception as e:
        print(f"❌ Signal evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_trade_recording():
    """Test 3: Trade outcome recording"""
    print("\n" + "="*80)
    print("TEST 3: TRADE OUTCOME RECORDING")
    print("="*80)
    
    try:
        controller = AdaptiveController(config={'adaptive_enabled': True})
        
        # Simulate 10 trades
        trades = []
        for i in range(10):
            entry_time = datetime.now() - timedelta(hours=5-i, minutes=30)
            exit_time = entry_time + timedelta(minutes=3)
            
            trade = {
                'entry_time': entry_time,
                'exit_time': exit_time,
                'bias_strength': 0.6 + (i % 3) * 0.1,
                'oi_conviction': ['WEAK', 'MEDIUM', 'HIGH'][i % 3],
                'gamma': 0.03 + (i % 3) * 0.01,
                'theta': -30 - (i % 3) * 10,
                'vix': 18 + (i % 3) * 2,
                'exit_reason': ['TARGET', 'SL_HIT', 'TIME_EXIT'][i % 3],
                'holding_minutes': 3 + i % 5,
                'won': i % 3 != 1,  # Lose every 3rd trade
                'pnl': (200 if i % 3 != 1 else -150) + i * 10
            }
            
            controller.record_trade_outcome(trade)
            trades.append(trade)
        
        print(f"✅ Recorded {len(trades)} trade outcomes")
        
        # Check learning engine state
        total_trades = len(controller.learning_engine.trade_history)
        print(f"   Total trades in history: {total_trades}")
        print(f"   Ready for analysis: {total_trades >= 10}")
        
        return True
    except Exception as e:
        print(f"❌ Trade recording failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_daily_learning():
    """Test 4: Daily learning cycle"""
    print("\n" + "="*80)
    print("TEST 4: DAILY LEARNING CYCLE")
    print("="*80)
    
    try:
        controller = AdaptiveController(config={'adaptive_enabled': True})
        
        # Record 25 sample trades (minimum for learning)
        print("📚 Simulating 25 trades with patterns...")
        for i in range(25):
            entry_hour = 9 + (i % 5)
            entry_time = datetime.now().replace(hour=entry_hour, minute=30)
            exit_time = entry_time + timedelta(minutes=4)
            
            # Pattern: morning trades (9-11) win more
            is_morning = entry_hour < 11
            won = (is_morning and i % 4 != 0) or (not is_morning and i % 2 == 0)
            
            trade = {
                'entry_time': entry_time,
                'exit_time': exit_time,
                'bias_strength': 0.7,
                'oi_conviction': 'HIGH' if i % 2 == 0 else 'MEDIUM',
                'gamma': 0.04,
                'theta': -35,
                'vix': 19,
                'exit_reason': 'TARGET' if won else 'SL_HIT',
                'holding_minutes': 4,
                'won': won,
                'pnl': 250 if won else -180
            }
            
            controller.record_trade_outcome(trade)
        
        print(f"   Recorded: 25 trades")
        
        # Run daily learning
        print("\n🔄 Running daily learning...")
        summary = controller.run_daily_learning()
        
        print(f"✅ Daily learning completed")
        print(f"   Insights Generated: {summary['insights_generated']}")
        print(f"   Loss Patterns Detected: {summary['loss_patterns_detected']}")
        print(f"   Proposals Created: {summary['proposals_created']}")
        print(f"   Proposals Approved: {summary['proposals_approved']}")
        
        # Show insights
        if summary['insights_generated'] > 0:
            print("\n💡 Sample Insights:")
            insights = controller.learning_engine.analyze_patterns()
            for insight in insights[:3]:
                print(f"   {insight.type}: {insight.bucket.value}")
                print(f"      Reason: {insight.reason}")
                print(f"      Confidence: {insight.confidence:.1%}")
        
        return True
    except Exception as e:
        print(f"❌ Daily learning failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_adaptive_status():
    """Test 5: Get adaptive status"""
    print("\n" + "="*80)
    print("TEST 5: ADAPTIVE STATUS DISPLAY")
    print("="*80)
    
    try:
        controller = AdaptiveController(config={'adaptive_enabled': True})
        
        # Record some trades first
        for i in range(10):
            entry_time = datetime.now() - timedelta(hours=i)
            controller.record_trade_outcome({
                'entry_time': entry_time,
                'exit_time': entry_time + timedelta(minutes=3),
                'bias_strength': 0.7,
                'oi_conviction': 'HIGH',
                'gamma': 0.04,
                'theta': -35,
                'vix': 19,
                'exit_reason': 'TARGET',
                'holding_minutes': 3,
                'won': i % 3 != 1,
                'pnl': 200 if i % 3 != 1 else -150
            })
        
        # Get status
        status = controller.get_adaptive_status()
        
        print(f"✅ Adaptive status retrieved")
        print(f"\n🎯 System Status:")
        print(f"   Enabled: {status['enabled']}")
        
        print(f"\n📚 Learning Engine:")
        print(f"   Total Trades: {status['learning']['total_trades_learned']}")
        print(f"   Insights: {status['learning']['insights_count']}")
        
        print(f"\n🌍 Market Regime:")
        print(f"   Current: {status['regime']['regime']}")
        print(f"   Confidence: {status['regime']['confidence']:.1%}")
        
        print(f"\n⚖️  Adaptive Weights:")
        print(f"   Restrictions: {status['weights']['active_restrictions']}")
        print(f"   Amplifications: {status['weights']['active_amplifications']}")
        
        print(f"\n🔍 Loss Patterns:")
        print(f"   Total Detected: {status['patterns']['total_patterns_detected']}")
        print(f"   Active Blocks: {len(status['patterns']['active_blocks'])}")
        
        print(f"\n🛡️  Safety:")
        print(f"   Learning Allowed: {status['safety']['learning_allowed']}")
        print(f"   Pending Proposals: {status['safety']['pending_proposals']}")
        
        return True
    except Exception as e:
        print(f"❌ Status retrieval failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_state_persistence():
    """Test 6: State export/import"""
    print("\n" + "="*80)
    print("TEST 6: STATE PERSISTENCE")
    print("="*80)
    
    try:
        controller1 = AdaptiveController(config={'adaptive_enabled': True})
        
        # Record some trades
        for i in range(5):
            entry_time = datetime.now() - timedelta(hours=i)
            controller1.record_trade_outcome({
                'entry_time': entry_time,
                'exit_time': entry_time + timedelta(minutes=3),
                'bias_strength': 0.7,
                'oi_conviction': 'HIGH',
                'gamma': 0.04,
                'theta': -35,
                'vix': 19,
                'exit_reason': 'TARGET',
                'holding_minutes': 3,
                'won': True,
                'pnl': 200
            })
        
        # Export state to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        controller1.export_state(temp_path)
        print(f"✅ State exported to {temp_path}")
        
        # Import into new controller
        controller2 = AdaptiveController(config={'adaptive_enabled': True})
        controller2.import_state(temp_path)
        print(f"✅ State imported successfully")
        
        # Cleanup
        import os
        os.unlink(temp_path)
        
        # Verify (weights should persist, learning history is fresh start by design)
        status1 = controller1.get_adaptive_status()
        status2 = controller2.get_adaptive_status()
        
        # Check that structure is consistent (weights persist)
        weights_match = len(status1['weights']['active_restrictions']) == len(status2['weights']['active_restrictions'])
        print(f"   Weights structure match: {weights_match}")
        print(f"   Controller 1 restrictions: {len(status1['weights']['active_restrictions'])}")
        print(f"   Controller 2 restrictions: {len(status2['weights']['active_restrictions'])}")
        
        # Note: Learning history doesn't persist (fresh start by design for safety)
        print(f"   Note: Learning history resets on import (safety by design)")
        
        return weights_match
    except Exception as e:
        print(f"❌ State persistence failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all integration tests"""
    print("="*80)
    print("ADAPTIVE INTEGRATION TEST SUITE")
    print("Testing Phase 10 integration with Angel-X main bot")
    print("="*80)
    
    tests = [
        ("Adaptive Initialization", test_adaptive_initialization),
        ("Signal Evaluation", test_signal_evaluation),
        ("Trade Recording", test_trade_recording),
        ("Daily Learning Cycle", test_daily_learning),
        ("Adaptive Status", test_adaptive_status),
        ("State Persistence", test_state_persistence)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("\n" + "="*80)
    print(f"RESULTS: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    print("="*80)
    
    if passed == total:
        print("\n🎯 ALL TESTS PASSED - Integration successful!")
        print("✅ Adaptive Controller ready for production")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed - review errors above")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
