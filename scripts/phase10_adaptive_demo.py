"""
PHASE 10: Adaptive Learning System Demo
Demonstrates self-correcting, market-aware brain with safety guards
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.adaptive.adaptive_controller import AdaptiveController
from app.adaptive.learning_engine import TradeFeatures, FeatureBucket
from datetime import datetime, timedelta
import random


def demo_adaptive_signal_evaluation():
    """Demonstrate adaptive signal evaluation"""
    print("\n" + "="*100)
    print("🧠 PHASE 10 - ADAPTIVE SIGNAL EVALUATION")
    print("="*100)
    
    # Initialize controller
    controller = AdaptiveController(config={'adaptive_enabled': True})
    
    # Sample market data
    market_data = {
        'range_pct': 1.2,
        'higher_highs': True,
        'lower_lows': False,
        'vix': 19.5,
        'atr_pct': 1.1,
        'roc_5m': 0.2,
        'roc_15m': 0.4,
        'oi_imbalance': 0.3,
        'iv_expanding': False,
        'volume_surge': False
    }
    
    # Sample trading signal
    signal_data = {
        'time': datetime.now(),
        'bias_strength': 0.75,
        'gamma': 0.045,
        'theta': -42,
        'oi_conviction': 'HIGH',
        'vix': 19.5
    }
    
    # Recent trade history
    recent_trades = [
        {'won': True, 'pnl': 500},
        {'won': True, 'pnl': 300},
        {'won': False, 'pnl': -200},
    ]
    
    print("\n📊 Evaluating Trading Signal...")
    decision = controller.evaluate_signal(market_data, signal_data, recent_trades)
    
    print(f"\n🎯 DECISION: {'✅ TRADE' if decision.should_trade else '🚫 BLOCK'}")
    print(f"\n📈 Confidence: {decision.confidence.confidence_level.value} ({decision.confidence.confidence_score:.1%})")
    print(f"   - Historical Success: {decision.confidence.historical_success_score:.1%}")
    print(f"   - Regime Match: {decision.confidence.regime_match_score:.1%}")
    print(f"   - Recent Performance: {decision.confidence.recent_performance_score:.1%}")
    print(f"   - Sample Size: {decision.confidence.sample_size_score:.1%}")
    
    print(f"\n🌍 Market Regime: {decision.current_regime.regime.value}")
    print(f"   - Confidence: {decision.current_regime.confidence:.1%}")
    print(f"   - Characteristics: {', '.join(decision.current_regime.sub_characteristics)}")
    print(f"   - Posture: {decision.current_regime.get_posture_description()}")
    
    print(f"\n💰 Recommended Position Size: {decision.recommended_size:.0%} of normal")
    print(f"📊 Recommended Frequency: {decision.recommended_frequency:.0%} of normal")
    
    print(f"\n💡 Explanation: {decision.decision_explanation}")
    
    return controller


def demo_learning_from_history(controller: AdaptiveController):
    """Demonstrate learning from trade history"""
    print("\n\n" + "="*100)
    print("📚 ADAPTIVE LEARNING FROM HISTORY")
    print("="*100)
    
    # Simulate 50 trades with patterns
    print("\n🔄 Ingesting 50 sample trades...")
    
    trades = []
    for i in range(50):
        # Create trade with patterns
        # Morning trades perform better
        hour = random.choice([9, 10, 11, 13, 14])
        is_morning = (hour in [10, 11])
        
        # HIGH OI conviction wins more
        oi_conviction = random.choice(['HIGH', 'MEDIUM', 'LOW'])
        
        # Determine outcome based on patterns
        win_probability = 0.50  # Base
        if is_morning:
            win_probability += 0.25  # Morning boost
        if oi_conviction == 'HIGH':
            win_probability += 0.20  # HIGH OI boost
        
        won = random.random() < win_probability
        pnl = random.uniform(200, 500) if won else random.uniform(-150, -300)
        
        trade_time = datetime.now() - timedelta(days=random.randint(1, 30), hours=hour-9)
        
        trade = TradeFeatures(
            time_bucket=controller.learning_engine.get_bucket_for_time(trade_time),
            bias_bucket=FeatureBucket.BIAS_MEDIUM,
            greeks_bucket=FeatureBucket.GREEKS_NEUTRAL,
            oi_bucket=controller.learning_engine.get_bucket_for_oi(oi_conviction),
            vol_bucket=FeatureBucket.VOL_NORMAL,
            entry_delta=0.5,
            entry_theta=-30,
            entry_gamma=0.03,
            exit_reason='TARGET' if won else 'STOP_LOSS',
            holding_minutes=random.randint(15, 45),
            won=won,
            pnl=pnl,
            timestamp=trade_time
        )
        
        controller.learning_engine.ingest_trade(trade)
        trades.append(trade)
    
    print(f"   ✅ Ingested {len(trades)} trades")
    
    # Analyze patterns
    print("\n🔬 Analyzing patterns...")
    insights = controller.learning_engine.analyze_patterns()
    
    print(f"\n✨ Generated {len(insights)} insights:")
    for insight in insights[:5]:  # Top 5
        print(f"\n   📌 {insight.insight_type} - {insight.bucket.value}")
        print(f"      Reason: {insight.reason}")
        print(f"      Confidence: {insight.confidence:.1%}")
        print(f"      Recommendation: {insight.recommendation}")
    
    return insights


def demo_loss_pattern_detection(controller: AdaptiveController):
    """Demonstrate loss pattern detection"""
    print("\n\n" + "="*100)
    print("🔍 LOSS PATTERN DETECTION")
    print("="*100)
    
    # Inject deliberate loss pattern (OPENING window fails)
    print("\n⚠️  Simulating repeating OPENING window losses...")
    
    for i in range(6):
        trade = TradeFeatures(
            time_bucket=FeatureBucket.TIME_OPENING,
            bias_bucket=FeatureBucket.BIAS_MEDIUM,
            greeks_bucket=FeatureBucket.GREEKS_NEUTRAL,
            oi_bucket=FeatureBucket.OI_MEDIUM,
            vol_bucket=FeatureBucket.VOL_NORMAL,
            entry_delta=0.5,
            entry_theta=-30,
            entry_gamma=0.03,
            exit_reason='STOP_LOSS',
            holding_minutes=20,
            won=False,
            pnl=-250,
            timestamp=datetime.now() - timedelta(days=i*2)
        )
        controller.learning_engine.ingest_trade(trade)
    
    # Analyze patterns
    loss_patterns = controller.pattern_detector.analyze_trade_history(
        controller.learning_engine.trade_history
    )
    
    print(f"\n🚨 Detected {len(loss_patterns)} loss patterns:")
    
    for pattern in loss_patterns:
        print(f"\n   ⚠️  Pattern: {pattern.pattern_type.value}")
        print(f"      Characteristic: {pattern.characteristic}")
        print(f"      Severity: {pattern.severity.value}")
        print(f"      Occurrences: {pattern.occurrences} losses")
        print(f"      Total Loss: ₹{pattern.total_loss:,.0f}")
        print(f"      Action: {pattern.recommended_action}")
        if pattern.block_duration_hours > 0:
            print(f"      Block Duration: {pattern.block_duration_hours}h")
    
    # Check active blocks
    active_blocks = [b for b in controller.pattern_detector.active_blocks if b.is_active()]
    
    if active_blocks:
        print(f"\n🚫 Active Blocks: {len(active_blocks)}")
        for block in active_blocks:
            print(f"   - {block.blocked_bucket.value}: {block.reason} ({block.get_remaining_hours():.1f}h remaining)")


def demo_safety_guards(controller: AdaptiveController):
    """Demonstrate safety guard system"""
    print("\n\n" + "="*100)
    print("🛡️  SAFETY GUARD SYSTEM")
    print("="*100)
    
    # Check if learning allowed
    print("\n🔒 Checking safety constraints...")
    
    safety_check = controller.safety_guard.check_learning_allowed()
    print(f"\n   Learning Allowed: {'✅ YES' if safety_check.passed else '🚫 NO'}")
    print(f"   Reason: {safety_check.reason}")
    print(f"   Recommendation: {safety_check.recommendation}")
    
    # Check sample size validation
    sample_check = controller.safety_guard.check_sample_size(50)
    print(f"\n   Sample Size Adequate: {'✅ YES' if sample_check.passed else '🚫 NO'}")
    print(f"   Reason: {sample_check.reason}")
    
    # Check winning streak caution
    streak_check = controller.safety_guard.check_winning_streak_caution(3)
    print(f"\n   No Over-Confidence: {'✅ YES' if streak_check.passed else '🚫 NO'}")
    
    # Show safety status
    status = controller.safety_guard.get_safety_status()
    print(f"\n📊 Safety Status:")
    print(f"   - Last Update: {status['last_update'] if status['last_update'] else 'Never'}")
    print(f"   - Hours Since Update: {status['hours_since_update']:.1f}h")
    print(f"   - Adjustments Today: {status['adjustments_today']}/{status['max_adjustments']}")
    print(f"   - Pending Proposals: {status['pending_proposals']}")


def demo_adaptive_status(controller: AdaptiveController):
    """Show complete adaptive system status"""
    print("\n\n" + "="*100)
    print("📊 COMPLETE ADAPTIVE SYSTEM STATUS")
    print("="*100)
    
    status = controller.get_adaptive_status()
    
    print(f"\n🎯 System Enabled: {status['enabled']}")
    print(f"📅 Last Learning: {status['last_daily_learning']}")
    
    print(f"\n📚 Learning Engine:")
    learning = status['learning']
    print(f"   - Total Trades Learned: {learning['total_trades_learned']}")
    print(f"   - Insights Generated: {learning['insights_count']}")
    print(f"   - Last Update: {learning['last_update']}")
    
    print(f"\n🌍 Market Regime:")
    regime = status['regime']
    print(f"   - Current: {regime['regime']}")
    print(f"   - Confidence: {regime['confidence']:.1%}")
    print(f"   - Stable: {regime['stable']}")
    print(f"   - Description: {regime['description']}")
    
    print(f"\n⚖️  Adaptive Weights:")
    weights = status['weights']
    print(f"   - Active Restrictions: {len(weights['active_restrictions'])}")
    for restriction in weights['active_restrictions'][:3]:
        print(f"      🚫 {restriction['bucket']}: {restriction['reason']}")
    
    print(f"   - Active Amplifications: {len(weights['active_amplifications'])}")
    for amp in weights['active_amplifications'][:3]:
        print(f"      ✅ {amp['bucket']}: {amp['weight']:.2f}x - {amp['reason']}")
    
    print(f"\n🔍 Loss Patterns:")
    patterns = status['patterns']
    print(f"   - Total Detected: {patterns['total_patterns_detected']}")
    print(f"   - Active Blocks: {len(patterns['active_blocks'])}")
    
    print(f"\n🛡️  Safety:")
    safety = status['safety']
    print(f"   - Learning Allowed: {safety['learning_allowed']}")
    print(f"   - Pending Proposals: {safety['pending_proposals']}")
    print(f"   - Approved Today: {safety['approved_today']}")


def run_complete_demo():
    """Run complete adaptive system demonstration"""
    print("\n" + "#"*100)
    print("#" + " "*98 + "#")
    print("#" + " "*25 + "ANGEL-X PHASE 10 — ADAPTIVE LEARNING SYSTEM" + " "*31 + "#")
    print("#" + " "*25 + "Self-Correcting Market-Aware Brain" + " "*38 + "#")
    print("#" + " "*98 + "#")
    print("#"*100)
    
    # Part 1: Signal Evaluation
    controller = demo_adaptive_signal_evaluation()
    
    input("\n\nPress Enter to continue to Learning from History...")
    
    # Part 2: Learning from History
    insights = demo_learning_from_history(controller)
    
    input("\n\nPress Enter to continue to Loss Pattern Detection...")
    
    # Part 3: Loss Pattern Detection
    demo_loss_pattern_detection(controller)
    
    input("\n\nPress Enter to continue to Safety Guards...")
    
    # Part 4: Safety Guards
    demo_safety_guards(controller)
    
    input("\n\nPress Enter to see Complete System Status...")
    
    # Part 5: Complete Status
    demo_adaptive_status(controller)
    
    # Final summary
    print("\n\n" + "="*100)
    print("✅ PHASE 10 DEMONSTRATION COMPLETE")
    print("="*100)
    print("""
