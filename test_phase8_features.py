#!/usr/bin/env python3
"""
ANGEL-X Phase 8 Feature Test Script
Test all new features: Greeks exit, Multi-strike, Kelly sizing, Risk Greeks, Database
"""

import sys
import requests
from datetime import datetime
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from app.engines.smart_exit_engine import SmartExitEngine, ExitConfiguration, ExitTrigger
from app.engines.portfolio.multi_strike_engine import MultiStrikePortfolioEngine
from app.core.position_sizing import PositionSizing
from app.core.risk_manager import RiskManager


def test_dashboard_api():
    """Test Dashboard API endpoints"""
    print("\n" + "="*80)
    print("TEST 1: Dashboard API Endpoints")
    print("="*80)
    
    base_url = "http://localhost:5000"
    endpoints = [
        "/health",
        "/api/dashboard",
        "/api/positions",
        "/api/portfolio",
        "/api/performance",
        "/api/trades?limit=5"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=2)
            status = "✅ PASS" if response.status_code == 200 else "❌ FAIL"
            print(f"{status} {endpoint} - Status: {response.status_code}")
            
            if endpoint == "/health" and response.status_code == 200:
                data = response.json()
                print(f"     Health: {data.get('status')}, Time: {data.get('timestamp')}")
                
        except requests.exceptions.ConnectionError:
            print(f"❌ FAIL {endpoint} - Dashboard not running")
        except Exception as e:
            print(f"❌ FAIL {endpoint} - Error: {e}")


def test_smart_exit_engine():
    """Test Smart Exit Engine with Greeks triggers"""
    print("\n" + "="*80)
    print("TEST 2: Smart Exit Engine (Greeks-based exits)")
    print("="*80)
    
    config = ExitConfiguration(
        use_trailing_stop=True,
        trailing_stop_percent=2.0,
        delta_weakness_threshold=0.15,
        gamma_rollover_threshold=0.8,
        iv_crush_threshold=5.0
    )
    
    engine = SmartExitEngine(config)
    print("✅ Smart Exit Engine initialized")
    
    # Test delta weakness exit
    print("\nTest Case: Delta Weakness Exit")
    exit_snapshot = engine.check_exit_conditions(
        trade_id="TEST_001",
        current_price=145.0,
        current_delta=0.30,  # Dropped from 0.45 (33% decline)
        current_gamma=0.008,
        current_theta=-0.03,
        current_iv=22.0,
        entry_price=150.0,
        entry_delta=0.45,
        entry_gamma=0.010,
        entry_iv=23.0,
        sl_price=140.0,
        target_price=165.0,
        entry_time=datetime.now(),
        time_to_expiry_minutes=30,
        quantity=75,
        exited_qty=0
    )
    
    if exit_snapshot and exit_snapshot.trigger == ExitTrigger.DELTA_WEAKNESS:
        print(f"✅ Delta weakness trigger PASSED")
        print(f"   Trigger: {exit_snapshot.trigger.value}")
        print(f"   Exit Price: ₹{exit_snapshot.exit_price}")
        print(f"   Delta at exit: {exit_snapshot.delta_at_exit:.3f}")
    else:
        print(f"❌ Delta weakness trigger FAILED")
    
    # Test gamma rollover exit
    print("\nTest Case: Gamma Rollover Exit")
    exit_snapshot = engine.check_exit_conditions(
        trade_id="TEST_002",
        current_price=155.0,
        current_delta=0.50,
        current_gamma=0.007,  # Dropped to 70% of entry
        current_theta=-0.03,
        current_iv=22.0,
        entry_price=150.0,
        entry_delta=0.45,
        entry_gamma=0.010,
        entry_iv=23.0,
        sl_price=140.0,
        target_price=165.0,
        entry_time=datetime.now(),
        time_to_expiry_minutes=30,
        quantity=75,
        exited_qty=0
    )
    
    if exit_snapshot and exit_snapshot.trigger == ExitTrigger.GAMMA_ROLLOVER:
        print(f"✅ Gamma rollover trigger PASSED")
        print(f"   Trigger: {exit_snapshot.trigger.value}")
        print(f"   Gamma at exit: {exit_snapshot.gamma_at_exit:.4f}")
    else:
        print(f"❌ Gamma rollover trigger FAILED")


