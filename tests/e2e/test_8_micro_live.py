"""
TEST-8: MICRO LIVE
Duration: 5-10 days

🚨 LIVE TRADING - Real money, smallest scale
⚠️ Only after ALL Golden Rules are YES

Max 1 trade/day
Smallest position size
"""
import sys
from pathlib import Path
from datetime import datetime, date

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test8Config, TestProgression, GoldenRules
from app.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test8MicroLiveMonitor:
    """
    Micro live monitoring
    
    ⚠️ CRITICAL: This is LIVE trading with real money
    
    PASS যদি:
    - Max 1 trade/day
    - Smallest qty
    - SL respected 100%
    - All rules followed
    
    FAIL যদি:
    - Multiple trades in day
    - Larger position
    - SL skipped even once
    """
    
    def __init__(self):
        self.config = Test8Config
        
        # Live trading state
        self.test_start_date = date.today()
        self.daily_trades = {}  # date -> trade count
        self.total_test_days = 0
        
        # Metrics
        self.metrics = {
            'total_days': 0,
            'total_trades': 0,
            'days_with_trade': 0,
            'days_no_trade': 0,
            
            'wins': 0,
            'losses': 0,
            'total_pnl': 0,
            
            'rule_violations': 0,  # MUST be ZERO
            'multiple_trades_days': 0,  # MUST be ZERO
            'oversized_positions': 0,  # MUST be ZERO
            'sl_skips': 0,  # MUST be ZERO
            
            'trades_log': []
        }
    
    def check_daily_limit(self, current_date: date) -> bool:
        """Check if daily trade limit reached"""
        if current_date not in self.daily_trades:
            self.daily_trades[current_date] = 0
        
        if self.daily_trades[current_date] >= self.config.MAX_TRADES_PER_DAY:
            logger.warning(f"⚠️ Daily limit reached ({self.config.MAX_TRADES_PER_DAY} trade)")
            return False
        
        return True
    
    def process_live_trade(self, trade_data: dict) -> dict:
        """Process live trade"""
        current_date = date.today()
        
        # Check daily limit
        if not self.check_daily_limit(current_date):
            logger.error("❌ Trade attempted after daily limit!")
            self.metrics['multiple_trades_days'] += 1
            self.metrics['rule_violations'] += 1
            return {'allowed': False, 'reason': 'daily_limit_exceeded'}
        
        # Check position size
        position_size = trade_data.get('position_size', 0)
        if position_size > self.config.POSITION_SIZE:
            logger.error(f"❌ Position size too large!")
            logger.error(f"   Size: {position_size} | Max: {self.config.POSITION_SIZE}")
            self.metrics['oversized_positions'] += 1
            self.metrics['rule_violations'] += 1
            return {'allowed': False, 'reason': 'position_too_large'}
        
        # Check SL
        has_sl = trade_data.get('has_sl', False)
        if not has_sl:
            logger.error("❌ CRITICAL: Trade without SL!")
            self.metrics['sl_skips'] += 1
            self.metrics['rule_violations'] += 1
            GoldenRules.SL_NEVER_SKIPPED = False
            return {'allowed': False, 'reason': 'no_sl'}
        
        # Trade allowed
        self.daily_trades[current_date] += 1
        self.metrics['total_trades'] += 1
        
        if self.daily_trades[current_date] == 1:
            self.metrics['days_with_trade'] += 1
        
        trade_record = {
            'date': current_date,
            'time': datetime.now(),
            'entry': trade_data.get('entry_price'),
            'sl': trade_data.get('sl_price'),
            'target': trade_data.get('target_price'),
            'size': position_size,
            'pnl': None  # To be updated on exit
        }
        
        self.metrics['trades_log'].append(trade_record)
        
        logger.info(f"✅ LIVE Trade {self.metrics['total_trades']}")
        logger.info(f"   Date: {current_date}")
        logger.info(f"   Entry: ₹{trade_record['entry']}")
        logger.info(f"   SL: ₹{trade_record['sl']}")
        logger.info(f"   Size: {position_size} lot")
        logger.info(f"   Daily count: {self.daily_trades[current_date]}/{self.config.MAX_TRADES_PER_DAY}")
        
        return {'allowed': True, 'trade_id': len(self.metrics['trades_log'])}
    
    def process_trade_exit(self, trade_id: int, exit_data: dict):
        """Process trade exit"""
        if trade_id > len(self.metrics['trades_log']):
            logger.error(f"Invalid trade ID: {trade_id}")
            return
        
        trade = self.metrics['trades_log'][trade_id - 1]
        exit_price = exit_data.get('exit_price')
        exit_reason = exit_data.get('reason')
        
        # Calculate PnL
        pnl = (exit_price - trade['entry']) * trade['size']
        trade['pnl'] = pnl
        
        self.metrics['total_pnl'] += pnl
        
        if pnl > 0:
            self.metrics['wins'] += 1
        else:
            self.metrics['losses'] += 1
        
        logger.info(f"📤 Trade Exit {trade_id}")
        logger.info(f"   Exit: ₹{exit_price}")
        logger.info(f"   Reason: {exit_reason}")
        logger.info(f"   PnL: ₹{pnl:+.0f}")
        logger.info(f"   Total PnL: ₹{self.metrics['total_pnl']:+.0f}")
        
        # Check if SL was respected
        if exit_reason == 'SL' and exit_price != trade['sl']:
            logger.warning(f"⚠️ SL slippage detected")
            logger.warning(f"   Expected: ₹{trade['sl']} | Actual: ₹{exit_price}")
    
    def update_test_progress(self):
        """Update test progress"""
        self.metrics['total_days'] = (date.today() - self.test_start_date).days + 1
        self.metrics['days_no_trade'] = self.metrics['total_days'] - self.metrics['days_with_trade']
    
    def generate_report(self) -> dict:
        """Generate test report"""
        self.update_test_progress()
        
        report = {
            'metrics': self.metrics,
            'pass_fail': {
                'min_test_days': self.metrics['total_days'] >= self.config.MIN_TEST_DAYS,
                'zero_violations': self.metrics['rule_violations'] == 0,
                'max_one_trade_daily': self.metrics['multiple_trades_days'] == 0,
                'correct_position_size': self.metrics['oversized_positions'] == 0,
                'sl_always_placed': self.metrics['sl_skips'] == 0,
                'positive_pnl': self.metrics['total_pnl'] > 0  # Not critical but good
            }
        }
        
        return report
    
    def evaluate_pass_fail(self, report: dict) -> bool:
        """Evaluate if test passed"""
        if not report:
            return False
        
        pf = report['pass_fail']
        
        # Critical checks
        critical_checks = [
            pf['zero_violations'],
            pf['max_one_trade_daily'],
            pf['correct_position_size'],
            pf['sl_always_placed']
        ]
        
        # Must have minimum test days
        if not pf['min_test_days']:
            logger.warning(f"Need {self.config.MIN_TEST_DAYS} days minimum")
            return False
        
        return all(critical_checks)
    
    def print_report(self, report: dict):
        """Print formatted report"""
        logger.info("")
        logger.info("="*60)
        logger.info("📊 TEST-8: MICRO LIVE TEST REPORT")
        logger.info("="*60)
        
        m = report['metrics']
        
        logger.info("\n📅 Test Duration:")
        logger.info(f"   Total days: {m['total_days']} (min: {self.config.MIN_TEST_DAYS})")
        logger.info(f"   Days with trade: {m['days_with_trade']}")
        logger.info(f"   Days no trade: {m['days_no_trade']}")
        
        logger.info("\n📈 Trading Metrics:")
        logger.info(f"   Total trades: {m['total_trades']}")
        logger.info(f"   Wins: {m['wins']}")
        logger.info(f"   Losses: {m['losses']}")
        logger.info(f"   Total PnL: ₹{m['total_pnl']:+.0f}")
        
        logger.info("\n⚠️ CRITICAL Violations (MUST BE ZERO):")
        logger.info(f"   Rule violations: {m['rule_violations']}")
        logger.info(f"   Multiple trades/day: {m['multiple_trades_days']}")
        logger.info(f"   Oversized positions: {m['oversized_positions']}")
        logger.info(f"   SL skips: {m['sl_skips']}")
        
        logger.info("\n📝 Trade Log:")
        for i, trade in enumerate(m['trades_log'], 1):
            pnl_str = f"₹{trade['pnl']:+.0f}" if trade['pnl'] is not None else "Open"
            logger.info(f"   {i}. {trade['date']} | Entry: ₹{trade['entry']} | PnL: {pnl_str}")
        
        logger.info("\n✅ Pass/Fail Criteria:")
        pf = report['pass_fail']
        for criteria, passed in pf.items():
            status = "✅ PASS" if passed else "❌ FAIL"
            logger.info(f"   {criteria}: {status}")
        
        logger.info("")
        logger.info("="*60)
        
        if self.evaluate_pass_fail(report):
            logger.info("✅ TEST-8 PASSED")
            logger.info("")
            logger.info("🎉 CONGRATULATIONS!")
            logger.info("")
            logger.info("You have successfully completed:")
            logger.info("   ✓ All 9 test levels")
            logger.info("   ✓ Golden Rules validated")
            logger.info("   ✓ Micro live trading")
            logger.info("   ✓ Proven system reliability")
            logger.info("")
            logger.info("📈 Next Steps:")
            logger.info("   1. Gradually scale up position size")
            logger.info("   2. Increase to 2-3 trades/day")
            logger.info("   3. Monitor performance closely")
            logger.info("   4. Stay boring and professional")
            logger.info("")
            logger.info("Remember: ধৈর্য + নিয়ম = লাভ")
        else:
            logger.info("❌ TEST-8 FAILED")
            logger.info("")
            logger.info("Issues found:")
            if m['rule_violations'] > 0:
                logger.error(f"   ✗ {m['rule_violations']} rule violations")
            if m['sl_skips'] > 0:
                logger.error(f"   ✗ SL skipped {m['sl_skips']} times - CRITICAL!")
            if not pf['min_test_days']:
                logger.warning(f"   ⚠️ Need more test days ({m['total_days']}/{self.config.MIN_TEST_DAYS})")
        
        logger.info("="*60)


