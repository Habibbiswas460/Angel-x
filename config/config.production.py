# Production Configuration - Angel-X Trading System
# Copy this file to config/config.py and update with production credentials

import os
from datetime import datetime

# ============================================================================
# Environment Settings
# ============================================================================
ENVIRONMENT = os.getenv('ENVIRONMENT', 'production')
DEBUG = os.getenv('DEBUG', 'false').lower() == 'true'
TESTING = False
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
TIMEZONE = os.getenv('TIMEZONE', 'Asia/Kolkata')

# ============================================================================
# Trading Configuration
# ============================================================================
TRADING_ENABLED = os.getenv('TRADING_ENABLED', 'false').lower() == 'true'
TRADING_MODE = 'LIVE' if TRADING_ENABLED else 'DEMO'  # LIVE, DEMO, PAPER
TRADING_HOURS_START = '09:15'  # NSE market open
TRADING_HOURS_END = '15:30'    # NSE market close
TRADING_DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI']

# ============================================================================
# AngelOne Broker Configuration
# ============================================================================
ANGELONE_BROKER = 'angelone'
ANGELONE_CLIENT_ID = os.getenv('ANGELONE_CLIENT_ID', '')
ANGELONE_PASSWORD = os.getenv('ANGELONE_PASSWORD', '')
ANGELONE_TOTP_SECRET = os.getenv('ANGELONE_TOTP_SECRET', '')
ANGELONE_API_KEY = os.getenv('ANGELONE_API_KEY', '')
ANGELONE_FEED_TOKEN = os.getenv('ANGELONE_FEED_TOKEN', '')

# Broker connection settings
BROKER_CONNECT_TIMEOUT = 30  # seconds
BROKER_RECONNECT_ATTEMPTS = 5
BROKER_RECONNECT_DELAY = 10  # seconds
BROKER_HEARTBEAT_INTERVAL = 60  # seconds

# ============================================================================
# Market Data Configuration
# ============================================================================
MARKET_DATA_SOURCE = 'angelone'  # angelone or yfinance
MARKET_DATA_SYMBOLS = [
    'NSE:NIFTY50',
    'NSE:BANKNIFTY',
    'NSE:FINNIFTY',
    'NSE:MIDCPNIFTY',
]

# Market data update frequency
MARKET_DATA_UPDATE_INTERVAL = 1  # seconds
OPTION_CHAIN_UPDATE_INTERVAL = 5  # seconds
GREEKS_UPDATE_INTERVAL = 5  # seconds

# Data retention
MARKET_DATA_HISTORY_DAYS = 90
OPTION_CHAIN_HISTORY_DAYS = 7
TRADES_HISTORY_DAYS = 365

# ============================================================================
# Database Configuration
# ============================================================================
DATABASE_TYPE = 'postgresql'
DATABASE_HOST = os.getenv('DATABASE_HOST', 'postgres')
DATABASE_PORT = int(os.getenv('DATABASE_PORT', '5432'))
DATABASE_NAME = os.getenv('DATABASE_NAME', 'angelx_ml')
DATABASE_USER = os.getenv('DATABASE_USER', 'angelx')
DATABASE_PASSWORD = os.getenv('DATABASE_PASSWORD', '')
DATABASE_POOL_SIZE = 8
DATABASE_POOL_RECYCLE = 3600

# Construct connection string
DATABASE_URL = (
    f"postgresql://{DATABASE_USER}:{DATABASE_PASSWORD}@"
    f"{DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}"
)

# ============================================================================
# Risk Management Configuration
# ============================================================================
# Position sizing
INITIAL_CAPITAL = float(os.getenv('INITIAL_CAPITAL', '100000'))  # ₹1,00,000
RISK_PER_TRADE = 0.02  # 2% of capital per trade
MAX_POSITION_SIZE = 0.10  # 10% of capital max per position
MAX_DAILY_LOSS = 0.05  # 5% daily loss limit

# Greeks-based limits
MAX_DELTA_EXPOSURE = 50  # Δ limit per symbol
MAX_GAMMA_EXPOSURE = 100  # Γ limit per symbol
MAX_VEGA_EXPOSURE = 1000  # ν limit per symbol
MAX_THETA_EXPOSURE = 500  # Θ limit per symbol

# Trading limits
MAX_TRADES_PER_DAY = 100
MAX_CONCURRENT_POSITIONS = 20
MIN_OPTION_PRICE = 1  # Minimum option premium
MIN_OPTION_IV = 5  # Minimum implied volatility (%)

# Stop loss and take profit
DEFAULT_SL_PERCENT = 2  # 2% stop loss
DEFAULT_TP_PERCENT = 5  # 5% take profit
TRAILING_SL_PERCENT = 1  # 1% trailing stop loss

# ============================================================================
# Strategy Configuration
# ============================================================================
ENABLED_STRATEGIES = [
    'options_seller_premium',
    'straddle_strangle',
    'bull_call_spread',
    'iron_condor',
]

# Strategy timeframes
TIMEFRAME_INTRADAY = '5m'   # 5-minute candles
TIMEFRAME_SWING = '1h'      # 1-hour candles
TIMEFRAME_LONG = '1d'       # Daily candles

# Signal generation thresholds
SIGNAL_CONFIDENCE_THRESHOLD = 0.65  # 65% confidence minimum
SIGNAL_STRENGTH_THRESHOLD = 0.50  # 50% signal strength minimum

# ============================================================================
# Greeks Engine Configuration
# ============================================================================
GREEKS_CALCULATION_METHOD = 'black_scholes'  # black_scholes, binomial
GREEKS_UPDATE_FREQUENCY = 5000  # Update every 5000 market ticks
GREEKS_IV_SOURCE = 'market'  # market or calculated
GREEKS_SMOOTHING_PERIOD = 20  # Bars for smoothing IV

