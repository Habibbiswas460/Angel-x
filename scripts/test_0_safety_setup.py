"""
TEST-0: PRE-TEST SAFETY SETUP
Mandatory before any other test

Bot চিন্তা করবে, সিদ্ধান্ত নেবে, কিন্তু order যাবে না
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import Test0Config, TestProgression
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class Test0PreTestSafetySetup:
    """
    ⚠️ CRITICAL: Safety gates before any testing
    """
    
    def __init__(self):
        self.config = Test0Config
        self.passed = False
        
    def validate_configuration(self) -> bool:
        """Validate all safety settings"""
        logger.info("="*60)
        logger.info("🟥 TEST-0: PRE-TEST SAFETY SETUP")
        logger.info("="*60)
        
        checks = []
        
        # Check 1: DEMO_MODE must be True
        demo_mode = self.config.DEMO_MODE
        logger.info(f"1. DEMO_MODE = {demo_mode}")
        if demo_mode:
            logger.info("   ✅ PASS: Bot will think but not execute")
            checks.append(True)
        else:
            logger.error("   ❌ FAIL: DEMO_MODE must be True for testing")
            checks.append(False)
        
        # Check 2: REAL_MARKET_DATA must be True
        real_data = self.config.REAL_MARKET_DATA
        logger.info(f"2. REAL_MARKET_DATA = {real_data}")
        if real_data:
            logger.info("   ✅ PASS: Using real market data")
            checks.append(True)
        else:
            logger.warning("   ⚠️ WARN: Should use real market data for accurate testing")
            checks.append(True)  # Not critical
        
        # Check 3: ORDER_PLACEMENT must be False
        order_placement = self.config.ORDER_PLACEMENT
        logger.info(f"3. ORDER_PLACEMENT = {order_placement}")
        if not order_placement:
            logger.info("   ✅ PASS: Orders will NOT go to broker")
            checks.append(True)
        else:
            logger.error("   ❌ CRITICAL FAIL: ORDER_PLACEMENT must be False")
            checks.append(False)
        
        # Check 4: Logging enabled
        log_decisions = self.config.LOG_ALL_DECISIONS
        logger.info(f"4. LOG_ALL_DECISIONS = {log_decisions}")
        if log_decisions:
            logger.info("   ✅ PASS: All decisions will be logged")
            checks.append(True)
        else:
            logger.warning("   ⚠️ WARN: Should enable decision logging")
            checks.append(True)
        
        # Check 5: Health check required
        health_check = self.config.REQUIRE_HEALTH_CHECK
        logger.info(f"5. REQUIRE_HEALTH_CHECK = {health_check}")
        if health_check:
            logger.info("   ✅ PASS: Data health check mandatory")
            checks.append(True)
        else:
            logger.warning("   ⚠️ WARN: Health check should be required")
            checks.append(True)
        
        # Check 6: Stale data blocking
        block_stale = self.config.BLOCK_IF_STALE_DATA
        logger.info(f"6. BLOCK_IF_STALE_DATA = {block_stale}")
        if block_stale:
            logger.info("   ✅ PASS: Will block trades on stale data")
            checks.append(True)
        else:
            logger.error("   ❌ FAIL: Must block on stale data")
            checks.append(False)
        
        # Final verdict
        logger.info("")
        logger.info("="*60)
        
        all_passed = all(checks)
        
        if all_passed:
            logger.info("✅ TEST-0 PASSED: Safe to proceed to TEST-1")
            logger.info("")
            logger.info("📌 Summary:")
            logger.info("   - Bot will analyze market")
            logger.info("   - Bot will make decisions")
            logger.info("   - Bot will log everything")
            logger.info("   - Bot will NOT place any orders")
            logger.info("")
            logger.info("⚠️ যদি এটা skip করো → সব test invalid ❌")
            self.passed = True
        else:
            logger.error("❌ TEST-0 FAILED: Fix configuration before proceeding")
            logger.error("   CANNOT proceed to other tests")
            self.passed = False
        
        logger.info("="*60)
        
        return all_passed
    
    def run(self) -> bool:
        """Run TEST-0"""
        passed = self.validate_configuration()
        
        if passed:
            # Mark as completed
            TestProgression.mark_completed('TEST-0')
            
            # Show next steps
            logger.info("")
            logger.info("📋 NEXT STEPS:")
            logger.info("   1. Run bot in DEMO_MODE for 1-2 days")
            logger.info("   2. Monitor logs for:")
            logger.info("      - Data availability")
            logger.info("      - Decision quality")
            logger.info("      - System stability")
            logger.info("   3. Proceed to TEST-1 after validation")
            logger.info("")
        
        return passed


def main():
    """Run TEST-0"""
    print("\n" + "="*60)
    print("🧪 ANGEL-X MASTER TEST PLAN")
    print("="*60)
    print("")
    
    # Show test progression
    print(TestProgression.get_progress_report())
    
    # Check if TEST-0 can run
    if not TestProgression.can_run_test('TEST-0'):
        print("❌ Cannot run TEST-0 at this time")
        return False
    
    # Run TEST-0
    test = Test0PreTestSafetySetup()
    passed = test.run()
    
    if passed:
        print("")
        print("="*60)
        print("✅ TEST-0 COMPLETE")
        print("="*60)
        print("")
        print("👉 Next: TEST-1 - DATA & HEALTH TEST")
        print("   Duration: 1-2 days")
        print("   Focus: Data quality, system stability")
        print("")
    else:
        print("")
        print("="*60)
        print("❌ TEST-0 FAILED - FIX CONFIGURATION")
        print("="*60)
        print("")
    
    return passed


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
