"""
Angel-X Testing Configuration
Professional Test Mode Settings
"""

# ============================================================================
# TEST LEVELS - এক এক করে pass করতে হবে
# ============================================================================

TEST_LEVELS = {
    'TEST-0': 'PRE-TEST SAFETY SETUP',
    'TEST-1': 'DATA & HEALTH TEST',
    'TEST-2': 'SIGNAL FLOOD TEST',
    'TEST-3': 'ENTRY QUALITY TEST',
    'TEST-4': 'ADAPTIVE VETO TEST',
    'TEST-5': 'RISK MANAGER TEST',
    'TEST-6': 'SL FAILURE SIMULATION',
    'TEST-7': 'SHADOW-LIVE TEST',
    'TEST-8': 'MICRO LIVE TEST'
}

# ============================================================================
# TEST-0: PRE-TEST SAFETY SETUP (Mandatory)
# ============================================================================

class Test0Config:
    """
    Bot চিন্তা করবে, সিদ্ধান্ত নেবে, কিন্তু order যাবে না
    """
    DEMO_MODE = True              # Bot runs but NO orders
    REAL_MARKET_DATA = True       # Real LTP, Greeks from broker
    ORDER_PLACEMENT = False       # ⚠️ CRITICAL: No orders to broker
    LOG_ALL_DECISIONS = True      # Every decision logged
    
    # Safety gates
    REQUIRE_HEALTH_CHECK = True   # Data health check mandatory
    BLOCK_IF_STALE_DATA = True    # Stop if data old
    

# ============================================================================
# TEST-1: DATA & HEALTH TEST (1-2 days)
# ============================================================================

class Test1Config:
    """
    Data quality and health monitoring test
    """
    # Test duration
    MIN_TEST_DAYS = 1
    MAX_TEST_DAYS = 2
    
    # What to monitor
    CHECK_LTP_AVAILABILITY = True
    CHECK_GREEKS_AVAILABILITY = True
    CHECK_OI_DATA = True
    CHECK_WEBSOCKET_HEALTH = True
    
    # Stale data thresholds (seconds)
    LTP_STALE_THRESHOLD = 10      # LTP older than 10s = stale
    GREEKS_STALE_THRESHOLD = 30   # Greeks older than 30s = stale
    
    # Expected behavior
    EXPECT_MANY_NO_TRADE = True   # Should see many "NO TRADE" logs
    EXPECT_HALT_ON_STALE = True   # Should halt on stale data
    EXPECT_WEBSOCKET_RECOVERY = True  # Should recover from WS drop
    
    # Pass criteria
    MIN_NO_TRADE_PERCENTAGE = 70  # 70%+ time should be NO TRADE
    MAX_STALE_DATA_TRADES = 0     # ZERO trades on stale data
    

# ============================================================================
# TEST-2: SIGNAL FLOOD TEST (Choppy Day)
# ============================================================================

class Test2Config:
    """
    Sideways/choppy market - should NOT trade much
    """
    # Test conditions
    PREFER_SIDEWAYS_DAY = True    # Pick choppy/sideways market day
    
    # Expected metrics
    EXPECT_MANY_SIGNALS = True    # Signals will come
    EXPECT_FEW_TRADES = True      # But trades should be LOW
    EXPECT_NEUTRAL_BIAS = True    # Bias = Neutral most time
    
    # Pass criteria
    MAX_TRADE_TO_SIGNAL_RATIO = 0.2  # Max 20% signals → trades
    MIN_NEUTRAL_BIAS_TIME = 70    # 70%+ time bias = Neutral
    MAX_TRADES_ON_CHOP_DAY = 2    # Maximum 2 trades on choppy day
    

# ============================================================================
# TEST-3: ENTRY QUALITY TEST
# ============================================================================

class Test3Config:
    """
    Entry quality gates - should block most trades
    """
    # Quality checks
    CHECK_GREEKS_STRENGTH = True
    CHECK_SPREAD_WIDTH = True
    CHECK_OI_AUTHENTICITY = True
    CHECK_LIQUIDITY = True
    
    # Pass criteria
    MIN_BLOCK_RATE = 70           # 70-80% signals should be blocked
    MAX_BLOCK_RATE = 80
    ONLY_CLEAN_SETUPS = True      # Only "clean" setups approved
    
    # Expected behavior
    EXPECT_FREQUENT_VETO = True   # Frequent "Entry Quality VETO"
    EXPECT_SPREAD_BLOCKS = True   # "Spread too wide" blocks
    EXPECT_GREEKS_BLOCKS = True   # "Greeks weak" blocks
    

# ============================================================================
# TEST-4: ADAPTIVE VETO TEST (Phase-10)
# ============================================================================