def main():
    """Run TEST-8"""
    print("\n" + "="*60)
    print("🧪 TEST-8: MICRO LIVE")
    print("="*60)
    print("")
    
    # Check if can run
    if not TestProgression.can_run_test('TEST-8'):
        print("❌ Complete TEST-7 first")
        return False
    
    # CRITICAL: Check Golden Rules
    print("🏆 Checking Golden Rules...")
    print("")
    
    if not GoldenRules.all_passed():
        print("="*60)
        print("❌ GOLDEN RULES NOT SATISFIED")
        print("="*60)
        print("")
        print("Golden Rules Status:")
        print(f"   SL কখনো skip হয়নি? → {GoldenRules.SL_NEVER_SKIPPED}")
        print(f"   Loss এর পর bot চুপ ছিল? → {GoldenRules.CALM_AFTER_LOSS}")
        print(f"   Chop day-এ trade কম? → {GoldenRules.LOW_TRADES_ON_CHOP}")
        print(f"   তুমি mentally শান্ত? → {GoldenRules.MENTALLY_CALM}")
        print("")
        print("⛔ CANNOT proceed to live trading")
        print("⚠️ One NO = STOP")
        print("")
        print("Run: python3 scripts/validate_golden_rules.py")
        print("")
        return False
    
    print("✅ Golden Rules: ALL PASSED")
    print("")
    print("="*60)
    print("⚠️ WARNING: LIVE TRADING MODE")
    print("="*60)
    print("")
    print("This is REAL money trading.")
    print("Rules:")
    print("   - Max 1 trade per day")
    print("   - Position size: 1 lot only")
    print("   - SL MANDATORY")
    print("   - Minimum 5-10 days")
    print("")
    
    confirm = input("Type 'START LIVE' to begin: ")
    
    if confirm != 'START LIVE':
        print("\n❌ Cancelled")
        return False
    
    print("\n" + "="*60)
    print("🚀 MICRO LIVE TEST STARTED")
    print("="*60)
    print("")
    
    monitor = Test8MicroLiveMonitor()
    
    print("📋 Test running in live mode")
    print("   Monitor logs daily")
    print("   Check compliance")
    print("   Stay disciplined")
    print("")
    print("ℹ️ This is a simulation demo")
    print("")
    
    # In real implementation, this would connect to live trading
    # For now, show simulation
    print("🏃 Simulating 5-day test...\n")
    
    import random
    from datetime import timedelta
    
    for day in range(5):
        current_date = monitor.test_start_date + timedelta(days=day)
        print(f"\n--- Day {day+1}: {current_date} ---")
        
        # Simulate trade decision
        if random.random() < 0.7:  # 70% chance of trade
            trade_data = {
                'entry_price': random.randint(100, 150),
                'sl_price': random.randint(90, 95),
                'target_price': random.randint(155, 165),
                'position_size': 1,
                'has_sl': True
            }
            
            result = monitor.process_live_trade(trade_data)
            
            if result['allowed']:
                # Simulate exit
                exit_data = {
                    'exit_price': trade_data['entry_price'] + random.randint(-5, 10),
                    'reason': random.choice(['Target', 'SL', 'Time'])
                }
                monitor.process_trade_exit(result['trade_id'], exit_data)
        else:
            print("No trade today")
            monitor.metrics['days_no_trade'] += 1
    
    # Generate report
    print("\n" + "="*60)
    report = monitor.generate_report()
    monitor.print_report(report)
    
    passed = monitor.evaluate_pass_fail(report)
    
    if passed:
        TestProgression.mark_completed('TEST-8')
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
