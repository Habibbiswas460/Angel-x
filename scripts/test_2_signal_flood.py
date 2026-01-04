"""
TEST-2: SIGNAL FLOOD TEST
একটা choppy/sideways দিনে চালাও

⚠️ TRAP: Signal তো আসবেই। কিন্তু trade করা উচিত না।

PASS যদি:
- 100 signal আসলো, 10-15 টা trade করলো
- Neutral bias সময় long → block
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test2Config, TestProgression
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test2SignalFloodMonitor:
    """
    Monitor signal flood behavior
    
    বেশি trade = ভালো না
    
    PASS যদি:
    - signal আসে কিন্তু trade কম
    - neutral bias এ block করে
    
    FAIL যদি:
    - সব signal এ entry করে
    - bias ignore করে
    """
    
    def __init__(self):
        self.config = Test2Config
        
        # Metrics
        self.metrics = {
            'total_signals': 0,
            'bias_bullish_signals': 0,
            'bias_bearish_signals': 0,
            'bias_neutral_signals': 0,
            
            'total_trades': 0,
            'blocked_by_bias': 0,
            'blocked_by_quality': 0,
            'blocked_by_other': 0,
            
            'trades_during_neutral': 0,  # Should be minimal
            'trades_during_chop': 0,     # Should be minimal
            
            'chop_detected_count': 0,
            'neutral_bias_time': 0,
            
            'signal_types': defaultdict(int),
            'block_reasons': defaultdict(int)
        }
        
        # State tracking
        self.current_bias = 'NEUTRAL'
        self.is_choppy = False
        
    def record_signal(self, signal_type: str, bias: str):
        """Record signal generation"""
        self.metrics['total_signals'] += 1
        self.metrics['signal_types'][signal_type] += 1
        
        # Track bias
        if bias == 'BULLISH':
            self.metrics['bias_bullish_signals'] += 1
        elif bias == 'BEARISH':
            self.metrics['bias_bearish_signals'] += 1
        else:
            self.metrics['bias_neutral_signals'] += 1
        
        logger.info(f"📊 Signal: {signal_type} | Bias: {bias}")
    
    def record_trade(self, signal_type: str, bias: str):
        """Record trade execution"""
        self.metrics['total_trades'] += 1
        
        # Track trades during bad conditions
        if bias == 'NEUTRAL':
            self.metrics['trades_during_neutral'] += 1
            logger.warning(f"⚠️ Trade during NEUTRAL bias: {signal_type}")
        
        if self.is_choppy:
            self.metrics['trades_during_chop'] += 1
            logger.warning(f"⚠️ Trade during CHOPPY market: {signal_type}")
        
        logger.info(f"✅ Trade executed: {signal_type}")
    
    def record_block(self, signal_type: str, reason: str):
        """Record blocked signal"""
        self.metrics['block_reasons'][reason] += 1
        
        if 'bias' in reason.lower():
            self.metrics['blocked_by_bias'] += 1
        elif 'quality' in reason.lower():
            self.metrics['blocked_by_quality'] += 1
        else:
            self.metrics['blocked_by_other'] += 1
        
        logger.info(f"⛔ Blocked: {signal_type} | Reason: {reason}")
    
    def update_market_state(self, bias: str, is_choppy: bool):
        """Update market state"""
        self.current_bias = bias
        self.is_choppy = is_choppy
        
        if bias == 'NEUTRAL':
            self.metrics['neutral_bias_time'] += 1
        
        if is_choppy:
            self.metrics['chop_detected_count'] += 1
    
    def generate_report(self) -> dict:
        """Generate test report"""
        total_signals = self.metrics['total_signals']
        total_trades = self.metrics['total_trades']
        
        if total_signals == 0:
            return None
        
        # Calculate ratios
        signal_to_trade_ratio = (total_trades / total_signals) if total_signals > 0 else 0
        block_rate = ((total_signals - total_trades) / total_signals) * 100
        
        # Calculate neutral bias percentage
        neutral_pct = (self.metrics['bias_neutral_signals'] / total_signals) * 100
        
        report = {
            'metrics': self.metrics,
            'ratios': {
                'signal_to_trade_ratio': signal_to_trade_ratio,
                'block_rate': block_rate,
                'neutral_bias_percentage': neutral_pct
            },
            'pass_fail': {
                'low_signal_to_trade': signal_to_trade_ratio <= self.config.MAX_TRADE_TO_SIGNAL_RATIO,
                'blocks_on_neutral': self.metrics['trades_during_neutral'] <= 2,
                'blocks_on_chop': self.metrics['trades_during_chop'] <= self.config.MAX_TRADES_ON_CHOP_DAY,
                'high_block_rate': block_rate >= 70  # At least 70% blocked
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
        logger.info("📊 TEST-2: SIGNAL FLOOD TEST REPORT")
        logger.info("="*60)
        
        # Metrics
        m = report['metrics']
        r = report['ratios']
        
        logger.info("\n📈 Signal Metrics:")
        logger.info(f"   Total signals: {m['total_signals']}")
        logger.info(f"   Bullish signals: {m['bias_bullish_signals']}")
        logger.info(f"   Bearish signals: {m['bias_bearish_signals']}")
        logger.info(f"   Neutral signals: {m['bias_neutral_signals']} ({r['neutral_bias_percentage']:.1f}%)")
        
        logger.info("\n📈 Trade Metrics:")
        logger.info(f"   Total trades: {m['total_trades']}")
        logger.info(f"   Signal→Trade ratio: {r['signal_to_trade_ratio']:.2f} ({r['signal_to_trade_ratio']*100:.1f}%)")
        logger.info(f"   Block rate: {r['block_rate']:.1f}%")
        
        logger.info("\n⚠️ Warning Metrics:")
        logger.info(f"   Trades during neutral: {m['trades_during_neutral']}")
        logger.info(f"   Trades during chop: {m['trades_during_chop']}")
        
        logger.info("\n🚫 Block Reasons:")
        for reason, count in m['block_reasons'].items():
            logger.info(f"   {reason}: {count}")
        
        # Pass/Fail
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        # Final verdict
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-2 PASSED")
            logger.info("")
            logger.info("Expected behavior observed:")
            logger.info(f"   ✓ Signal flood controlled ({r['signal_to_trade_ratio']:.1%} conversion)")
            logger.info(f"   ✓ High block rate ({r['block_rate']:.1f}%)")
            logger.info("   ✓ Bias awareness working")
            logger.info("")
            logger.info("📌 Remember: বেশি trade = ভালো না")
        else:
            logger.info("❌ TEST-2 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if not pf['low_signal_to_trade']:
                logger.error(f"   ✗ Too many trades ({r['signal_to_trade_ratio']:.1%})")
            if not pf['blocks_on_neutral']:
                logger.error(f"   ✗ Trading during neutral bias ({m['trades_during_neutral']} trades)")
            if not pf['blocks_on_chop']:
                logger.error(f"   ✗ Trading during choppy market ({m['trades_during_chop']} trades)")
        
        logger.info("="*60)


def main():
    """Run TEST-2 simulation"""
    print("\n" + "="*60)
    print("🧪 TEST-2: SIGNAL FLOOD TEST")
    print("="*60)
    print("")
    
    # Check if can run
    if not TestProgression.can_run_test('TEST-2'):
        print("❌ Complete TEST-1 first")
        return False
    
    print("📋 Test Setup:")
    print("   Run on: Choppy/Sideways day")
    print("   Focus: Signal filtering and bias awareness")
    print("")
    print("📌 Expected behavior:")
    print("   ✓ 100 signals → 10-15 trades")
    print("   ✓ Neutral bias → block")
    print("   ✓ Choppy market → minimal trades")
    print("")
    print("❌ Fail if:")
    print("   ✗ All signals → trades")
    print("   ✗ Bias ignored")
    print("")
    
    # Create monitor
    monitor = Test2SignalFloodMonitor()
    
    # Simulated choppy day
    print("🏃 Simulating choppy day...\n")
    
    # Simulate 100 signals with mostly neutral bias
    biases = ['NEUTRAL'] * 70 + ['BULLISH'] * 15 + ['BEARISH'] * 15
    
    for i, bias in enumerate(biases):
        signal_type = f"Signal-{i+1}"
        
        # Update market state
        is_choppy = i % 3 == 0  # Intermittent chop
        monitor.update_market_state(bias, is_choppy)
        
        # Record signal
        monitor.record_signal(signal_type, bias)
        
        # Simulate decision
        if bias == 'NEUTRAL':
            # Should mostly block
            if i % 10 == 0:  # Only 10% trade
                monitor.record_trade(signal_type, bias)
            else:
                monitor.record_block(signal_type, "Bias neutral")
        
        elif is_choppy:
            # Should block on chop
            monitor.record_block(signal_type, "Market choppy")
        
        else:
            # Normal processing
            if i % 4 == 0:  # 25% trade rate on clean signals
                monitor.record_trade(signal_type, bias)
            else:
                monitor.record_block(signal_type, "Quality gate failed")
    
    # Generate report
    report = monitor.generate_report()
    monitor.print_report(report)
    
    # Evaluate
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-2')
        print("\n👉 Next: TEST-3 - ENTRY QUALITY TEST\n")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
