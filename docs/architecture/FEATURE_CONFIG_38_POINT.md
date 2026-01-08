"""
Configuration for 38-point Feature Integration
Add these settings to your config.py or .env
"""

# ============================================================================
# 1. REAL-TIME DASHBOARD (Feature #6)
# ============================================================================
DASHBOARD_ENABLED = True
DASHBOARD_PORT = 5000
DASHBOARD_REFRESH_INTERVAL = 2  # seconds

# ============================================================================
# 2. SMART EXIT ENGINE (Features #4, #5)
# ============================================================================
USE_SMART_EXIT_ENGINE = True
USE_TRAILING_STOP = True
TRAILING_STOP_PERCENT = 2.0  # Trail by 2% of peak price

USE_PROFIT_LADDER = True
PROFIT_LADDER_RUNGS = [
    (1.0, 0.25),   # Exit 25% at 1% profit
    (2.0, 0.50),   # Exit 50% at 2% profit
    (3.0, 0.25),   # Exit 25% at 3% profit
]

MAX_HOLD_TIME = 600  # 10 minutes in seconds
EXPIRY_EXIT_MINUTES = 5  # Exit 5 minutes before expiry

# Greeks-based exit thresholds
DELTA_WEAKNESS_THRESHOLD = 0.15  # 15% degradation
GAMMA_ROLLOVER_THRESHOLD = 0.8   # 80% of entry gamma
IV_CRUSH_THRESHOLD = 5.0          # 5% IV drop

# ============================================================================
# 3. TRADE JOURNAL ANALYTICS (Feature #7)
# ============================================================================
TRADE_JOURNAL_ENABLED = True
JOURNAL_DIR = "./journal"
EXPORT_ANALYTICS_ON_STOP = True

# ============================================================================
# 4. MULTI-STRIKE PORTFOLIO (Feature #3)
# ============================================================================
USE_MULTI_STRIKE = False  # Enable multi-strike trading
HEDGE_STRIKES = []  # ['+100', '-100'] for hedges
USE_SPREADS = False
SPREAD_TYPE = "BULL_CALL"  # BULL_CALL, BEAR_PUT, IRON_CONDOR

# ============================================================================
# 5. REAL BROKER GREEKS (Feature #2)
# ============================================================================
USE_BROKER_GREEKS = False  # Use broker's Greeks if available
BROKER_GREEKS_ENDPOINT = None
GREEKS_UPDATE_INTERVAL = 5  # seconds

# ============================================================================
# 6. VOLATILITY REGIME DETECTION (Feature #11)
# ============================================================================
USE_VOLATILITY_REGIME = False
REGIME_DETECTION_PERIOD = 20  # bars/ticks
LOW_VOL_THRESHOLD = 10  # VIX
HIGH_VOL_THRESHOLD = 25  # VIX

# ============================================================================
# 7. SMART MONEY FLOW TRACKING (Feature #12)
# ============================================================================
TRACK_SMART_MONEY = False
OI_BUILDUP_THRESHOLD = 1000  # contracts
MONITOR_MAX_PAIN = False

# ============================================================================
# 8. DYNAMIC POSITION SIZING (Feature #15)
# ============================================================================
USE_DYNAMIC_SIZING = False
USE_KELLY_CRITERION = False
KELLY_FRACTION = 0.25  # Conservative Kelly

# ============================================================================
# 9. GREEKS EXPOSURE LIMITS (Feature #16)
# ============================================================================
USE_GREEKS_LIMITS = False
MAX_PORTFOLIO_DELTA = 500
MAX_PORTFOLIO_GAMMA = 2.0
MAX_PORTFOLIO_VEGA = 1000

# ============================================================================
# 10. CIRCUIT BREAKER SYSTEM (Feature #18)
# ============================================================================
USE_CIRCUIT_BREAKER = False
CIRCUIT_BREAKER_TRIGGERS = [
    ('flash_crash', -5),      # -5% drop
    ('extreme_vol', 50),      # VIX > 50
    ('api_failure', True),    # API down
]

# ============================================================================
# 11. DATABASE LAYER (Feature #26)
# ============================================================================
USE_DATABASE = False
DB_TYPE = "postgresql"  # postgresql, mongodb
DB_HOST = "localhost"
DB_PORT = 5432
DB_NAME = "angelx"
DB_USER = "angelx"
DB_PASSWORD = "password"

# ============================================================================
# 12. BACKTESTING (Feature #5)
# ============================================================================
BACKTESTING_ENABLED = False
BACKTEST_DATA_SOURCE = "local"  # local, broker
BACKTEST_FROM_DATE = "2024-01-01"
BACKTEST_TO_DATE = "2024-01-31"
BACKTEST_SLIPPAGE_PERCENT = 0.05  # 0.05%

# ============================================================================
# 13. PAPER TRADING WITH SLIPPAGE (Feature #22)
# ============================================================================
USE_REALISTIC_SLIPPAGE = True
SLIPPAGE_MODEL = "spread_based"  # spread_based, volatility_based
BASE_SPREAD_PERCENT = 0.1  # 0.1%
SLIPPAGE_VOLATILITY = "normal"  # normal, high, extreme

# ============================================================================
# 14. MULTI-ACCOUNT SUPPORT (Feature #24)
# ============================================================================
USE_MULTI_ACCOUNT = False
SECONDARY_BROKER_CONFIG = None

# ============================================================================
# 15. AUTO-RECONNECT & FAILOVER (Feature #25)
# ============================================================================
AUTO_RECONNECT_ENABLED = True
RECONNECT_MAX_ATTEMPTS = 5
RECONNECT_BACKOFF_MULTIPLIER = 2  # Exponential backoff

# ============================================================================
# 16. ADVANCED FEATURES FLAGS
# ============================================================================
ML_STRIKE_PREDICTION_ENABLED = False
PATTERN_RECOGNITION_ENABLED = False
ADAPTIVE_PARAMETERS_ENABLED = True

# Scalping vs Swing vs Volatility modes
STRATEGY_MODE = "SCALPING"  # SCALPING, SWING, VOLATILITY
SCALPING_HOLD_MINUTES = 0.25  # 15 seconds
SWING_HOLD_DAYS = 1

# Voice alerts
VOICE_ALERTS_ENABLED = False
VOICE_ENGINE = "gtts"  # gtts, pyttsx3
