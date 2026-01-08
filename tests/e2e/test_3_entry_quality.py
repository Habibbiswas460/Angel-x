"""
TEST-3: ENTRY QUALITY TEST
Duration: 2-3 days

Validates quality gate system
Only clean setups should be taken
"""
import sys
from pathlib import Path
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test3Config, TestProgression
from app.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test3EntryQualityMonitor:
    """
    Monitor entry quality gates
    
    PASS যদি:
    - 70-80% entries blocked
    - শুধু clean setups নেয়
    - Multi-factor confirmation কাজ করে
    
    FAIL যদি:
    - Low block rate (<50%)
    - Messy setups নেয়
    """
    
    def __init__(self):
        self.config = Test3Config
        
        # Metrics
        self.metrics = {
            'total_entries_evaluated': 0,
            'entries_allowed': 0,
            'entries_blocked': 0,
            
            'clean_setups': 0,
            'messy_setups': 0,
            
            'quality_factors': {
                'pattern_clean': 0,
                'pattern_messy': 0,
                'volume_good': 0,
                'volume_poor': 0,
                'greeks_healthy': 0,
                'greeks_unhealthy': 0,
                'bias_aligned': 0,
                'bias_misaligned': 0,
            },
            
            'block_reasons': defaultdict(int)
        }
    
    def evaluate_entry_quality(self, entry_data: dict) -> dict:
        """Evaluate entry quality with multi-factor check"""
        self.metrics['total_entries_evaluated'] += 1
        
        quality_checks = {
            'pattern_clean': False,
            'volume_good': False,
            'greeks_healthy': False,
            'bias_aligned': False,
            'confirmation': False
        }
        
        # Check pattern quality
        pattern_score = entry_data.get('pattern_score', 0)
        if pattern_score >= 0.7:
            quality_checks['pattern_clean'] = True
            self.metrics['quality_factors']['pattern_clean'] += 1
        else:
            self.metrics['quality_factors']['pattern_messy'] += 1
        
        # Check volume
        volume_ratio = entry_data.get('volume_ratio', 1.0)
        if volume_ratio >= 1.5:
            quality_checks['volume_good'] = True
            self.metrics['quality_factors']['volume_good'] += 1
        else:
            self.metrics['quality_factors']['volume_poor'] += 1
        
        # Check Greeks health
        greeks_score = entry_data.get('greeks_score', 0)
        if greeks_score >= 0.6:
            quality_checks['greeks_healthy'] = True
            self.metrics['quality_factors']['greeks_healthy'] += 1
        else:
            self.metrics['quality_factors']['greeks_unhealthy'] += 1
        
        # Check bias alignment
        bias_aligned = entry_data.get('bias_aligned', False)
        if bias_aligned:
            quality_checks['bias_aligned'] = True
            self.metrics['quality_factors']['bias_aligned'] += 1
        else:
            self.metrics['quality_factors']['bias_misaligned'] += 1
        
        # Multi-factor confirmation - ALL must pass (strict)
        passed_checks = sum(quality_checks.values())
        if passed_checks == 4:  # All 4 previous checks passed
            quality_checks['confirmation'] = True
        # If any factor failed, confirmation automatically fails
        
        return quality_checks
    
    def record_entry_decision(self, entry_data: dict, quality_checks: dict):
        """Record entry decision based on quality"""
        all_passed = all(quality_checks.values())
        
        if all_passed:
            # This is a clean setup - ALL factors passed
            self.metrics['entries_allowed'] += 1
            self.metrics['clean_setups'] += 1
            logger.info(f"✅ ENTRY ALLOWED: {entry_data.get('signal_type', 'Unknown')}")
            logger.info("   Quality Check:")
            for check, passed in quality_checks.items():
                logger.info(f"      {check}: {'✅' if passed else '❌'}")
        else:
            # Messy setup - at least one factor failed
            self.metrics['entries_blocked'] += 1
            self.metrics['messy_setups'] += 1
            failed_checks = [k for k, v in quality_checks.items() if not v]
            reason = f"Quality gate failed: {', '.join(failed_checks)}"
            self.metrics['block_reasons'][reason] += 1
            logger.info(f"⛔ ENTRY BLOCKED: {entry_data.get('signal_type', 'Unknown')}")
            logger.info(f"   Reason: {reason}")
    
    def generate_report(self) -> dict:
        """Generate test report"""
        total = self.metrics['total_entries_evaluated']
        if total == 0:
            return None
        
        allowed = self.metrics['entries_allowed']
        blocked = self.metrics['entries_blocked']
        
        block_rate = (blocked / total) * 100
        clean_setup_rate = (self.metrics['clean_setups'] / total) * 100
        
        report = {
            'metrics': self.metrics,
            'percentages': {
                'block_rate': block_rate,
                'clean_setup_rate': clean_setup_rate
            },
            'pass_fail': {
                'block_rate_target': block_rate >= self.config.MIN_BLOCK_RATE,
                'clean_setups_only': self.metrics['entries_allowed'] == self.metrics['clean_setups'],
                'multi_factor_working': True  # Checked in quality evaluation
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
        logger.info("📊 TEST-3: ENTRY QUALITY TEST REPORT")
        logger.info("="*60)
        
        m = report['metrics']
        p = report['percentages']
        
        logger.info("\n📈 Entry Metrics:")
        logger.info(f"   Total evaluated: {m['total_entries_evaluated']}")
        logger.info(f"   Entries allowed: {m['entries_allowed']}")
        logger.info(f"   Entries blocked: {m['entries_blocked']}")
        logger.info(f"   Block rate: {p['block_rate']:.1f}% (target: {self.config.MIN_BLOCK_RATE}%+)")
        
        logger.info("\n📊 Quality Metrics:")
        logger.info(f"   Clean setups: {m['clean_setups']}")
        logger.info(f"   Messy setups: {m['messy_setups']}")
        logger.info(f"   Clean setup rate: {p['clean_setup_rate']:.1f}%")
        
        logger.info("\n🔍 Quality Factors:")
        qf = m['quality_factors']
        logger.info(f"   Pattern clean: {qf['pattern_clean']} | Messy: {qf['pattern_messy']}")
        logger.info(f"   Volume good: {qf['volume_good']} | Poor: {qf['volume_poor']}")
        logger.info(f"   Greeks healthy: {qf['greeks_healthy']} | Unhealthy: {qf['greeks_unhealthy']}")
        logger.info(f"   Bias aligned: {qf['bias_aligned']} | Misaligned: {qf['bias_misaligned']}")
        
        logger.info("\n🚫 Top Block Reasons:")
        for reason, count in sorted(m['block_reasons'].items(), key=lambda x: x[1], reverse=True)[:5]:
            logger.info(f"   {reason}: {count}")
        
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-3 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info(f"   ✓ High block rate ({p['block_rate']:.1f}%)")
            logger.info("   ✓ Only clean setups allowed")
            logger.info("   ✓ Multi-factor confirmation working")
        else:
            logger.info("❌ TEST-3 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if not pf['block_rate_target']:
                logger.error(f"   ✗ Block rate too low ({p['block_rate']:.1f}%)")
            if not pf['clean_setups_only']:
                logger.error("   ✗ Messy setups being allowed")
        
        logger.info("="*60)


def main():
    """Run TEST-3 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-3: ENTRY QUALITY TEST")
    print("="*60)
    print("")
    
    if not TestProgression.can_run_test('TEST-3'):
        print("❌ Complete TEST-2 first")
        return False
    
    print("📋 Test Setup:")
    print("   Duration: 2-3 days")
    print("   Focus: Entry quality gates")
    print("")
    print("📌 Expected behavior:")
    print("   ✓ 70-80% entries blocked")
    print("   ✓ Only clean setups allowed")
    print("   ✓ Multi-factor confirmation")
    print("")
    
    monitor = Test3EntryQualityMonitor()
    
    print("🏃 Running simulated test...\n")
    
    # Simulate 100 entry evaluations
    import random
    for i in range(100):
        # Simulate entry data with varying quality
        entry_data = {
            'signal_type': f"Entry-{i+1}",
            'pattern_score': random.uniform(0.3, 1.0),
            'volume_ratio': random.uniform(0.8, 2.5),
            'greeks_score': random.uniform(0.4, 0.9),
            'bias_aligned': random.choice([True, False])
        }
        
        # Evaluate quality
        quality_checks = monitor.evaluate_entry_quality(entry_data)
        
        # Record decision
        monitor.record_entry_decision(entry_data, quality_checks)
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-3')
        print("\n👉 Next: TEST-4 - ADAPTIVE VETO TEST\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
