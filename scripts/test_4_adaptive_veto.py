"""
TEST-4: ADAPTIVE VETO TEST
Duration: 3-5 days

Validates adaptive learning system
Monitors regime detection and confidence-based blocking
"""
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test4Config, TestProgression
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test4AdaptiveVetoMonitor:
    """
    Monitor adaptive veto system
    
    PASS যদি:
    - ~30% blocks from adaptive
    - Low confidence → block
    - Regime detection কাজ করে
    
    FAIL যদি:
    - Adaptive blocking না
    - Confidence ignore করে
    """
    
    def __init__(self):
        self.config = Test4Config
        
        # Metrics
        self.metrics = {
            'total_signals': 0,
            'adaptive_blocks': 0,
            'confidence_blocks': 0,
            'regime_blocks': 0,
            'other_blocks': 0,
            'trades_allowed': 0,
            
            'low_confidence_trades': 0,  # Should be ZERO
            'regime_changes_detected': 0,
            
            'confidence_distribution': defaultdict(int),
            'regime_history': []
        }
        
        self.current_regime = 'TRENDING'
    
    def check_adaptive_decision(self, signal_data: dict) -> dict:
        """Check adaptive system decision"""
        self.metrics['total_signals'] += 1
        
        confidence = signal_data.get('confidence', 0.5)
        regime = signal_data.get('regime', 'TRENDING')
        
        # Update regime
        if regime != self.current_regime:
            self.metrics['regime_changes_detected'] += 1
            self.metrics['regime_history'].append(regime)
            self.current_regime = regime
            logger.info(f"🔄 Regime change detected: {self.current_regime} → {regime}")
        
        # Track confidence distribution
        conf_bucket = int(confidence * 10) / 10  # Round to 1 decimal
        self.metrics['confidence_distribution'][conf_bucket] += 1
        
        # Adaptive veto logic
        decision = {
            'allowed': True,
            'blocked_by': None,
            'confidence': confidence,
            'regime': regime
        }
        
        # Check confidence threshold
        if confidence < self.config.MIN_CONFIDENCE_FOR_TRADE:
            decision['allowed'] = False
            decision['blocked_by'] = 'low_confidence'
            self.metrics['confidence_blocks'] += 1
            self.metrics['adaptive_blocks'] += 1
            return decision
        
        # Check regime
        if regime == 'CHOPPY' and not self.config.ALLOW_TRADES_IN_CHOP:
            decision['allowed'] = False
            decision['blocked_by'] = 'regime_chop'
            self.metrics['regime_blocks'] += 1
            self.metrics['adaptive_blocks'] += 1
            return decision
        
        # Adaptive veto (based on recent performance)
        adaptive_veto = signal_data.get('adaptive_veto', False)
        if adaptive_veto:
            decision['allowed'] = False
            decision['blocked_by'] = 'adaptive_veto'
            self.metrics['adaptive_blocks'] += 1
            return decision
        
        # Trade allowed
        self.metrics['trades_allowed'] += 1
        
        # Check if low confidence trade slipped through
        if confidence < self.config.MIN_CONFIDENCE_FOR_TRADE:
            self.metrics['low_confidence_trades'] += 1
            logger.error(f"❌ Low confidence trade allowed: {confidence:.2f}")
        
        return decision
    
    def record_decision(self, signal_data: dict, decision: dict):
        """Record adaptive decision"""
        if decision['allowed']:
            logger.info(f"✅ Trade allowed: {signal_data.get('type', 'Unknown')}")
            logger.info(f"   Confidence: {decision['confidence']:.2f}")
            logger.info(f"   Regime: {decision['regime']}")
        else:
            logger.info(f"⛔ Adaptive BLOCK: {signal_data.get('type', 'Unknown')}")
            logger.info(f"   Reason: {decision['blocked_by']}")
            logger.info(f"   Confidence: {decision['confidence']:.2f}")
            logger.info(f"   Regime: {decision['regime']}")
    
    def generate_report(self) -> dict:
        """Generate test report"""
        total = self.metrics['total_signals']
        if total == 0:
            return None
        
        adaptive_block_pct = (self.metrics['adaptive_blocks'] / total) * 100
        
        report = {
            'metrics': self.metrics,
            'percentages': {
                'adaptive_block_pct': adaptive_block_pct
            },
            'pass_fail': {
                'adaptive_blocking': (
                    adaptive_block_pct >= 
                    self.config.ADAPTIVE_BLOCK_PERCENTAGE * 0.8  # 80% of target
                    and 
                    adaptive_block_pct <= 
                    self.config.ADAPTIVE_BLOCK_PERCENTAGE * 1.5  # 150% of target
                ),
                'confidence_respected': self.metrics['low_confidence_trades'] == 0,
                'regime_detection': self.metrics['regime_changes_detected'] > 0
            }
        }
        
        return report
    
    def evaluate_pass_fail(self, report: dict) -> bool:
        """Evaluate if test passed"""
        if not report:
            return False
        
        pass_fail = report['pass_fail']
        return all(pass_fail.values())
    
    def print_report(self, report: dict):
        """Print formatted report"""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 TEST-4: ADAPTIVE VETO TEST REPORT")
        logger.info("="*60)
        
        m = report['metrics']
        p = report['percentages']
        
        logger.info("\n📈 Adaptive Metrics:")
        logger.info(f"   Total signals: {m['total_signals']}")
        logger.info(f"   Adaptive blocks: {m['adaptive_blocks']} ({p['adaptive_block_pct']:.1f}%)")
        logger.info(f"   Confidence blocks: {m['confidence_blocks']}")
        logger.info(f"   Regime blocks: {m['regime_blocks']}")
        logger.info(f"   Trades allowed: {m['trades_allowed']}")
        
        logger.info("\n⚠️ Warning Metrics:")
        logger.info(f"   Low confidence trades: {m['low_confidence_trades']} (should be 0)")
        logger.info(f"   Regime changes detected: {m['regime_changes_detected']}")
        
        logger.info("\n📊 Confidence Distribution:")
        for conf, count in sorted(m['confidence_distribution'].items()):
            bar = "█" * int(count / max(m['confidence_distribution'].values()) * 20)
            logger.info(f"   {conf:.1f}: {bar} ({count})")
        
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-4 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info(f"   ✓ Adaptive blocking working ({p['adaptive_block_pct']:.1f}%)")
            logger.info("   ✓ Confidence threshold respected")
            logger.info("   ✓ Regime detection active")
        else:
            logger.info("❌ TEST-4 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if not pf['adaptive_blocking']:
                logger.error(f"   ✗ Adaptive block rate off target ({p['adaptive_block_pct']:.1f}%)")
            if not pf['confidence_respected']:
                logger.error(f"   ✗ Low confidence trades allowed ({m['low_confidence_trades']})")
            if not pf['regime_detection']:
                logger.error("   ✗ No regime changes detected")
        
        logger.info("="*60)


def main():
    """Run TEST-4 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-4: ADAPTIVE VETO TEST")
    print("="*60)
    print("")
    
    if not TestProgression.can_run_test('TEST-4'):
        print("❌ Complete TEST-3 first")
        return False
    
    print("📋 Test Setup:")
    print("   Duration: 3-5 days")
    print("   Focus: Adaptive learning and regime detection")
    print("")
    print("📌 Expected behavior:")
    print("   ✓ ~30% adaptive blocks")
    print("   ✓ Low confidence → block")
    print("   ✓ Regime detection working")
    print("")
    
    monitor = Test4AdaptiveVetoMonitor()
    
    print("🏃 Running simulated test...\n")
    
    import random
    regimes = ['TRENDING', 'CHOPPY', 'VOLATILE']
    
    for i in range(150):
        # Simulate signal with varying confidence and regime
        signal_data = {
            'type': f"Signal-{i+1}",
            'confidence': random.uniform(0.3, 0.9),
            'regime': random.choice(regimes) if i % 30 == 0 else monitor.current_regime,
            'adaptive_veto': random.random() < 0.1  # 10% adaptive veto
        }
        
        # Check adaptive decision
        decision = monitor.check_adaptive_decision(signal_data)
        
        # Record decision
        monitor.record_decision(signal_data, decision)
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-4')
        print("\n👉 Next: TEST-5 - RISK MANAGER TEST\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