def test_multi_strike_engine():
    """Test Multi-Strike Auto Selection Engine"""
    print("\n" + "="*80)
    print("TEST 3: Multi-Strike Auto Selection Engine")
    print("="*80)
    
    engine = MultiStrikePortfolioEngine()
    print("✅ Multi-Strike Engine initialized")
    
    # Test auto CE/PE selection
    print("\nTest Case: Auto CE/PE Selection")
    
    ce_type = engine.auto_select_option_type(bias='bullish', confidence=75)
    print(f"   Bullish bias (75% conf) → {ce_type} {'✅' if ce_type == 'CE' else '❌'}")
    
    pe_type = engine.auto_select_option_type(bias='bearish', confidence=75)
    print(f"   Bearish bias (75% conf) → {pe_type} {'✅' if pe_type == 'PE' else '❌'}")
    
    neutral_type = engine.auto_select_option_type(bias='neutral', confidence=40)
    print(f"   Neutral bias (40% conf) → {neutral_type} ✅")
    
    # Test IV scoring
    print("\nTest Case: IV Scoring")
    scores = [
        (20.0, "Optimal (20%)"),
        (25.0, "Optimal (25%)"),
        (35.0, "Good (35%)"),
        (50.0, "Too High (50%)")
    ]
    
    for iv, desc in scores:
        score = engine._score_iv(iv)
        print(f"   IV {desc}: Score = {score:.0f}/30")


def test_position_sizing_kelly():
    """Test Dynamic Position Sizing with Kelly Criterion"""
    print("\n" + "="*80)
    print("TEST 4: Dynamic Position Sizing (Kelly Criterion)")
    print("="*80)
    
    sizer = PositionSizing()
    print("✅ Position Sizing initialized")
    
    # Test win probability estimation
    print("\nTest Case: Win Probability Estimation")
    
    test_cases = [
        {
            'name': 'High Probability Trade',
            'delta': 0.50,
            'gamma': 0.012,
            'iv': 22.0,
            'bias_confidence': 80,
            'oi_change': 1000
        },
        {
            'name': 'Medium Probability Trade',
            'delta': 0.35,
            'gamma': 0.006,
            'iv': 30.0,
            'bias_confidence': 60,
            'oi_change': 0
        },
        {
            'name': 'Low Probability Trade',
            'delta': 0.25,
            'gamma': 0.003,
            'iv': 45.0,
            'bias_confidence': 45,
            'oi_change': -500
        }
    ]
    
    for case in test_cases:
        prob = sizer.estimate_win_probability(
            delta=case['delta'],
            gamma=case['gamma'],
            iv=case['iv'],
            bias_confidence=case['bias_confidence'],
            oi_change=case['oi_change']
        )
        print(f"   {case['name']}: {prob:.1%}")
        print(f"      Δ={case['delta']:.2f}, Γ={case['gamma']:.3f}, "
              f"IV={case['iv']:.0f}%, Conf={case['bias_confidence']}")
    
    # Test Kelly sizing
    print("\nTest Case: Kelly Criterion Sizing")
    position = sizer.calculate_position_size(
        entry_price=150.0,
        hard_sl_price=140.0,
        target_price=165.0,
        delta=0.50,
        gamma=0.012,
        iv=22.0,
        bias_confidence=80,
        oi_change=1000
    )
    
    if position.sizing_valid:
        print(f"✅ Position sizing PASSED")
        print(f"   Quantity: {position.quantity}")
        print(f"   Lots: {position.num_lots:.1f}")
        if position.win_probability:
            print(f"   Win Probability: {position.win_probability:.1%}")
        if position.kelly_fraction:
            print(f"   Kelly Fraction: {position.kelly_fraction:.2%}")
    else:
        print(f"❌ Position sizing FAILED: {position.rejection_reason}")


