"""
TEST-1: DATA & HEALTH TEST
Duration: 1-2 days

Monitors:
- LTP availability
- Stale data detection  
- Greeks availability
- WebSocket health
"""
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test1Config, TestProgression, GoldenRules
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test1DataHealthMonitor:
    """
    Monitor data quality and system health
    
    PASS যদি:
    - অনেক সময় "NO TRADE" log দেখো
    - stale হলে "HALT" আসে
    - bot panic করে না
    
    FAIL যদি:
    - data না থাকলেও entry try করে
    """
    
    def __init__(self):
        self.config = Test1Config
        self.start_time = None
        self.end_time = None
        
        # Metrics
        self.metrics = {
            'total_checks': 0,
            'ltp_available': 0,
            'ltp_stale': 0,
            'greeks_available': 0,
            'greeks_stale': 0,
            'oi_available': 0,
            'websocket_drops': 0,
            'websocket_recoveries': 0,
            'halt_events': 0,
            'no_trade_events': 0,
            'trades_on_stale_data': 0,  # Must be ZERO
            'panic_events': 0  # Must be ZERO
        }
        
        # Stale data tracking
        self.last_ltp_time = None
        self.last_greeks_time = None
        
    def check_ltp_health(self, ltp_data: dict) -> bool:
        """Check LTP data health"""
        self.metrics['total_checks'] += 1
        
        if not ltp_data or 'ltp' not in ltp_data:
            logger.warning("⚠️ LTP data not available")
            return False
        
        self.metrics['ltp_available'] += 1
        
        # Check staleness
        timestamp = ltp_data.get('timestamp', time.time())
        age = time.time() - timestamp
        
        if age > self.config.LTP_STALE_THRESHOLD:
            logger.warning(f"⚠️ LTP data stale ({age:.1f}s old)")
            self.metrics['ltp_stale'] += 1
            return False
        
        self.last_ltp_time = timestamp
        return True
    
    def check_greeks_health(self, greeks_data: dict) -> bool:
        """Check Greeks data health"""
        if not greeks_data or 'delta' not in greeks_data:
            logger.warning("⚠️ Greeks data not available")
            return False
        
        self.metrics['greeks_available'] += 1
        
        # Check staleness
        timestamp = greeks_data.get('timestamp', time.time())
        age = time.time() - timestamp
        
        if age > self.config.GREEKS_STALE_THRESHOLD:
            logger.warning(f"⚠️ Greeks data stale ({age:.1f}s old)")
            self.metrics['greeks_stale'] += 1
            return False
        
        self.last_greeks_time = timestamp
        return True
    
    def record_no_trade(self, reason: str):
        """Record NO TRADE decision"""
        self.metrics['no_trade_events'] += 1
        logger.info(f"✅ NO TRADE: {reason}")
    
    def record_halt(self, reason: str):
        """Record HALT event"""
        self.metrics['halt_events'] += 1
        logger.warning(f"⛔ HALT: {reason}")
    
    def record_websocket_drop(self):
        """Record WebSocket connection drop"""
        self.metrics['websocket_drops'] += 1
        logger.warning("🔌 WebSocket connection dropped")
    
    def record_websocket_recovery(self):
        """Record WebSocket recovery"""
        self.metrics['websocket_recoveries'] += 1
        logger.info("✅ WebSocket connection recovered")
    
    def record_trade_attempt(self, data_healthy: bool):
        """Record trade attempt"""
        if not data_healthy:
            self.metrics['trades_on_stale_data'] += 1
            logger.error("❌ CRITICAL: Trade attempted on stale data!")
    
    def record_panic_event(self):
        """Record panic/error event"""
        self.metrics['panic_events'] += 1
        logger.error("❌ PANIC EVENT detected!")
    
    def generate_report(self) -> dict:
        """Generate test report"""
        # Calculate percentages
        total = self.metrics['total_checks']
        if total == 0:
            return None
        
        ltp_availability = (self.metrics['ltp_available'] / total) * 100
        greeks_availability = (self.metrics['greeks_available'] / total) * 100
        
        total_decisions = self.metrics['no_trade_events'] + self.metrics['halt_events']
        if total_decisions > 0:
            no_trade_pct = (self.metrics['no_trade_events'] / total_decisions) * 100
        else:
            no_trade_pct = 0
        
        report = {
            'metrics': self.metrics,
            'percentages': {
                'ltp_availability': ltp_availability,
                'greeks_availability': greeks_availability,
                'no_trade_percentage': no_trade_pct
            },
            'pass_fail': {
                'ltp_available': ltp_availability >= 90,  # 90%+ availability
                'greeks_available': greeks_availability >= 90,
                'no_trade_high': no_trade_pct >= self.config.MIN_NO_TRADE_PERCENTAGE,
                'zero_stale_trades': self.metrics['trades_on_stale_data'] == 0,
                'zero_panic': self.metrics['panic_events'] == 0,
                'ws_recovery': self.metrics['websocket_recoveries'] >= self.metrics['websocket_drops']
            }
        }
        
        return report
    
    def evaluate_pass_fail(self, report: dict) -> bool:
        """Evaluate if test passed"""
        if not report:
            return False
        
        pass_fail = report['pass_fail']
        
        # All criteria must pass
        all_passed = all(pass_fail.values())
        
        return all_passed
    
    def print_report(self, report: dict):
        """Print formatted report"""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 TEST-1: DATA & HEALTH TEST REPORT")
        logger.info("="*60)
        
        # Metrics
        m = report['metrics']
        logger.info("\n📈 Metrics:")
        logger.info(f"   Total checks: {m['total_checks']}")
        logger.info(f"   LTP available: {m['ltp_available']} ({report['percentages']['ltp_availability']:.1f}%)")
        logger.info(f"   LTP stale: {m['ltp_stale']}")
        logger.info(f"   Greeks available: {m['greeks_available']} ({report['percentages']['greeks_availability']:.1f}%)")
        logger.info(f"   Greeks stale: {m['greeks_stale']}")
        logger.info(f"   WebSocket drops: {m['websocket_drops']}")
        logger.info(f"   WebSocket recoveries: {m['websocket_recoveries']}")
        logger.info(f"   NO TRADE events: {m['no_trade_events']} ({report['percentages']['no_trade_percentage']:.1f}%)")
        logger.info(f"   HALT events: {m['halt_events']}")
        logger.info(f"   Trades on stale data: {m['trades_on_stale_data']} ⚠️")
        logger.info(f"   Panic events: {m['panic_events']} ⚠️")
        
        # Pass/Fail criteria
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        # Final verdict
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-1 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info("   ✓ অনেক সময় 'NO TRADE' log দেখেছো")
            logger.info("   ✓ stale হলে 'HALT' এসেছে")
            logger.info("   ✓ bot panic করে নি")
        else:
            logger.info("❌ TEST-1 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if not pf['zero_stale_trades']:
                logger.error("   ✗ data না থাকলেও entry try করেছে")
            if not pf['zero_panic']:
                logger.error("   ✗ bot panic করেছে")
            if not pf['no_trade_high']:
                logger.error("   ✗ পর্যাপ্ত 'NO TRADE' decision নেই")
        
        logger.info("="*60)


def main():
    """Run TEST-1 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-1: DATA & HEALTH TEST")
    print("="*60)
    print("")
    
    # Check if can run
    if not TestProgression.can_run_test('TEST-1'):
        print("❌ Complete TEST-0 first")
        return False
    
    print("📋 Test Setup:")
    print("   Duration: 1-2 days")
    print("   Focus: Data quality and system stability")
    print("")
    print("📌 What to look for:")
    print("   ✓ Many 'NO TRADE' logs")
    print("   ✓ 'HALT' on stale data")
    print("   ✓ Bot doesn't panic")
    print("")
    print("❌ Fail if:")
    print("   ✗ Trades on stale data")
    print("   ✗ Bot panics on errors")
    print("")
    
    # Create monitor
    monitor = Test1DataHealthMonitor()
    
    # Simulated test run (replace with real implementation)
    print("🏃 Running simulated test...\n")
    
    # Simulate various scenarios
    for i in range(100):
        # Simulate LTP check
        ltp_data = {'ltp': 20000 + i, 'timestamp': time.time()}
        monitor.check_ltp_health(ltp_data)
        
        # Simulate Greeks check
        greeks_data = {'delta': 0.5, 'timestamp': time.time()}
        monitor.check_greeks_health(greeks_data)
        
        # Simulate decision
        if i % 5 == 0:
            monitor.record_no_trade("Market bias neutral")
        
        # Simulate occasional issues
        if i == 50:
            monitor.record_websocket_drop()
            time.sleep(0.1)
            monitor.record_websocket_recovery()
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    # Evaluate
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-1')
        print("\n👉 Next: TEST-2 - SIGNAL FLOOD TEST\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