class Test4Config:
    """
    Adaptive learning system test
    """
    # Test duration
    MIN_TEST_DAYS = 2
    MAX_TEST_DAYS = 3
    
    # What to monitor
    MONITOR_ADAPTIVE_BLOCKS = True
    MONITOR_REGIME_DETECTION = True
    MONITOR_CONFIDENCE_SCORES = True
    
    # Expected behavior
    EXPECT_ADAPTIVE_REDUCES_TRADES = True  # AI should reduce trades
    EXPECT_LOW_CONFIDENCE_SKIPS = True     # Low confidence → skip
    
    # Pass criteria
    ADAPTIVE_BLOCK_PERCENTAGE = 30  # Adaptive should block 30%+ entries
    MIN_CONFIDENCE_FOR_TRADE = 0.6  # Minimum 0.6 confidence to trade
    
    # Logging
    LOG_ADAPTIVE_DECISIONS = True
    LOG_REGIME_CHANGES = True
    LOG_LEARNING_UPDATES = True
    

# ============================================================================
# TEST-5: RISK MANAGER TEST (Most Important)
# ============================================================================

class Test5Config:
    """
    Risk management behavior test
    """
    # Test scenarios
    SIMULATE_SL_HITS = True
    SIMULATE_DAILY_LOSS = True
    SIMULATE_CONSECUTIVE_LOSSES = True
    
    # Expected behavior
    EXPECT_NO_TRADE_AFTER_LIMIT = True    # Stop after daily loss
    EXPECT_NO_REVENGE_TRADE = True        # No revenge after loss
    EXPECT_SILENCE_ON_LIMIT = True        # Bot goes silent
    
    # Pass criteria
    ZERO_TRADES_AFTER_DAILY_LIMIT = True
    ZERO_TRADES_DURING_COOLDOWN = True
    RESPECT_MAX_LOSS = True
    
    # Thresholds for testing
    TEST_DAILY_LOSS_LIMIT = -500   # ₹500 daily loss limit for test
    TEST_CONSECUTIVE_LOSS_LIMIT = 2  # 2 consecutive losses
    TEST_COOLDOWN_MINUTES = 15     # 15 min cooldown after loss
    

# ============================================================================
# TEST-6: SL FAILURE SIMULATION (Hard Test)
# ============================================================================

class Test6Config:
    """
    Worst-case scenario: SL fails/delays
    """
    # Simulation modes
    SIMULATE_SL_REJECT = True     # SL order rejected by broker
    SIMULATE_SL_DELAY = True      # SL placement delayed
    SIMULATE_GREEKS_DELAY = True  # Greeks data delayed
    
    # Expected behavior
    EXPECT_FORCE_EXIT = True      # Should force exit on SL failure
    EXPECT_NO_NAKED_POSITION = True  # No position without SL
    EXPECT_WAIT_ON_DELAY = True   # Wait/retry on delay
    
    # Pass criteria
    ZERO_NAKED_POSITIONS = True   # No trade without SL ever
    FORCE_EXIT_ON_SL_FAIL = True  # Force market exit if SL fails
    MAX_SL_RETRY_ATTEMPTS = 3     # Max 3 retry attempts
    

# ============================================================================
# TEST-7: SHADOW-LIVE TEST (Real Feel)
# ============================================================================

class Test7Config:
    """
    Real market, real decisions, NO execution
    "Would have traded" mode
    """
    DEMO_MODE = False             # Full decision making
    EXECUTION_ENABLED = False     # But NO actual orders
    REAL_MARKET_FULL_RUN = True   # Full day simulation
    
    # Logging
    LOG_WOULD_HAVE_TRADED = True  # "WOULD HAVE TRADED" logs
    LOG_ENTRY_EXIT_REASON = True  # Why trade taken/skipped
    LOG_MENTAL_STATE = True       # Bot's "emotional" state
    
    # Expected behavior
    EXPECT_CLEAN_DECISIONS = True
    EXPECT_NO_EMOTIONAL_BEHAVIOR = True
    EXPECT_CONSISTENT_LOGIC = True
    
    # Pass criteria
    ALL_DECISIONS_LOGGED = True
    REASONING_CLEAR = True
    NO_PANIC_BEHAVIOR = True
    

# ============================================================================
# TEST-8: MICRO LIVE TEST (Final Step)
# ============================================================================

class Test8Config:
    """
    ⚠️ LIVE TRADING - Only after ALL tests pass
    """
    # Safety limits
    MAX_TRADES_PER_DAY = 1        # Only 1 trade
    POSITION_SIZE = 1             # Smallest quantity
    NO_OVERRIDE_ALLOWED = False   # No manual override
    NO_PARAMETER_TUNING = False   # No changes during test
    
    # Test duration
    MIN_TEST_DAYS = 5             # Minimum 5 days
    
    # Expected behavior
    EXPECT_CLEAN_EXECUTION = True
    EXPECT_SL_RESPECTED = True
    EXPECT_MENTAL_CALM = True
    
    # Emergency stop
    EMERGENCY_STOP_ENABLED = True
    STOP_ON_FIRST_ERROR = True
    

# ============================================================================
# GOLDEN RULES (Automated Checks)
# ============================================================================