# ============================================================================
# Learning System Configuration
# ============================================================================
LEARNING_ENABLED = True
LEARNING_MODEL = 'gradient_boosting'  # gradient_boosting, neural_network, ensemble
LEARNING_DATA_RETENTION_DAYS = 365
LEARNING_RETRAINING_INTERVAL = 86400  # 24 hours
LEARNING_MIN_SAMPLES = 500  # Minimum samples for training

# Model performance thresholds
MIN_MODEL_ACCURACY = 0.55  # 55% minimum accuracy
MIN_MODEL_PRECISION = 0.50  # 50% minimum precision
MIN_MODEL_RECALL = 0.50  # 50% minimum recall

# ============================================================================
# Monitoring Configuration
# ============================================================================
MONITORING_ENABLED = True
METRICS_EXPORT_PORT = 8000
METRICS_SCRAPE_INTERVAL = 15  # seconds
PROMETHEUS_ENABLED = True

# Health check configuration
HEALTH_CHECK_INTERVAL = 60  # seconds
HEALTH_CHECK_TIMEOUT = 10  # seconds

# ============================================================================
# Logging Configuration
# ============================================================================
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_FILE = os.path.join(os.path.dirname(__file__), '../logs/angel-x.log')
LOG_MAX_BYTES = 10485760  # 10MB
LOG_BACKUP_COUNT = 7  # Keep 7 backup logs
LOG_ROTATION_TIME = 'midnight'

# Log levels for specific modules
LOG_LEVELS = {
    'app.services.broker': 'DEBUG',
    'app.domains.options': 'INFO',
    'app.domains.trading': 'INFO',
    'app.utils.market_data': 'DEBUG',
}

# ============================================================================
# API Configuration
# ============================================================================
API_HOST = '0.0.0.0'
API_PORT = 5000
API_WORKERS = 4
API_TIMEOUT = 60  # seconds
API_RATE_LIMIT = 1000  # requests per minute
CORS_ENABLED = False  # Disable CORS in production
CORS_ORIGINS = []

# ============================================================================
# Cache Configuration
# ============================================================================
CACHE_ENABLED = True
CACHE_TYPE = 'memory'  # memory, redis
CACHE_TTL = 300  # seconds
CACHE_MAX_SIZE = 10000  # Maximum items in cache

# Redis configuration (if using Redis)
REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
REDIS_DB = 0
REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', '')

# ============================================================================
# Backup Configuration
# ============================================================================
BACKUP_ENABLED = True
BACKUP_FREQUENCY = 'daily'  # daily, weekly
BACKUP_TIME = '02:00'  # 2 AM IST
BACKUP_RETENTION_DAYS = 30
BACKUP_DESTINATION = os.path.join(os.path.dirname(__file__), '../backups/')

# ============================================================================
# Notification Configuration
# ============================================================================
NOTIFICATIONS_ENABLED = True
NOTIFICATION_CHANNELS = ['log']  # log, email, slack, telegram

# Email notifications
EMAIL_ENABLED = False
EMAIL_SMTP_SERVER = os.getenv('EMAIL_SMTP_SERVER', 'smtp.gmail.com')
EMAIL_SMTP_PORT = int(os.getenv('EMAIL_SMTP_PORT', '587'))
EMAIL_SENDER = os.getenv('EMAIL_SENDER', '')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD', '')
EMAIL_RECIPIENTS = os.getenv('EMAIL_RECIPIENTS', '').split(',')

# Slack notifications
SLACK_ENABLED = False
SLACK_WEBHOOK_URL = os.getenv('SLACK_WEBHOOK_URL', '')
SLACK_CHANNEL = '#trading-alerts'

# ============================================================================
# Performance Configuration
# ============================================================================
THREAD_POOL_SIZE = 10
QUEUE_MAX_SIZE = 1000
BATCH_PROCESSING_ENABLED = True
BATCH_SIZE = 100

# ============================================================================
# Security Configuration
# ============================================================================
SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-production')
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_ENABLED = True

# ============================================================================
# Feature Flags
# ============================================================================
FEATURES = {
    'live_trading': TRADING_ENABLED,
    'adaptive_learning': LEARNING_ENABLED,
    'risk_management': True,
    'greeks_calculation': True,
    'options_support': True,
    'broker_integration': True,
    'market_data_feed': True,
    'monitoring': MONITORING_ENABLED,
    'backtesting': False,  # Disable in production
    'paper_trading': not TRADING_ENABLED,  # Enable when not in live trading
}

# ============================================================================
# Validation
# ============================================================================
if TRADING_ENABLED and not all([
    ANGELONE_CLIENT_ID,
    ANGELONE_PASSWORD,
    ANGELONE_TOTP_SECRET,
]):
    raise ValueError("Broker credentials required for live trading")

if not DATABASE_PASSWORD and ENVIRONMENT == 'production':
    raise ValueError("Database password required in production")

print(f"""
═══════════════════════════════════════════════════════════════════════
✓ Angel-X Production Configuration Loaded
═══════════════════════════════════════════════════════════════════════
Environment:        {ENVIRONMENT}
Trading Mode:       {TRADING_MODE}
Database:           {DATABASE_HOST}:{DATABASE_PORT}/{DATABASE_NAME}
Broker:             {ANGELONE_BROKER}
Risk Per Trade:     {RISK_PER_TRADE * 100}%
Max Daily Loss:     {MAX_DAILY_LOSS * 100}%
Initial Capital:    ₹{INITIAL_CAPITAL:,.0f}
═══════════════════════════════════════════════════════════════════════
""")
