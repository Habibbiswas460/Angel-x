"""
Angel-X Enhanced Risk Management Configuration
Production-ready risk parameters with slippage buffer and execution failure handling
"""

# ============================================================================
# CORE RISK LIMITS
# ============================================================================

# Daily Loss/Profit Limits (in rupees)
MAX_DAILY_LOSS = 2000           # Maximum loss per day
MAX_DAILY_PROFIT = 5000         # Target profit per day (0 = unlimited)

# Trade Limits
MAX_TRADES_PER_DAY = 10         # Maximum number of trades per day
MAX_POSITION_SIZE = 50          # Maximum lots per trade

# ============================================================================
# ENHANCED: SLIPPAGE PROTECTION
# ============================================================================

# Slippage Buffer (10-15% recommended)
# Real loss can exceed calculated SL due to:
# - Gap moves
# - Slippage on fill
# - Delayed execution
SLIPPAGE_BUFFER_PERCENT = 0.15  # 15% safety margin

# Effective max loss calculation:
# EFFECTIVE_MAX_LOSS = MAX_DAILY_LOSS * (1 - SLIPPAGE_BUFFER_PERCENT)
# Example: 2000 * 0.85 = 1700 (stops trading at -1700 instead of -2000)

# ============================================================================
# ENHANCED: LOSS-BASED COOLDOWN
# ============================================================================

# Consecutive Loss Control
CONSECUTIVE_LOSS_LIMIT = 2      # Number of consecutive losses before cooldown
COOLDOWN_AFTER_CONSECUTIVE_LOSS = 15  # Minutes to wait after hitting limit

# Examples:
# - 1 loss → continue trading
# - 2 losses in a row → 15 min cooldown
# - Win → cooldown reset

# Cooldown benefits:
# ✅ Prevents revenge trading
# ✅ Avoids choppy market traps
# ✅ Protects capital in bad conditions

# ============================================================================
# ENHANCED: MULTI-LEG STRATEGY CONTROL
# ============================================================================

# Multi-leg Safety (Straddle, Strangle, Spreads)
MULTI_LEG_ENABLED = False       # Default: Disabled for initial testing

# Reason for disabled by default:
# - Multi-leg has complex Greeks interaction
# - Risk calculation different from single-leg
# - Requires separate testing cycle
# 
# Enable only after:
# ✅ Single-leg proven profitable
# ✅ Multi-leg Greeks logic tested
# ✅ Separate risk parameters defined

# ============================================================================
# ENHANCED: EXECUTION FAILURE TRACKING
# ============================================================================

# Failure Rate Thresholds
MAX_REJECTION_RATE = 0.30       # 30% rejection rate → halt trading
MIN_ATTEMPTS_FOR_RATE_CHECK = 10  # Minimum attempts before checking rate

# Tracked failure types:
# - rejected_orders: Broker rejected order
# - partial_fills: Order partially filled
# - delayed_fills: Execution delayed significantly
# - sl_placement_failures: SL order failed to place

# These metrics feed into:
# ✅ Risk dashboard
# ✅ Phase 10 adaptive learning
# ✅ Broker/market condition alerts

# ============================================================================
# SL PLACEMENT FAILURE HANDLING
# ============================================================================

# What happens if SL fails to place:
SL_FAILURE_ACTION = "FORCE_EXIT"  # Options: "FORCE_EXIT", "RETRY", "ALERT_ONLY"

# Force exit behavior:
# - SL placement fails → Immediately market exit the position
# - Don't wait for retry
# - Prevents naked position without protection

# ============================================================================
# POSITION RISK VALIDATION
# ============================================================================

# Single trade shouldn't risk more than X% of daily limit
MAX_SINGLE_TRADE_RISK_PCT = 0.50  # 50% of daily limit

# Risk per trade (% of capital)
RISK_PER_TRADE = 0.02           # 2% per trade (from main config)

# These work together:
# Example with 50k capital, 2k daily limit:
# - Single trade max risk: 1000 (50% of 2k daily limit)
# - This equals 2% of 50k capital
# - With slippage buffer: actual limit ~850

# ============================================================================
# CIRCUIT BREAKER SETTINGS
# ============================================================================

# Automatic halt triggers:
CIRCUIT_BREAKER_TRIGGERS = {
    'daily_loss_limit': True,       # Halt when daily loss limit hit
    'daily_profit_target': True,    # Halt when profit target achieved
    'consecutive_losses': True,     # Cooldown (not halt) after N losses
    'high_rejection_rate': True,    # Halt if >30% orders rejected
    'execution_anomaly': True       # Halt on unusual execution patterns
}

# Manual resume required after halt
AUTO_RESUME_AFTER_HALT = False

# ============================================================================
# TIME-BASED RESTRICTIONS
# ============================================================================

# Trading window (from main config)
# MARKET_START_TIME = "09:15"
# SQUARE_OFF_TIME = "15:15"

# Additional time-based rules:
NO_TRADE_FIRST_MIN = 5          # Don't trade first 5 minutes (volatility)
NO_TRADE_LAST_MIN = 15          # Don't trade last 15 minutes (square-off rush)

# ============================================================================
# RECOMMENDED TESTING PROTOCOL
# ============================================================================

"""
BEFORE GOING LIVE - MANDATORY TESTS:

🧪 Test 1: No-Order Safety Test
  - Disable actual order execution
  - Run for full day
  - Check: How many signals blocked by risk manager
  - Expected: High block rate = good

🧪 Test 2: Forced Loss Simulation
  - Simulate SL hits
  - Check: Bot stops at limit
  - Check: No revenge trading
  - Expected: Clean stop

🧪 Test 3: SL Failure Scenario
  - Mock SL placement failure
  - Check: Force exit triggered
  - Check: No naked positions
  - Expected: Immediate exit

🧪 Test 4: Cooldown Verification
  - Simulate 2 consecutive losses
  - Check: 15 min pause activated
  - Check: Trading resumes after cooldown
  - Expected: Strict cooldown respect

🧪 Test 5: Over-Signal Test
  - Run in choppy market
  - Check: Trade count limited
  - Check: Cooldown activating properly
  - Expected: Capital protected

PAPER TRADING MINIMUM: 1 WEEK
- Test all market conditions
- Verify all risk rules working
- Check execution failure handling
- Validate slippage assumptions

ONLY THEN → LIVE with SMALL CAPITAL
"""

# ============================================================================
# PRODUCTION DEPLOYMENT CHECKLIST
# ============================================================================

"""
Before live trading, verify:

✅ MAX_DAILY_LOSS set appropriately
✅ SLIPPAGE_BUFFER tested on paper
✅ CONSECUTIVE_LOSS_LIMIT = 2 (don't increase)
✅ COOLDOWN_AFTER_CONSECUTIVE_LOSS >= 15 min
✅ MULTI_LEG_ENABLED = False (until tested separately)
✅ All test scripts passing
✅ Execution failure tracking active
✅ Logger configured properly
✅ Dashboard showing risk metrics
✅ Manual halt/resume tested

⚠️ START SMALL:
- First week: 10% of planned capital
- Monitor every trade
- Verify risk rules working
- Scale up only after consistency
"""
