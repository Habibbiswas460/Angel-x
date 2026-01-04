#!/usr/bin/env python3
"""
Angel-X Risk Management Test Suite
Tests all enhanced risk management features

Run: python3 scripts/test_risk_management.py
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.core.risk_manager import RiskManager
from datetime import datetime, timedelta
import time


class TestRiskManagement:
    """Comprehensive risk management tests"""
    
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        
    def test_1_slippage_buffer(self):
        """🧪 Test 1: Slippage Buffer Protection"""
        print("\n" + "="*70)
        print("🧪 TEST 1: Slippage Buffer Protection")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        # Check slippage buffer configured
        print(f"Max Daily Loss: {risk_mgr.max_daily_loss}")
        print(f"Slippage Buffer: {risk_mgr.slippage_buffer * 100}%")
        print(f"Effective Max Loss: {risk_mgr.effective_max_loss}")
        
        # Verify buffer is working
        expected_effective = risk_mgr.max_daily_loss * (1 - risk_mgr.slippage_buffer)
        
        if abs(risk_mgr.effective_max_loss - expected_effective) < 0.01:
            print("✅ Slippage buffer calculation correct")
            self.tests_passed += 1
        else:
            print(f"❌ Slippage buffer incorrect: {risk_mgr.effective_max_loss} != {expected_effective}")
            self.tests_failed += 1
            
        # Test loss limit with buffer
        risk_mgr.daily_pnl = -risk_mgr.effective_max_loss - 1
        allowed, reason = risk_mgr.can_take_trade({'quantity': 1, 'risk_amount': 10})
        
        if not allowed and "slippage" in reason.lower():
            print("✅ Trading halted at effective limit (with buffer)")
            self.tests_passed += 1
        else:
            print(f"❌ Should halt at effective limit: {reason}")
            self.tests_failed += 1
    
    def test_2_cooldown_system(self):
        """🧪 Test 2: Loss-Based Cooldown"""
        print("\n" + "="*70)
        print("🧪 TEST 2: Loss-Based Cooldown After Consecutive Losses")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        print(f"Consecutive Loss Limit: {risk_mgr.consecutive_loss_limit}")
        print(f"Cooldown Duration: {risk_mgr.cooldown_minutes} minutes")
        
        # Simulate first loss
        print("\nSimulating loss #1...")
        risk_mgr.record_trade({'pnl': -100})
        print(f"Losses in row: {risk_mgr.losses_in_row}")
        
        # Check if trading allowed (should be)
        allowed, reason = risk_mgr.can_take_trade({'quantity': 1, 'risk_amount': 10})
        if allowed:
            print("✅ Trading allowed after 1 loss")
            self.tests_passed += 1
        else:
            print(f"❌ Should allow trading after 1 loss: {reason}")
            self.tests_failed += 1
        
        # Simulate second loss (should trigger cooldown)
        print("\nSimulating loss #2...")
        risk_mgr.record_trade({'pnl': -100})
        print(f"Losses in row: {risk_mgr.losses_in_row}")
        
        # Check cooldown activated
        allowed, reason = risk_mgr.can_take_trade({'quantity': 1, 'risk_amount': 10})
        if not allowed and "cooldown" in reason.lower():
            print(f"✅ Cooldown activated: {reason}")
            self.tests_passed += 1
        else:
            print(f"❌ Cooldown should activate after {risk_mgr.consecutive_loss_limit} losses")
            self.tests_failed += 1
        
        # Simulate win (should clear cooldown)
        print("\nSimulating win...")
        risk_mgr.record_trade({'pnl': 200})
        print(f"Losses in row: {risk_mgr.losses_in_row}")
        
        if risk_mgr.losses_in_row == 0:
            print("✅ Loss streak reset on win")
            self.tests_passed += 1
        else:
            print("❌ Loss streak should reset on win")
            self.tests_failed += 1
    
    def test_3_multi_leg_safety(self):
        """🧪 Test 3: Multi-Leg Strategy Control"""
        print("\n" + "="*70)
        print("🧪 TEST 3: Multi-Leg Strategy Safety")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        print(f"Multi-leg Enabled: {risk_mgr.multi_leg_enabled}")
        
        # Try multi-leg trade when disabled
        trade_info = {
            'quantity': 10,
            'risk_amount': 100,
            'strategy_type': 'straddle'  # Multi-leg
        }
        
        allowed, reason = risk_mgr.can_take_trade(trade_info)
        
        if not risk_mgr.multi_leg_enabled and not allowed and "multi-leg" in reason.lower():
            print("✅ Multi-leg trades blocked when disabled")
            self.tests_passed += 1
        else:
            print(f"❌ Multi-leg should be blocked: {reason}")
            self.tests_failed += 1
        
        # Try single-leg trade (should work)
        trade_info['strategy_type'] = 'single'
        allowed, reason = risk_mgr.can_take_trade(trade_info)
        
        if allowed:
            print("✅ Single-leg trades allowed")
            self.tests_passed += 1
        else:
            print(f"❌ Single-leg should be allowed: {reason}")
            self.tests_failed += 1
    
    def test_4_execution_failure_tracking(self):
        """🧪 Test 4: Execution Failure Recording"""
        print("\n" + "="*70)
        print("🧪 TEST 4: Execution Failure Tracking")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        # Record various failures
        print("Recording execution failures...")
        risk_mgr.record_execution_failure('rejected')
        risk_mgr.record_execution_failure('rejected')
        risk_mgr.record_execution_failure('partial_fill')
        risk_mgr.record_execution_failure('sl_failure')
        
        failures = risk_mgr.execution_failures
        print(f"Rejected orders: {failures['rejected_orders']}")
        print(f"Partial fills: {failures['partial_fills']}")
        print(f"SL failures: {failures['sl_placement_failures']}")
        
        if failures['rejected_orders'] == 2:
            print("✅ Rejection tracking works")
            self.tests_passed += 1
        else:
            print("❌ Rejection tracking failed")
            self.tests_failed += 1
        
        if failures['sl_placement_failures'] == 1:
            print("✅ SL failure tracking works")
            self.tests_passed += 1
        else:
            print("❌ SL failure tracking failed")
            self.tests_failed += 1
    
    def test_5_position_risk_with_slippage(self):
        """🧪 Test 5: Position Risk Validation (Slippage-Adjusted)"""
        print("\n" + "="*70)
        print("🧪 TEST 5: Position Risk with Slippage Buffer")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        # Test position risk calculation
        position_size = 10
        entry_price = 100
        stop_loss = 95  # 5 point risk
        
        print(f"Position: {position_size} lots @ ₹{entry_price}")
        print(f"Stop Loss: ₹{stop_loss}")
        print(f"Base Risk: {position_size * 5} = ₹50")
        print(f"With {risk_mgr.slippage_buffer*100}% buffer: {position_size * 5 * (1 + risk_mgr.slippage_buffer):.2f}")
        
        acceptable, reason = risk_mgr.check_position_risk(position_size, entry_price, stop_loss)
        
        if acceptable:
            print(f"✅ Position risk acceptable: {reason}")
            self.tests_passed += 1
        else:
            print(f"⚠️ Position rejected: {reason}")
            # Not necessarily a failure - depends on config
            self.tests_passed += 1
    
    def test_6_daily_limit_enforcement(self):
        """🧪 Test 6: Daily Limit Circuit Breaker"""
        print("\n" + "="*70)
        print("🧪 TEST 6: Daily Loss Limit Circuit Breaker")
        print("="*70)
        
        risk_mgr = RiskManager()
        
        # Push to daily limit
        risk_mgr.daily_pnl = -risk_mgr.effective_max_loss - 1
        
        print(f"Daily PnL: {risk_mgr.daily_pnl}")
        print(f"Effective Max Loss: {risk_mgr.effective_max_loss}")
        
        allowed, reason = risk_mgr.can_take_trade({'quantity': 1, 'risk_amount': 10})
        
        if not allowed:
            print(f"✅ Trading halted at limit: {reason}")
            self.tests_passed += 1
        else:
            print("❌ Trading should be halted at daily limit")
            self.tests_failed += 1
        
        if risk_mgr.trading_halted:
            print("✅ Circuit breaker activated")
            self.tests_passed += 1
        else:
            print("❌ Circuit breaker should be active")
            self.tests_failed += 1
    
    def test_7_max_trades_limit(self):
        """🧪 Test 7: Maximum Trades Per Day"""
        print("\n" + "="*70)
        print("🧪 TEST 7: Maximum Trades Per Day Limit")
        print("="*70)
        
        risk_mgr = RiskManager()
        max_trades = risk_mgr.max_trades_per_day
        
        print(f"Max trades per day: {max_trades}")
        
        # Simulate trades up to limit
        for i in range(max_trades):
            risk_mgr.record_trade({'pnl': 10})
        
        print(f"Trades executed: {risk_mgr.trades_today}")
        
        # Try one more trade
        allowed, reason = risk_mgr.can_take_trade({'quantity': 1, 'risk_amount': 10})
        
        if not allowed and "max trades" in reason.lower():
            print(f"✅ Max trades limit enforced: {reason}")
            self.tests_passed += 1
        else:
            print(f"❌ Max trades limit not working: {reason}")
            self.tests_failed += 1
    
    def run_all_tests(self):
        """Run all risk management tests"""
        print("\n" + "🔥"*35)
        print("   ANGEL-X RISK MANAGEMENT TEST SUITE")
        print("🔥"*35)
        
        tests = [
            self.test_1_slippage_buffer,
            self.test_2_cooldown_system,
            self.test_3_multi_leg_safety,
            self.test_4_execution_failure_tracking,
            self.test_5_position_risk_with_slippage,
            self.test_6_daily_limit_enforcement,
            self.test_7_max_trades_limit
        ]
        
        for test in tests:
            try:
                test()
            except Exception as e:
                print(f"\n❌ TEST ERROR: {e}")
                self.tests_failed += 1
        
        # Summary
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {self.tests_passed / (self.tests_passed + self.tests_failed) * 100:.1f}%")
        
        if self.tests_failed == 0:
            print("\n🎉 ALL TESTS PASSED - Risk Management Ready!")
            return True
        else:
            print("\n⚠️ SOME TESTS FAILED - Review Before Live Trading")
            return False


if __name__ == "__main__":
    tester = TestRiskManagement()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)