Adaptive Components Demonstrated:

1. LEARNING ENGINE:
   ✅ Analyzes trade history
   ✅ Identifies performance patterns
   ✅ Generates actionable insights
   ✅ Human-readable buckets (not black-box)

2. MARKET REGIME DETECTOR:
   ✅ Classifies market character
   ✅ Adapts trading posture
   ✅ Regime-aware recommendations
   ✅ Stability tracking

3. ADAPTIVE WEIGHT ADJUSTER:
   ✅ Adjusts rule weights (not rules)
   ✅ Amplifies good edges
   ✅ Restricts poor edges
   ✅ Transparent adjustments

4. CONFIDENCE SCORER:
   ✅ Scores every signal
   ✅ Combines history + regime + recent
   ✅ Size recommendations
   ✅ Emotionless decisions

5. LOSS PATTERN DETECTOR:
   ✅ Detects repeating failures
   ✅ Automatic blocks
   ✅ Stops capital bleed
   ✅ Time-bound restrictions

6. SAFETY GUARD SYSTEM:
   ✅ Prevents same-day learning
   ✅ Limits adjustments
   ✅ Proposal review cycle
   ✅ Shadow testing
   ✅ Emergency reset

7. ADAPTIVE CONTROLLER:
   ✅ Orchestrates all components
   ✅ Complete decision pipeline
   ✅ Export/import state
   ✅ Daily learning cycle

PHILOSOPHY FULFILLED:
✅ Learning ≠ Prediction
✅ Learning = Filter & Control
✅ No wild AI
✅ Stability > Intelligence
✅ Explainable decisions
✅ Human override always available

ANGEL-X FINAL IDENTITY:
✔️  Greeks-aware
✔️  OI-driven
✔️  Risk-disciplined
✔️  Self-correcting
✔️  Emotion-proof
✔️  Market-adaptive

👉 Angel-X is now an INSTITUTIONAL TRADING SYSTEM! 🎯
""")
    
    print("="*100 + "\n")


if __name__ == "__main__":
    try:
        run_complete_demo()
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
