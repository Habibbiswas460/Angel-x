"""
Golden Rules Validator

Validates all 4 Golden Rules before allowing TEST-8 (micro live)

Golden Rules:
1. SL কখনো skip হয়নি?           → YES ✅
2. Loss এর পর bot চুপ ছিল?       → YES ✅
3. Chop day-এ trade কম?          → YES ✅
4. তুমি mentally শান্ত?          → YES ✅

One NO → STOP immediately
"""
import sys
import json
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.test_config import GoldenRules, TestProgression
from app.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)

GOLDEN_RULES_FILE = '/tmp/angel_x_golden_rules.json'


def load_golden_rules():
    """Load Golden Rules from persistence file"""
    try:
        if Path(GOLDEN_RULES_FILE).exists():
            with open(GOLDEN_RULES_FILE, 'r') as f:
                data = json.load(f)
                GoldenRules.SL_NEVER_SKIPPED = data.get('SL_NEVER_SKIPPED')
                GoldenRules.CALM_AFTER_LOSS = data.get('CALM_AFTER_LOSS')
                GoldenRules.LOW_TRADES_ON_CHOP = data.get('LOW_TRADES_ON_CHOP')
                GoldenRules.MENTALLY_CALM = data.get('MENTALLY_CALM')
    except Exception as e:
        logger.warning(f"Could not load Golden Rules: {e}")


def validate_golden_rules():
    """Validate all Golden Rules"""
    print("\n" + "="*80)
    print(" " * 25 + "🏆 GOLDEN RULES VALIDATION 🏆")
    print("="*80)
    print("")
    
    print("⚠️ ALL must be YES to proceed to TEST-8 (Micro Live)")
    print("⚠️ One NO → STOP immediately")
    print("")
    
    # Load Golden Rules from persistence
    load_golden_rules()
    
    # Check each rule
    print("="*80)
    print("Golden Rules Status:")
    print("="*80)
    
    rules = [
        ("SL কখনো skip হয়নি?", GoldenRules.SL_NEVER_SKIPPED),
        ("Loss এর পর bot চুপ ছিল?", GoldenRules.CALM_AFTER_LOSS),
        ("Chop day-এ trade কম?", GoldenRules.LOW_TRADES_ON_CHOP),
        ("তুমি mentally শান্ত?", GoldenRules.MENTALLY_CALM)
    ]
    
    all_yes = True
    
    for i, (rule, status) in enumerate(rules, 1):
        if status is True:
            status_str = "YES ✅"
        elif status is False:
            status_str = "NO ❌"
            all_yes = False
        else:
            status_str = "Not checked ⏳"
            all_yes = False
        
        print(f"{i}. {rule}")
        print(f"   → {status_str}")
        print("")
    
    print("="*80)
    
    # Final verdict
    if all_yes and GoldenRules.all_passed():
        print("✅ ALL GOLDEN RULES PASSED")
        print("")
        print("🎉 You are ready for TEST-8 (Micro Live)")
        print("")
        print("Next steps:")
        print("   1. Run: python3 scripts/run_master_test.py --test TEST-8")
        print("   2. Max 1 trade/day")
        print("   3. Smallest position size")
        print("   4. Monitor for 5-10 days")
        print("")
        return True
    else:
        print("❌ GOLDEN RULES NOT SATISFIED")
        print("")
        print("⛔ CANNOT proceed to TEST-8")
        print("")
        print("Action required:")
        
        if GoldenRules.SL_NEVER_SKIPPED is False:
            print("   ✗ Fix: SL was skipped - Review TEST-6 and fix SL logic")
        
        if GoldenRules.CALM_AFTER_LOSS is False:
            print("   ✗ Fix: Revenge trading detected - Review TEST-5 cooldown")
        
        if GoldenRules.LOW_TRADES_ON_CHOP is False:
            print("   ✗ Fix: Too many trades on chop days - Review TEST-2 bias logic")
        
        if GoldenRules.MENTALLY_CALM is False:
            print("   ✗ Fix: Mental state not calm - Take a break, review logs")
        
        if any(r[1] is None for r in rules):
            print("   ⚠️ Some rules not checked yet - Complete all tests first")
        
        print("")
        print("⚠️ Do NOT skip this. One NO = STOP.")
        print("")
        return False
    
    print("="*80)


def manual_golden_rules_check():
    """Manual self-assessment for Golden Rules"""
    print("\n" + "="*80)
    print("📋 MANUAL GOLDEN RULES SELF-ASSESSMENT")
    print("="*80)
    print("")
    print("Be HONEST with yourself. Your capital depends on it.")
    print("")
    
    # Rule 1: SL never skipped
    print("="*80)
    print("1. SL কখনো skip হয়নি?")
    print("="*80)
    print("Check:")
    print("  □ Did bot ALWAYS place SL?")
    print("  □ Did SL ALWAYS get filled (or force exit)?")
    print("  □ Zero naked positions ever?")
    print("")
    answer = input("Answer (yes/no): ").strip().lower()
    GoldenRules.SL_NEVER_SKIPPED = (answer == 'yes')
    print(f"→ {GoldenRules.SL_NEVER_SKIPPED}")
    print("")
    
    # Rule 2: Calm after loss
    print("="*80)
    print("2. Loss এর পর bot চুপ ছিল?")
    print("="*80)
    print("Check:")
    print("  □ Cooldown enforced?")
    print("  □ Zero revenge trading?")
    print("  □ Gap between consecutive losses?")
    print("")
    answer = input("Answer (yes/no): ").strip().lower()
    GoldenRules.CALM_AFTER_LOSS = (answer == 'yes')
    print(f"→ {GoldenRules.CALM_AFTER_LOSS}")
    print("")
    
    # Rule 3: Low trades on chop
    print("="*80)
    print("3. Chop day-এ trade কম?")
    print("="*80)
    print("Check:")
    print("  □ Choppy days logged?")
    print("  □ ≤2 trades on chop days?")
    print("  □ High block rate maintained?")
    print("")
    answer = input("Answer (yes/no): ").strip().lower()
    GoldenRules.LOW_TRADES_ON_CHOP = (answer == 'yes')
    print(f"→ {GoldenRules.LOW_TRADES_ON_CHOP}")
    print("")
    
    # Rule 4: Mentally calm
    print("="*80)
    print("4. তুমি mentally শান্ত?")
    print("="*80)
    print("Check:")
    print("  □ Can sleep peacefully?")
    print("  □ No constant chart checking?")
    print("  □ Trust the system?")
    print("")
    answer = input("Answer (yes/no): ").strip().lower()
    GoldenRules.MENTALLY_CALM = (answer == 'yes')
    print(f"→ {GoldenRules.MENTALLY_CALM}")
    print("")
    
    # Validate
    return validate_golden_rules()


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("🏆 GOLDEN RULES VALIDATOR")
    print("="*80)
    print("")
    
    # Check test progression
    if 'TEST-7' not in TestProgression.completed_tests:
        print("⚠️ Warning: TEST-7 not completed yet")
        print("   Golden Rules validation usually done after TEST-7")
        print("")
    
    print("Choose validation mode:")
    print("  1. Automatic (from test results)")
    print("  2. Manual self-assessment")
    print("")
    
    choice = input("Choice (1/2): ").strip()
    
    if choice == '2':
        return manual_golden_rules_check()
    else:
        return validate_golden_rules()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
