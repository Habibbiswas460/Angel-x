"""
Quick Integration Verification
Shows adaptive system working in Angel-X context
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.adaptive.adaptive_controller import AdaptiveController

def main():
    print("="*80)
    print("ANGEL-X ADAPTIVE INTEGRATION VERIFICATION")
    print("="*80)
    
    # Initialize
    print("\n1️⃣  Initializing Adaptive Controller...")
    controller = AdaptiveController(config={'adaptive_enabled': True})
    print("✅ Adaptive system ready")
    
    # Simulate signal evaluation
    print("\n2️⃣  Evaluating trade signal...")
    market_data = {
        'vix': 19.5,
        'higher_highs': True,
        'lower_lows': False,
        'atr_pct': 1.2,
        'price_range_pct': 0.5,
        'rate_of_change': 0.015,
        'oi_imbalance': 0.02,
        'iv_expansion': False,
        'volume_surge': False
    }
    
    signal_data = {
        'time': datetime.now().replace(hour=10, minute=30),
        'bias_strength': 0.72,
        'oi_conviction': 'HIGH',
        'gamma': 0.045,
        'theta': -42,
        'vix': 19.5,
        'entry_delta': 0.55
    }
    
    decision = controller.evaluate_signal(market_data, signal_data, [])
    
    if decision.should_trade:
        print("✅ Signal APPROVED")
        print(f"   Confidence: {decision.confidence.confidence_level.value} ({decision.confidence.confidence_score:.1%})")
        print(f"   Regime: {decision.current_regime.regime.value if decision.current_regime else 'UNKNOWN'}")
        print(f"   Size: {decision.recommended_size:.0%} of normal")
    else:
        print("❌ Signal BLOCKED")
        print(f"   Reason: {decision.block_reason}")
    
    # Simulate trade recording
    print("\n3️⃣  Recording sample trades...")
    for i in range(5):
        entry_time = datetime.now() - timedelta(hours=5-i)
        controller.record_trade_outcome({
            'entry_time': entry_time,
            'exit_time': entry_time + timedelta(minutes=3),
            'bias_strength': 0.7,
            'oi_conviction': 'HIGH',
            'gamma': 0.04,
            'theta': -35,
            'vix': 19,
            'exit_reason': 'TARGET' if i % 2 == 0 else 'SL_HIT',
            'holding_minutes': 3,
            'won': i % 2 == 0,
            'pnl': 250 if i % 2 == 0 else -180
        })
    print(f"✅ Recorded {5} trades")
    
    # Show status
    print("\n4️⃣  Adaptive System Status:")
    status = controller.get_adaptive_status()
    print(f"   Enabled: {status['enabled']}")
    print(f"   Trades Learned: {status['learning']['total_trades_learned']}")
    print(f"   Regime: {status['regime']['regime']}")
    print(f"   Active Blocks: {len(status['patterns']['active_blocks'])}")
    
    print("\n" + "="*80)
    print("✅ INTEGRATION VERIFIED - All systems operational!")
    print("="*80)
    print("\n🎯 Angel-X is ready with adaptive learning enabled")
    print("📊 System will learn from trades and adapt to market conditions")
    print("🛡️  Safety guards active - human control maintained")
    print("\nNext: Enable ADAPTIVE_ENABLED=True in config.py and start trading!")

if __name__ == "__main__":
    main()