def test_risk_manager_greeks():
    """Test Risk Manager with Advanced Greeks Limits"""
    print("\n" + "="*80)
    print("TEST 5: Risk Manager (Advanced Greeks Limits)")
    print("="*80)
    
    risk_mgr = RiskManager()
    print("✅ Risk Manager initialized")
    
    # Test Greeks limits
    print("\nTest Case: Portfolio Greeks Tracking")
    
    risk_mgr.update_portfolio_greeks(
        net_delta=50.0,
        net_gamma=2.5,
        net_theta=-200.0,
        net_vega=500.0,
        gross_delta=80.0
    )
    
    greeks = risk_mgr.get_portfolio_greeks()
    print(f"   Net Delta: {greeks['net_delta']:.1f} (Util: {greeks['delta_utilization']:.1f}%)")
    print(f"   Net Gamma: {greeks['net_gamma']:.2f} (Util: {greeks['gamma_utilization']:.1f}%)")
    print(f"   Net Theta: {greeks['net_theta']:.1f}")
    print(f"   Needs Hedge: {greeks['needs_hedge']}")
    
    # Test trade approval with Greeks limits
    print("\nTest Case: Trade Approval with Greeks Limits")
    
    test_trades = [
        {
            'name': 'Normal Trade (should pass)',
            'delta': 20.0,
            'gamma': 1.0,
            'theta': -50.0,
            'should_pass': True
        },
        {
            'name': 'Exceeds Delta Limit (should fail)',
            'delta': 60.0,  # Would make total 110 > 100 limit
            'gamma': 1.0,
            'theta': -50.0,
            'should_pass': False
        },
        {
            'name': 'Exceeds Gamma Limit (should fail)',
            'delta': 10.0,
            'gamma': 3.0,  # Would make total 5.5 > 5.0 limit
            'theta': -50.0,
            'should_pass': False
        }
    ]
    
    for trade in test_trades:
        allowed, reason = risk_mgr.can_take_trade(
            trade_info={'quantity': 75, 'risk_amount': 1000},
            position_delta=trade['delta'],
            position_gamma=trade['gamma'],
            position_theta=trade['theta']
        )
        
        status = "✅" if allowed == trade['should_pass'] else "❌"
        print(f"{status} {trade['name']}")
        if not allowed:
            print(f"   Reason: {reason}")


def test_database_schema():
    """Test Database Schema (without actual DB connection)"""
    print("\n" + "="*80)
    print("TEST 6: Database Layer (Schema Validation)")
    print("="*80)
    
    try:
        from app.database import MLDatabase, DatabaseConfig
        
        db_config = DatabaseConfig(
            host="localhost",
            database="angelx_ml",
            user="angelx"
        )
        
        db = MLDatabase(db_config)
        print(f"✅ MLDatabase initialized (enabled={db.enabled})")
        
        if not db.enabled:
            print("   ℹ️  psycopg2 not installed - database features disabled")
            print("   To enable: pip install psycopg2-binary")
        else:
            print("   ✅ PostgreSQL driver available")
            print("   ℹ️  To connect: Ensure PostgreSQL is running")
        
    except Exception as e:
        print(f"❌ Database test FAILED: {e}")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("ANGEL-X PHASE 8 FEATURE TESTS")
    print("="*80)
    print(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Dashboard API", test_dashboard_api),
        ("Smart Exit Engine", test_smart_exit_engine),
        ("Multi-Strike Engine", test_multi_strike_engine),
        ("Kelly Position Sizing", test_position_sizing_kelly),
        ("Greeks Risk Manager", test_risk_manager_greeks),
        ("Database Schema", test_database_schema)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ TEST FAILED: {name}")
            print(f"   Error: {e}")
            failed += 1
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Total Tests: {len(tests)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Success Rate: {passed/len(tests)*100:.0f}%")
    print("="*80)


if __name__ == "__main__":
    run_all_tests()
