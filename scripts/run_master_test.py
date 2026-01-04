"""
MASTER TEST RUNNER
Orchestrates all test levels

Usage:
    python run_master_test.py --test TEST-0
    python run_master_test.py --test TEST-1
    python run_master_test.py --auto  # Run all in sequence
"""
import sys
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import TestProgression, GoldenRules
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class MasterTestRunner:
    """
    Master test orchestrator
    
    Ensures:
    - Tests run in order
    - No level skipping
    - Golden Rules validated
    """
    
    def __init__(self):
        self.tests = {
            'TEST-0': self.run_test_0,
            'TEST-1': self.run_test_1,
            'TEST-2': self.run_test_2,
            'TEST-3': self.run_test_3,
            'TEST-4': self.run_test_4,
            'TEST-5': self.run_test_5,
            'TEST-6': self.run_test_6,
            'TEST-7': self.run_test_7,
            'TEST-8': self.run_test_8,
        }
    
    def print_header(self):
        """Print test suite header"""
        print("\n" + "="*80)
        print(" " * 20 + "🔥 ANGEL-X MASTER TEST PLAN 🔥")
        print("="*80)
        print("\n📋 Test Philosophy:")
        print("   - boring system = professional system")
        print("   - বেশি trade = ভালো না")
        print("   - calm day = successful day")
        print("   - ধৈর্য + নিয়ম = লাভ")
        print("\n⚠️ Rules:")
        print("   1. Cannot skip test levels")
        print("   2. Each level must PASS before next")
        print("   3. Golden Rules must all be YES before TEST-8")
        print("   4. One NO in Golden Rules → STOP immediately")
        print("")
    
    def run_test_0(self) -> bool:
        """Run TEST-0: Safety Setup"""
        from test_0_safety_setup import main
        return main()
    
    def run_test_1(self) -> bool:
        """Run TEST-1: Data Health"""
        from test_1_data_health import main
        return main()
    
    def run_test_2(self) -> bool:
        """Run TEST-2: Signal Flood"""
        from test_2_signal_flood import main
        return main()
    
    def run_test_3(self) -> bool:
        """Run TEST-3: Entry Quality"""
        from test_3_entry_quality import main
        return main()
    
    def run_test_4(self) -> bool:
        """Run TEST-4: Adaptive Veto"""
        from test_4_adaptive_veto import main
        return main()
    
    def run_test_5(self) -> bool:
        """Run TEST-5: Risk Manager"""
        from test_5_risk_manager import main
        return main()
    
    def run_test_6(self) -> bool:
        """Run TEST-6: SL Failure"""
        from test_6_sl_failure import main
        return main()
    
    def run_test_7(self) -> bool:
        """Run TEST-7: Shadow-Live"""
        from test_7_shadow_live import main
        return main()
    
    def run_test_8(self) -> bool:
        """Run TEST-8: Micro Live"""
        from test_8_micro_live import main
        return main()
    
    def run_single_test(self, test_name: str) -> bool:
        """Run a single test"""
        # Validate test name
        if test_name not in self.tests:
            logger.error(f"❌ Invalid test: {test_name}")
            logger.error(f"   Valid tests: {', '.join(self.tests.keys())}")
            return False
        
        # Check if can run
        if not TestProgression.can_run_test(test_name):
            logger.error(f"❌ Cannot run {test_name}")
            logger.error("   Reason: Previous tests not completed")
            logger.error("")
            logger.error(TestProgression.get_progress_report())
            return False
        
        # Run test
        logger.info(f"\n🏃 Running {test_name}...\n")
        
        try:
            test_func = self.tests[test_name]
            passed = test_func()
            
            if passed:
                logger.info(f"\n✅ {test_name} PASSED\n")
            else:
                logger.error(f"\n❌ {test_name} FAILED\n")
            
            return passed
        
        except Exception as e:
            logger.error(f"\n❌ {test_name} CRASHED: {e}\n")
            import traceback
            traceback.print_exc()
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests in sequence"""
        self.print_header()
        
        logger.info("🏃 Running all tests in sequence...\n")
        
        for test_name in TestProgression.test_order:
            logger.info(f"\n{'='*80}")
            logger.info(f"Starting {test_name}")
            logger.info(f"{'='*80}\n")
            
            passed = self.run_single_test(test_name)
            
            if not passed:
                logger.error(f"\n❌ Stopped at {test_name}")
                logger.error("   Fix issues before continuing\n")
                return False
            
            # Wait for user confirmation before next test
            if test_name != 'TEST-8':
                logger.info("\n" + "="*80)
                input(f"Press Enter to continue to next test...")
                logger.info("")
        
        logger.info("\n" + "="*80)
        logger.info("✅ ALL TESTS PASSED!")
        logger.info("="*80)
        logger.info("\n🎉 Congratulations! System ready for production.\n")
        
        return True
    
    def show_progress(self):
        """Show current test progress"""
        self.print_header()
        print(TestProgression.get_progress_report())
        print("")
        
        # Show Golden Rules
        print("="*80)
        print("🏆 GOLDEN RULES STATUS")
        print("="*80)
        print(f"   SL কখনো skip হয়নি? → {GoldenRules.SL_NEVER_SKIPPED or 'Not checked'}")
        print(f"   Loss এর পর bot চুপ ছিল? → {GoldenRules.CALM_AFTER_LOSS or 'Not checked'}")
        print(f"   Chop day-এ trade কম? → {GoldenRules.LOW_TRADES_ON_CHOP or 'Not checked'}")
        print(f"   তুমি mentally শান্ত? → {GoldenRules.MENTALLY_CALM or 'Not checked'}")
        print("")
        
        if GoldenRules.all_passed():
            print("✅ All Golden Rules satisfied - Ready for TEST-8")
        else:
            print("⚠️ Complete all tests and validate Golden Rules before TEST-8")
        
        print("="*80)
        print("")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Angel-X Master Test Runner')
    parser.add_argument('--test', type=str, help='Specific test to run (TEST-0 to TEST-8)')
    parser.add_argument('--auto', action='store_true', help='Run all tests in sequence')
    parser.add_argument('--progress', action='store_true', help='Show test progress')
    
    args = parser.parse_args()
    
    runner = MasterTestRunner()
    
    if args.progress:
        runner.show_progress()
        return True
    
    elif args.auto:
        return runner.run_all_tests()
    
    elif args.test:
        return runner.run_single_test(args.test)
    
    else:
        # Show usage
        runner.print_header()
        print("Usage:")
        print("   python run_master_test.py --progress           # Show progress")
        print("   python run_master_test.py --test TEST-0        # Run specific test")
        print("   python run_master_test.py --auto               # Run all tests")
        print("")
        print("Available tests:")
        for test_name in TestProgression.test_order:
            status = "✅" if test_name in TestProgression.completed_tests else "⏳"
            print(f"   {status} {test_name}")
        print("")
        
        return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
