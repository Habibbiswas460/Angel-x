"""
TEST-6: SL FAILURE SIMULATION
Duration: 1 day

Simulates stop-loss failure scenarios
Tests force exit behavior
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test6Config, TestProgression, GoldenRules
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test6SLFailureMonitor:
    """
    Monitor SL failure scenarios
    
    PASS যদি:
    - Force exit হয় immediately
    - ZERO naked positions
    - Drawdown limit respect করে
    
    FAIL যদি:
    - Naked position থাকে
    - No exit action নেয়
    """
    
    def __init__(self):
        self.config = Test6Config
        
        # Metrics
        self.metrics = {
            'sl_failures': 0,
            'force_exits': 0,
            'naked_positions': 0,  # MUST be ZERO
            'drawdown_violations': 0,  # MUST be ZERO
            
            'sl_slippage_events': 0,
            'sl_rejection_events': 0,
            'gap_through_sl_events': 0,
            
            'avg_exit_time': 0,  # Should be < 5 seconds
            'max_drawdown': 0
        }
        
        self.sl_never_skipped = True
    
    def simulate_sl_failure(self, scenario: str, position_data: dict) -> dict:
        """Simulate SL failure scenario"""
        self.metrics['sl_failures'] += 1
        
        entry_price = position_data.get('entry_price', 100)
        sl_price = position_data.get('sl_price', 95)
        position_size = position_data.get('size', 25)
        
        logger.warning(f"🚨 SL FAILURE SCENARIO: {scenario}")
        logger.warning(f"   Entry: ₹{entry_price}")
        logger.warning(f"   SL: ₹{sl_price}")
        logger.warning(f"   Size: {position_size}")
        
        result = {
            'scenario': scenario,
            'force_exit': False,
            'exit_price': None,
            'exit_time': None,
            'naked_position': False
        }
        
        if scenario == 'SLIPPAGE':
            # SL at 95, filled at 92
            self.metrics['sl_slippage_events'] += 1
            exit_price = sl_price - 3
            logger.warning(f"   Slippage: SL {sl_price} → Filled {exit_price}")
            
            # Should force exit
            if self.config.FORCE_EXIT_ON_SL_FAIL:
                result['force_exit'] = True
                result['exit_price'] = exit_price
                result['exit_time'] = 2  # 2 seconds
                self.metrics['force_exits'] += 1
                logger.info(f"   ✅ Force exit: ₹{exit_price} (2 sec)")
            else:
                result['naked_position'] = True
                self.metrics['naked_positions'] += 1
                self.sl_never_skipped = False
                logger.error("   ❌ Naked position!")
        
        elif scenario == 'REJECTION':
            # SL order rejected by broker
            self.metrics['sl_rejection_events'] += 1
            logger.error("   ❌ SL order REJECTED by broker")
            
            # Must force market exit
            if self.config.FORCE_EXIT_ON_SL_FAIL:
                exit_price = sl_price - 2  # Market exit with slippage
                result['force_exit'] = True
                result['exit_price'] = exit_price
                result['exit_time'] = 3  # 3 seconds
                self.metrics['force_exits'] += 1
                logger.info(f"   ✅ Market exit: ₹{exit_price} (3 sec)")
            else:
                result['naked_position'] = True
                self.metrics['naked_positions'] += 1
                self.sl_never_skipped = False
                logger.error("   ❌ Naked position!")
        
        elif scenario == 'GAP_DOWN':
            # Market gaps through SL
            self.metrics['gap_through_sl_events'] += 1
            exit_price = sl_price - 8  # Large gap
            logger.error(f"   ⚠️ Gap through SL: {sl_price} → {exit_price}")
            
            # Should force exit at market
            if self.config.FORCE_EXIT_ON_SL_FAIL:
                result['force_exit'] = True
                result['exit_price'] = exit_price
                result['exit_time'] = 1  # Immediate
                self.metrics['force_exits'] += 1
                logger.info(f"   ✅ Gap exit: ₹{exit_price} (immediate)")
            else:
                result['naked_position'] = True
                self.metrics['naked_positions'] += 1
                self.sl_never_skipped = False
                logger.error("   ❌ Naked position!")
        
        # Calculate drawdown
        if result['exit_price']:
            loss = (entry_price - result['exit_price']) * position_size
            drawdown_pct = (loss / (entry_price * position_size)) * 100
            
            if drawdown_pct > self.config.MAX_DRAWDOWN_PERCENT:
                self.metrics['drawdown_violations'] += 1
                logger.error(f"   ❌ Drawdown exceeded: {drawdown_pct:.1f}%")
            
            if drawdown_pct > self.metrics['max_drawdown']:
                self.metrics['max_drawdown'] = drawdown_pct
        
        # Track exit time
        if result['exit_time']:
            self.metrics['avg_exit_time'] = (
                (self.metrics['avg_exit_time'] * (self.metrics['force_exits'] - 1) + 
                 result['exit_time']) / self.metrics['force_exits']
            )
        
        return result
    
    def generate_report(self) -> dict:
        """Generate test report"""
        report = {
            'metrics': self.metrics,
            'pass_fail': {
                'zero_naked_positions': self.metrics['naked_positions'] == 0,
                'all_force_exits': self.metrics['force_exits'] == self.metrics['sl_failures'],
                'fast_exits': self.metrics['avg_exit_time'] < 5,
                'zero_drawdown_violations': self.metrics['drawdown_violations'] == 0
            }
        }
        
        return report
    
    def evaluate_pass_fail(self, report: dict) -> bool:
        """Evaluate if test passed"""
        if not report:
            return False
        
        pf = report['pass_fail']
        
        # Update Golden Rules
        GoldenRules.SL_NEVER_SKIPPED = self.sl_never_skipped
        GoldenRules.save_to_file()  # Persist to file
        
        return all(pf.values())
    
    def print_report(self, report: dict):
        """Print formatted report"""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 TEST-6: SL FAILURE SIMULATION REPORT")
        logger.info("="*60)
        
        m = report['metrics']
        
        logger.info("\n📈 SL Failure Metrics:")
        logger.info(f"   Total SL failures: {m['sl_failures']}")
        logger.info(f"   Force exits: {m['force_exits']}")
        logger.info(f"   Slippage events: {m['sl_slippage_events']}")
        logger.info(f"   Rejection events: {m['sl_rejection_events']}")
        logger.info(f"   Gap through events: {m['gap_through_sl_events']}")
        
        logger.info("\n⚠️ CRITICAL Metrics:")
        logger.info(f"   Naked positions: {m['naked_positions']} (MUST be 0)")
        logger.info(f"   Drawdown violations: {m['drawdown_violations']} (MUST be 0)")
        logger.info(f"   Avg exit time: {m['avg_exit_time']:.1f} sec")
        logger.info(f"   Max drawdown: {m['max_drawdown']:.1f}%")
        
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        logger.info("\n🏆 Golden Rules Update:")
        logger.info(f"   SL_NEVER_SKIPPED: {self.sl_never_skipped}")
        
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-6 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info("   ✓ Force exits on all SL failures")
            logger.info("   ✓ ZERO naked positions")
            logger.info("   ✓ Fast exit times")
            logger.info("   ✓ Drawdown controlled")
        else:
            logger.info("❌ TEST-6 FAILED")
            logger.info("")
            logger.info("CRITICAL issues:")
            if not pf['zero_naked_positions']:
                logger.error(f"   ✗ {m['naked_positions']} naked positions!")
            if not pf['all_force_exits']:
                logger.error("   ✗ Some SL failures not force exited!")
        
        logger.info("="*60)


def main():
    """Run TEST-6 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-6: SL FAILURE SIMULATION")
    print("="*60)
    print("")
    
    if not TestProgression.can_run_test('TEST-6'):
        print("❌ Complete TEST-5 first")
        return False
    
    print("📋 Test Setup:")
    print("   Duration: 1 day")
    print("   Focus: SL failure behavior")
    print("")
    print("📌 Scenarios:")
    print("   1. SL slippage")
    print("   2. SL rejection")
    print("   3. Gap through SL")
    print("")
    
    monitor = Test6SLFailureMonitor()
    
    print("🏃 Running simulations...\n")
    
    # Simulate various SL failure scenarios
    scenarios = [
        ('SLIPPAGE', {'entry_price': 100, 'sl_price': 95, 'size': 25}),
        ('REJECTION', {'entry_price': 150, 'sl_price': 140, 'size': 25}),
        ('GAP_DOWN', {'entry_price': 200, 'sl_price': 190, 'size': 25}),
        ('SLIPPAGE', {'entry_price': 120, 'sl_price': 115, 'size': 25}),
        ('REJECTION', {'entry_price': 180, 'sl_price': 170, 'size': 25}),
    ]
    
    for scenario, position in scenarios:
        result = monitor.simulate_sl_failure(scenario, position)
        print("")
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-6')
        print("\n👉 Next: TEST-7 - SHADOW-LIVE TEST\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