class GoldenRules:
    """
    Final checklist before going live
    All must be YES
    """
    # Mandatory checks
    SL_NEVER_SKIPPED = None       # Will be set during tests
    CALM_AFTER_LOSS = None
    LOW_TRADES_ON_CHOP = None
    MENTALLY_CALM = None
    
    # Validation
    @classmethod
    def all_passed(cls) -> bool:
        """All golden rules must be True"""
        rules = [
            cls.SL_NEVER_SKIPPED,
            cls.CALM_AFTER_LOSS,
            cls.LOW_TRADES_ON_CHOP,
            cls.MENTALLY_CALM
        ]
        return all(r is True for r in rules)
    
    @classmethod
    def report(cls) -> str:
        """Generate golden rules report"""
        report = "\n" + "="*60 + "\n"
        report += "🔚 GOLDEN RULES FINAL CHECKLIST\n"
        report += "="*60 + "\n"
        
        checks = {
            "SL কখনো skip হয়নি?": cls.SL_NEVER_SKIPPED,
            "Loss এর পর bot চুপ ছিল?": cls.CALM_AFTER_LOSS,
            "Chop day-এ trade কম?": cls.LOW_TRADES_ON_CHOP,
            "তুমি mentally শান্ত?": cls.MENTALLY_CALM
        }
        
        for question, status in checks.items():
            if status is True:
                report += f"✅ {question} → YES\n"
            elif status is False:
                report += f"❌ {question} → NO ⚠️ STOP\n"
            else:
                report += f"⏳ {question} → PENDING\n"
        
        report += "="*60 + "\n"
        
        if cls.all_passed():
            report += "✅ ALL CHECKS PASSED - Ready for next level\n"
        else:
            report += "❌ SOME CHECKS FAILED - DO NOT PROCEED\n"
        
        report += "="*60 + "\n"
        return report


# ============================================================================
# TEST PROGRESSION CONTROL
# ============================================================================

class TestProgression:
    """
    Control test level progression
    Cannot skip levels
    """
    # Test completion status
    completed_tests = set()
    current_test = 'TEST-0'
    
    # Test dependencies (must complete in order)
    test_order = [
        'TEST-0', 'TEST-1', 'TEST-2', 'TEST-3',
        'TEST-4', 'TEST-5', 'TEST-6', 'TEST-7', 'TEST-8'
    ]
    
    @classmethod
    def can_run_test(cls, test_name: str) -> bool:
        """Check if test can be run"""
        if test_name not in cls.test_order:
            return False
        
        test_idx = cls.test_order.index(test_name)
        
        # TEST-0 can always run
        if test_idx == 0:
            return True
        
        # All previous tests must be completed
        for i in range(test_idx):
            if cls.test_order[i] not in cls.completed_tests:
                return False
        
        return True
    
    @classmethod
    def mark_completed(cls, test_name: str):
        """Mark test as completed"""
        cls.completed_tests.add(test_name)
        
        # Move to next test
        test_idx = cls.test_order.index(test_name)
        if test_idx < len(cls.test_order) - 1:
            cls.current_test = cls.test_order[test_idx + 1]
    
    @classmethod
    def get_progress_report(cls) -> str:
        """Generate progress report"""
        report = "\n" + "="*60 + "\n"
        report += "🧪 ANGEL-X TEST PROGRESSION\n"
        report += "="*60 + "\n"
        
        for test in cls.test_order:
            status = "✅ COMPLETE" if test in cls.completed_tests else "⏳ PENDING"
            is_current = "👉 " if test == cls.current_test else "   "
            report += f"{is_current}{test}: {TEST_LEVELS[test]} - {status}\n"
        
        report += "="*60 + "\n"
        report += f"Current Test: {cls.current_test}\n"
        report += f"Completed: {len(cls.completed_tests)}/{len(cls.test_order)}\n"
        report += "="*60 + "\n"
        
        return report


# ============================================================================
# ACTIVE TEST CONFIGURATION
# ============================================================================

# Current active test (change this to switch test modes)
ACTIVE_TEST = 'TEST-0'  # Start with safety setup

# Get active test config
def get_active_config():
    """Get configuration for active test"""
    configs = {
        'TEST-0': Test0Config,
        'TEST-1': Test1Config,
        'TEST-2': Test2Config,
        'TEST-3': Test3Config,
        'TEST-4': Test4Config,
        'TEST-5': Test5Config,
        'TEST-6': Test6Config,
        'TEST-7': Test7Config,
        'TEST-8': Test8Config
    }
    return configs.get(ACTIVE_TEST, Test0Config)


# ============================================================================
# EXPORT
# ============================================================================

__all__ = [
    'TEST_LEVELS',
    'Test0Config', 'Test1Config', 'Test2Config', 'Test3Config',
    'Test4Config', 'Test5Config', 'Test6Config', 'Test7Config', 'Test8Config',
    'GoldenRules',
    'TestProgression',
    'ACTIVE_TEST',
    'get_active_config'
]
