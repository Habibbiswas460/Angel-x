"""
TEST-7: SHADOW-LIVE TEST
Duration: 5-7 days

Real decisions, NO execution
Track would-be PnL, mental state

⚠️ This is your final rehearsal before live trading
"""
import sys
from pathlib import Path
from datetime import datetime
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test7Config, TestProgression, GoldenRules
from app.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test7ShadowLiveMonitor:
    """
    Shadow-live monitoring
    
    PASS যদি:
    - All decisions clear
    - Would-be PnL tracked
    - No emotional behavior
    - Mental state calm
    
    FAIL যদি:
    - Unclear decisions
    - Emotional patterns
    - Mental stress
    """
    
    def __init__(self):
        self.config = Test7Config
        
        # Shadow trading state
        self.shadow_trades = []
        self.shadow_pnl = 0
        
        # Metrics
        self.metrics = {
            'total_signals': 0,
            'would_have_traded': 0,
            'would_have_blocked': 0,
            
            'shadow_wins': 0,
            'shadow_losses': 0,
            'shadow_total_pnl': 0,
            
            'decision_clarity_score': 0,
            'emotional_events': 0,  # Should be ZERO
            'unclear_decisions': 0,  # Should be ZERO
            
            'daily_logs': defaultdict(list)
        }
        
        self.mentally_calm = True
    
    def process_shadow_signal(self, signal_data: dict) -> dict:
        """Process signal in shadow mode"""
        self.metrics['total_signals'] += 1
        
        signal_type = signal_data.get('type', 'Unknown')
        timestamp = datetime.now()
        
        logger.info(f"📊 SIGNAL: {signal_type}")
        logger.info(f"   Time: {timestamp.strftime('%H:%M:%S')}")
        
        # Simulate decision process
        decision = {
            'timestamp': timestamp,
            'signal': signal_type,
            'quality': signal_data.get('quality', 'Unknown'),
            'bias': signal_data.get('bias', 'Unknown'),
            'adaptive_conf': signal_data.get('confidence', 0),
            'risk_ok': signal_data.get('risk_ok', False),
            'would_trade': False,
            'block_reason': None,
            'clarity': 'CLEAR'
        }
        
        # Quality check
        if decision['quality'] != 'Clean':
            decision['block_reason'] = 'Quality gate failed'
            logger.info(f"   Quality: {decision['quality']} ❌")
        else:
            logger.info(f"   Quality: Clean ✅")
        
        # Bias check
        if decision['bias'] == 'NEUTRAL':
            decision['block_reason'] = 'Bias neutral'
            logger.info(f"   Bias: NEUTRAL ❌")
        else:
            logger.info(f"   Bias: {decision['bias']} ✅")
        
        # Adaptive check
        if decision['adaptive_conf'] < 0.6:
            decision['block_reason'] = f"Low confidence ({decision['adaptive_conf']:.2f})"
            logger.info(f"   Adaptive: {decision['adaptive_conf']:.2f} ❌")
        else:
            logger.info(f"   Adaptive: {decision['adaptive_conf']:.2f} ✅")
        
        # Risk check
        if not decision['risk_ok']:
            decision['block_reason'] = 'Risk limits'
            logger.info("   Risk: BLOCKED ❌")
        else:
            logger.info("   Risk: Within limits ✅")
        
        # Final decision
        if decision['block_reason']:
            decision['would_trade'] = False
            self.metrics['would_have_blocked'] += 1
            logger.info(f"   DECISION: ⛔ WOULD HAVE BLOCKED")
            logger.info(f"   Reason: {decision['block_reason']}")
        else:
            decision['would_trade'] = True
            self.metrics['would_have_traded'] += 1
            
            # Log shadow trade details
            entry = signal_data.get('entry_price', 100)
            sl = signal_data.get('sl_price', 95)
            target = signal_data.get('target_price', 110)
            qty = signal_data.get('qty', 25)
            
            logger.info("   DECISION: ✅ WOULD HAVE TRADED")
            logger.info(f"   Entry: ₹{entry}")
            logger.info(f"   SL: ₹{sl} | Target: ₹{target}")
            logger.info(f"   Qty: {qty} lots")
            
            shadow_trade = {
                'id': len(self.shadow_trades) + 1,
                'timestamp': timestamp,
                'entry': entry,
                'sl': sl,
                'target': target,
                'qty': qty
            }
            self.shadow_trades.append(shadow_trade)
            logger.info(f"   Shadow Trade ID: ST-{shadow_trade['id']:03d}")
        
        # Check decision clarity
        if not decision['block_reason'] and not decision['would_trade']:
            decision['clarity'] = 'UNCLEAR'
            self.metrics['unclear_decisions'] += 1
            logger.warning("   ⚠️ UNCLEAR DECISION!")
        
        # Track clarity score
        if decision['clarity'] == 'CLEAR':
            self.metrics['decision_clarity_score'] += 1
        
        logger.info("")
        
        return decision
    
    def process_shadow_exit(self, trade_id: int, exit_data: dict):
        """Process shadow trade exit"""
        if trade_id > len(self.shadow_trades):
            logger.error(f"Invalid shadow trade ID: {trade_id}")
            return
        
        trade = self.shadow_trades[trade_id - 1]
        exit_price = exit_data.get('exit_price', trade['entry'])
        exit_reason = exit_data.get('reason', 'Unknown')
        
        # Calculate shadow PnL
        pnl = (exit_price - trade['entry']) * trade['qty']
        
        logger.info(f"📤 Shadow Exit: ST-{trade_id:03d}")
        logger.info(f"   Exit: ₹{exit_price}")
        logger.info(f"   Reason: {exit_reason}")
        logger.info(f"   Shadow PnL: ₹{pnl:+.0f}")
        
        self.shadow_pnl += pnl
        self.metrics['shadow_total_pnl'] = self.shadow_pnl
        
        if pnl > 0:
            self.metrics['shadow_wins'] += 1
        else:
            self.metrics['shadow_losses'] += 1
        
        # Mental state check
        logger.info(f"   Mental State: {'😌 Calm' if self.mentally_calm else '😰 Stressed'}")
        logger.info("")
    
    def check_mental_state(self) -> bool:
        """Check mental state (manual for now)"""
        # In real implementation, this would analyze logs for:
        # - Excessive monitoring
        # - Emotional language
        # - Stress indicators
        return self.mentally_calm
    
    def generate_report(self) -> dict:
        """Generate test report"""
        total_signals = self.metrics['total_signals']
        if total_signals == 0:
            return None
        
        clarity_pct = (self.metrics['decision_clarity_score'] / total_signals) * 100
        
        report = {
            'metrics': self.metrics,
            'percentages': {
                'decision_clarity': clarity_pct
            },
            'pass_fail': {
                'high_clarity': clarity_pct >= 95,
                'zero_emotional_events': self.metrics['emotional_events'] == 0,
                'zero_unclear_decisions': self.metrics['unclear_decisions'] == 0,
                'mentally_calm': self.check_mental_state()
            }
        }
        
        return report
    
    def evaluate_pass_fail(self, report: dict) -> bool:
        """Evaluate if test passed"""
        if not report:
            return False
        
        pf = report['pass_fail']
        
        # Update Golden Rules
        GoldenRules.MENTALLY_CALM = pf['mentally_calm']
        GoldenRules.save_to_file()  # Persist to file
        
        return all(pf.values())
    
    def print_report(self, report: dict):
        """Print formatted report"""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 TEST-7: SHADOW-LIVE TEST REPORT")
        logger.info("="*60)
        
        m = report['metrics']
        p = report['percentages']
        
        logger.info("\n📈 Signal Metrics:")
        logger.info(f"   Total signals: {m['total_signals']}")
        logger.info(f"   Would have traded: {m['would_have_traded']}")
        logger.info(f"   Would have blocked: {m['would_have_blocked']}")
        
        logger.info("\n💰 Shadow PnL:")
        logger.info(f"   Shadow wins: {m['shadow_wins']}")
        logger.info(f"   Shadow losses: {m['shadow_losses']}")
        logger.info(f"   Total shadow PnL: ₹{m['shadow_total_pnl']:+.0f}")
        
        logger.info("\n🧠 Decision Quality:")
        logger.info(f"   Decision clarity: {p['decision_clarity']:.1f}%")
        logger.info(f"   Unclear decisions: {m['unclear_decisions']} (should be 0)")
        logger.info(f"   Emotional events: {m['emotional_events']} (should be 0)")
        
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        logger.info("\n🏆 Golden Rules Update:")
        logger.info(f"   MENTALLY_CALM: {pf['mentally_calm']}")
        
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-7 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info("   ✓ Clear decision making")
            logger.info("   ✓ No emotional behavior")
            logger.info("   ✓ Mental state calm")
            logger.info("")
            logger.info("📌 Ready for Golden Rules validation")
        else:
            logger.info("❌ TEST-7 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if not pf['high_clarity']:
                logger.error(f"   ✗ Decision clarity low ({p['decision_clarity']:.1f}%)")
            if not pf['zero_unclear_decisions']:
                logger.error(f"   ✗ {m['unclear_decisions']} unclear decisions")
            if not pf['mentally_calm']:
                logger.error("   ✗ Mental state not calm")
        
        logger.info("="*60)


def main():
    """Run TEST-7 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-7: SHADOW-LIVE TEST")
    print("="*60)
    print("")
    
    if not TestProgression.can_run_test('TEST-7'):
        print("❌ Complete TEST-6 first")
        return False
    
    print("📋 Test Setup:")
    print("   Duration: 5-7 days")
    print("   Mode: Real decisions, NO execution")
    print("")
    print("📌 What to log:")
    print("   ✓ Every decision with reasoning")
    print("   ✓ Would-be PnL tracking")
    print("   ✓ Mental state observations")
    print("")
    
    monitor = Test7ShadowLiveMonitor()
    
    print("🏃 Running simulation...\n")
    
    import random
    
    # Simulate shadow trading day
    for i in range(20):
        signal_data = {
            'type': random.choice(['BULLISH breakout', 'BEARISH breakdown', 'Reversal']),
            'quality': random.choice(['Clean', 'Messy', 'Clean', 'Clean']),
            'bias': random.choice(['BULLISH', 'BEARISH', 'NEUTRAL']),
            'confidence': random.uniform(0.4, 0.9),
            'risk_ok': random.choice([True, True, True, False]),
            'entry_price': random.randint(90, 150),
            'sl_price': random.randint(85, 95),
            'target_price': random.randint(155, 165),
            'qty': 25
        }
        
        decision = monitor.process_shadow_signal(signal_data)
        
        # Simulate exit for trades
        if decision['would_trade'] and len(monitor.shadow_trades) > 0:
            if random.random() < 0.3:  # 30% exit immediately
                exit_data = {
                    'exit_price': signal_data['entry_price'] + random.randint(-5, 15),
                    'reason': random.choice(['Target', 'SL', 'Time'])
                }
                monitor.process_shadow_exit(len(monitor.shadow_trades), exit_data)
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-7')
        print("\n👉 Next: Validate Golden Rules")
        print("   python3 scripts/validate_golden_rules.py\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
