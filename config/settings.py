"""
ANGEL-X Configuration Manager
Professional configuration system with environment-based settings,
validation, and security best practices.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from dotenv import load_dotenv
import logging

# ============================================================================
# ENVIRONMENT DETECTION
# ============================================================================

# Get project root
PROJECT_ROOT = Path(__file__).parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)
else:
    print(f"⚠️  WARNING: .env file not found at {ENV_FILE}")
    print(f"   Copy .env.example to .env and configure settings")

# Current environment
ENVIRONMENT = os.getenv("ANGELX_ENV", "development").lower()
DEBUG = os.getenv("DEBUG", "True").lower() == "true"
APP_NAME = os.getenv("APP_NAME", "ANGEL-X")

# Validate environment
VALID_ENVIRONMENTS = ["development", "staging", "production"]
if ENVIRONMENT not in VALID_ENVIRONMENTS:
    raise ValueError(f"Invalid ANGELX_ENV='{ENVIRONMENT}'. Must be one of: {VALID_ENVIRONMENTS}")

# ============================================================================
# CONFIGURATION HELPER FUNCTIONS
# ============================================================================

def get_env_bool(key: str, default: bool = False) -> bool:
    """Get boolean from environment variable."""
    value = os.getenv(key, str(default)).lower()
    return value in ("true", "1", "yes", "on")

def get_env_int(key: str, default: int = 0) -> int:
    """Get integer from environment variable."""
    try:
        return int(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_float(key: str, default: float = 0.0) -> float:
    """Get float from environment variable."""
    try:
        return float(os.getenv(key, str(default)))
    except ValueError:
        return default

def get_env_list(key: str, default: List[str] = None, separator: str = ",") -> List[str]:
    """Get list from environment variable."""
    if default is None:
        default = []
    value = os.getenv(key, "")
    if not value:
        return default
    return [item.strip() for item in value.split(separator) if item.strip()]

# ============================================================================
# ANGELONE BROKER CONFIGURATION
# ============================================================================

ANGELONE_API_KEY = os.getenv("ANGELONE_API_KEY", "")
ANGELONE_CLIENT_CODE = os.getenv("ANGELONE_CLIENT_CODE", "")
ANGELONE_PASSWORD = os.getenv("ANGELONE_PASSWORD", "")
ANGELONE_TOTP_SECRET = os.getenv("ANGELONE_TOTP_SECRET", "")

ANGELONE_API_TIMEOUT = get_env_int("ANGELONE_API_TIMEOUT", 30)
ANGELONE_MAX_RETRIES = get_env_int("ANGELONE_MAX_RETRIES", 3)
ANGELONE_RETRY_DELAY = get_env_int("ANGELONE_RETRY_DELAY", 2)

# ============================================================================
# TRADING MODE
# ============================================================================

PAPER_TRADING = get_env_bool("PAPER_TRADING", True)
PAPER_INITIAL_CAPITAL = get_env_float("PAPER_INITIAL_CAPITAL", 100000)
PAPER_SLIPPAGE_PCT = get_env_float("PAPER_SLIPPAGE_PCT", 0.05)

# Force paper trading in development
if ENVIRONMENT == "development" and not PAPER_TRADING:
    print("⚠️  WARNING: Forcing PAPER_TRADING=True in development environment")
    PAPER_TRADING = True

# Additional trading settings
TRADING_ENABLED = get_env_bool("TRADING_ENABLED", False)
LIVE_TRADING_CONFIRMATION = get_env_bool("LIVE_TRADING_CONFIRMATION", True)

# ============================================================================
# SECURITY SETTINGS
# ============================================================================

SECRET_KEY = os.getenv("SECRET_KEY", "change-me-to-a-strong-random-key-before-production")
if SECRET_KEY == "change-me-to-a-strong-random-key-before-production" and ENVIRONMENT == "production":
    raise ValueError("⚠️ CRITICAL: SECRET_KEY must be changed for production!")

ENCRYPTION_ENABLED = get_env_bool("ENCRYPTION_ENABLED", True)

# ============================================================================
# RISK MANAGEMENT
# ============================================================================

RISK_PER_TRADE = get_env_float("RISK_PER_TRADE", 0.02)
MAX_DAILY_LOSS = get_env_float("MAX_DAILY_LOSS", 5000)
MAX_DAILY_PROFIT = get_env_float("MAX_DAILY_PROFIT", 15000)
MAX_DAILY_TRADES = get_env_int("MAX_DAILY_TRADES", 10)
MAX_CONCURRENT_POSITIONS = get_env_int("MAX_CONCURRENT_POSITIONS", 3)

POSITION_SIZE_MULTIPLIER = get_env_float("POSITION_SIZE_MULTIPLIER", 1.0)
MIN_LOT_SIZE = get_env_int("MIN_LOT_SIZE", 75)
MAX_LOT_SIZE = get_env_int("MAX_LOT_SIZE", 300)

DEFAULT_STOP_LOSS_PCT = get_env_float("DEFAULT_STOP_LOSS_PCT", 0.15)
TRAILING_STOP_LOSS = get_env_bool("TRAILING_STOP_LOSS", True)
TRAILING_STOP_PCT = get_env_float("TRAILING_STOP_PCT", 0.08)

# Greeks limits
MAX_NET_DELTA = get_env_float("MAX_NET_DELTA", 100.0)
MAX_NET_GAMMA = get_env_float("MAX_NET_GAMMA", 5.0)
MAX_DAILY_THETA = get_env_float("MAX_DAILY_THETA", -500.0)

# ============================================================================
# MARKET DATA & CONNECTIVITY
# ============================================================================

DATA_SOURCE = os.getenv("DATA_SOURCE", "angelone")

WEBSOCKET_ENABLED = get_env_bool("WEBSOCKET_ENABLED", True)
WEBSOCKET_RECONNECT_ATTEMPTS = get_env_int("WEBSOCKET_RECONNECT_ATTEMPTS", 5)
WEBSOCKET_RECONNECT_DELAY = get_env_int("WEBSOCKET_RECONNECT_DELAY", 5)
WEBSOCKET_PING_INTERVAL = get_env_int("WEBSOCKET_PING_INTERVAL", 30)
WEBSOCKET_TICK_TIMEOUT = get_env_int("WEBSOCKET_TICK_TIMEOUT", 60)
WEBSOCKET_NO_DATA_FALLBACK = get_env_int("WEBSOCKET_NO_DATA_FALLBACK", 120)

MARKET_DATA_REFRESH = get_env_int("MARKET_DATA_REFRESH", 5)
GREEKS_CALCULATION_INTERVAL = get_env_int("GREEKS_CALCULATION_INTERVAL", 10)
OI_REFRESH_INTERVAL = get_env_int("OI_REFRESH_INTERVAL", 30)
DATA_FRESHNESS_TOLERANCE = get_env_int("DATA_FRESHNESS_TOLERANCE", 5)

# ============================================================================
# STRATEGY PARAMETERS
# ============================================================================

PRIMARY_UNDERLYING = os.getenv("PRIMARY_UNDERLYING", "NIFTY")
ALLOWED_UNDERLYING = get_env_list("ALLOWED_UNDERLYING", ["NIFTY", "BANKNIFTY"])
UNDERLYING_EXCHANGE = "NSE_INDEX"

OPTION_EXPIRY = os.getenv("OPTION_EXPIRY", "weekly")
ALLOWED_STRIKES_RANGE = get_env_int("ALLOWED_STRIKES_RANGE", 5)
OPTION_PRODUCT = os.getenv("OPTION_PRODUCT", "MIS")

# Trading session
TRADING_SESSION_START = os.getenv("TRADING_SESSION_START", "09:15")
TRADING_SESSION_END = os.getenv("TRADING_SESSION_END", "15:30")
NO_TRADE_START_TIME = os.getenv("NO_TRADE_START_TIME", "09:15")
NO_TRADE_END_TIME = os.getenv("NO_TRADE_END_TIME", "09:20")
NO_TRADE_LAST_MINUTES = get_env_int("NO_TRADE_LAST_MINUTES", 45)

# Volatility
IV_EXTREMELY_LOW_THRESHOLD = get_env_float("IV_LOW_THRESHOLD", 15.0)
IV_EXTREMELY_HIGH_THRESHOLD = get_env_float("IV_HIGH_THRESHOLD", 50.0)
IV_SAFE_ZONE = (
    get_env_float("IV_OPTIMAL_MIN", 20.0),
    get_env_float("IV_OPTIMAL_MAX", 40.0)
)

# Bias engine
BULLISH_DELTA_MIN = get_env_float("BULLISH_DELTA_MIN", 0.45)
BEARISH_DELTA_MAX = get_env_float("BEARISH_DELTA_MAX", -0.45)
NO_TRADE_DELTA_WEAK = get_env_float("NO_TRADE_DELTA_WEAK", 0.35)

# Strike selection
IDEAL_DELTA_CALL = (
    get_env_float("IDEAL_DELTA_CALL_MIN", 0.45),
    get_env_float("IDEAL_DELTA_CALL_MAX", 0.65)
)
IDEAL_DELTA_PUT = (
    get_env_float("IDEAL_DELTA_PUT_MIN", -0.65),
    get_env_float("IDEAL_DELTA_PUT_MAX", -0.45)
)
IDEAL_GAMMA_MIN = get_env_float("IDEAL_GAMMA_MIN", 0.002)
IDEAL_THETA_MAX = get_env_float("IDEAL_THETA_MAX", -0.05)

# Liquidity
MIN_BID_ASK_SPREAD_PCT = get_env_float("MIN_BID_ASK_SPREAD_PCT", 0.5)
MAX_BID_ASK_SPREAD_PCT = get_env_float("MAX_BID_ASK_SPREAD_PCT", 2.0)
MIN_OPEN_INTEREST = get_env_int("MIN_OPEN_INTEREST", 1000)
MIN_VOLUME = get_env_int("MIN_VOLUME", 500)

# ============================================================================
# DASHBOARD & API
# ============================================================================

DASHBOARD_ENABLED = get_env_bool("DASHBOARD_ENABLED", True)
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0")
DASHBOARD_PORT = get_env_int("DASHBOARD_PORT", 5001)
DASHBOARD_DEBUG = get_env_bool("DASHBOARD_DEBUG", False)

# Dashboard customization
DASHBOARD_VERSION = os.getenv("DASHBOARD_VERSION", "enhanced")  # minimal, modern, advanced, enhanced
DASHBOARD_REFRESH_RATE = get_env_int("DASHBOARD_REFRESH_RATE", 5)
DASHBOARD_THEME = os.getenv("DASHBOARD_THEME", "light")  # light, dark, auto
DASHBOARD_CHARTS_ENABLED = get_env_bool("DASHBOARD_CHARTS_ENABLED", True)
DASHBOARD_EXPORT_ENABLED = get_env_bool("DASHBOARD_EXPORT_ENABLED", True)
DASHBOARD_ALERTS_ENABLED = get_env_bool("DASHBOARD_ALERTS_ENABLED", True)

API_ENABLED = get_env_bool("API_ENABLED", True)
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = get_env_int("API_PORT", 5000)
API_CORS_ENABLED = get_env_bool("API_CORS_ENABLED", True)

# ============================================================================
# LOGGING
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_TO_CONSOLE = get_env_bool("LOG_TO_CONSOLE", True)
LOG_TO_FILE = get_env_bool("LOG_TO_FILE", True)
LOG_DIR = os.getenv("LOG_DIR", "./logs")

LOG_MAX_BYTES = get_env_int("LOG_MAX_BYTES", 10485760)  # 10MB
LOG_BACKUP_COUNT = get_env_int("LOG_BACKUP_COUNT", 5)

LOG_FORMAT = os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
LOG_DATE_FORMAT = os.getenv("LOG_DATE_FORMAT", "%Y-%m-%d %H:%M:%S")

# ============================================================================
# DATABASE & EXPORTS
# ============================================================================

DB_ENABLED = get_env_bool("DB_ENABLED", False)
DB_TYPE = os.getenv("DB_TYPE", "sqlite")
DB_PATH = os.getenv("DB_PATH", "./data/angelx.db")

EXPORT_TRADES_CSV = get_env_bool("EXPORT_TRADES_CSV", True)
EXPORT_METRICS_CSV = get_env_bool("EXPORT_METRICS_CSV", True)
CSV_EXPORT_DIR = os.getenv("CSV_EXPORT_DIR", "./data/exports")

# ============================================================================
# ALERTS & NOTIFICATIONS
# ============================================================================

EMAIL_ALERTS_ENABLED = get_env_bool("EMAIL_ALERTS_ENABLED", False)
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = get_env_int("SMTP_PORT", 587)
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ALERT_EMAIL = os.getenv("ALERT_EMAIL", "")

TELEGRAM_ALERTS_ENABLED = get_env_bool("TELEGRAM_ALERTS_ENABLED", False)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

ALERT_ON_TRADE_ENTRY = get_env_bool("ALERT_ON_TRADE_ENTRY", True)
ALERT_ON_TRADE_EXIT = get_env_bool("ALERT_ON_TRADE_EXIT", True)
ALERT_ON_STOP_LOSS = get_env_bool("ALERT_ON_STOP_LOSS", True)
ALERT_ON_PROFIT_TARGET = get_env_bool("ALERT_ON_PROFIT_TARGET", True)
ALERT_ON_ERRORS = get_env_bool("ALERT_ON_ERRORS", True)
ALERT_ON_CONNECTION_LOSS = get_env_bool("ALERT_ON_CONNECTION_LOSS", True)

# ============================================================================
# ADVANCED FEATURES
# ============================================================================

ML_ENABLED = get_env_bool("ML_ENABLED", True)
ML_MODEL_PATH = os.getenv("ML_MODEL_PATH", "./models")
ML_RETRAIN_INTERVAL = get_env_int("ML_RETRAIN_INTERVAL", 7)

ADAPTIVE_LEARNING_ENABLED = get_env_bool("ADAPTIVE_LEARNING_ENABLED", True)
ADAPTIVE_MIN_TRADES = get_env_int("ADAPTIVE_MIN_TRADES", 10)

USE_REAL_GREEKS_DATA = get_env_bool("USE_REAL_GREEKS_DATA", True)
GREEKS_BACKGROUND_REFRESH = get_env_bool("GREEKS_BACKGROUND_REFRESH", True)
GREEKS_REFRESH_INTERVAL = get_env_int("GREEKS_REFRESH_INTERVAL", 5)

SMART_EXIT_ENABLED = get_env_bool("SMART_EXIT_ENABLED", True)
TRAILING_STOP_ENABLED = get_env_bool("TRAILING_STOP_ENABLED", True)
PROFIT_LADDER_ENABLED = get_env_bool("PROFIT_LADDER_ENABLED", True)

# ============================================================================
# PERFORMANCE & OPTIMIZATION
# ============================================================================

WORKER_THREADS = get_env_int("WORKER_THREADS", 4)
MAX_QUEUE_SIZE = get_env_int("MAX_QUEUE_SIZE", 1000)

CACHE_ENABLED = get_env_bool("CACHE_ENABLED", True)
CACHE_TTL = get_env_int("CACHE_TTL", 300)

RATE_LIMIT_ENABLED = get_env_bool("RATE_LIMIT_ENABLED", True)
MAX_REQUESTS_PER_MINUTE = get_env_int("MAX_REQUESTS_PER_MINUTE", 60)

# ============================================================================
# TESTING & DEVELOPMENT
# ============================================================================

TEST_MODE = get_env_bool("TEST_MODE", False)
TEST_CAPITAL = get_env_float("TEST_CAPITAL", 50000)
TEST_DATA_PATH = os.getenv("TEST_DATA_PATH", "./data/test")

BACKTEST_ENABLED = get_env_bool("BACKTEST_ENABLED", False)
BACKTEST_START_DATE = os.getenv("BACKTEST_START_DATE", "2024-01-01")
BACKTEST_END_DATE = os.getenv("BACKTEST_END_DATE", "2024-12-31")

ENABLE_PROFILING = get_env_bool("ENABLE_PROFILING", False)
PROFILE_OUTPUT_DIR = os.getenv("PROFILE_OUTPUT_DIR", "./profiling")

# ============================================================================
# DATABASE ADVANCED (PostgreSQL)
# ============================================================================

DATABASE_HOST = os.getenv("DATABASE_HOST", "localhost")
DATABASE_PORT = get_env_int("DATABASE_PORT", 5432)
DATABASE_NAME = os.getenv("DATABASE_NAME", "angelx_ml")
DATABASE_USER = os.getenv("DATABASE_USER", "angelx")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD", "")
DATABASE_POOL_SIZE = get_env_int("DATABASE_POOL_SIZE", 8)
DATABASE_POOL_RECYCLE = get_env_int("DATABASE_POOL_RECYCLE", 3600)
DATABASE_MAX_OVERFLOW = get_env_int("DATABASE_MAX_OVERFLOW", 10)
DATABASE_POOL_TIMEOUT = get_env_int("DATABASE_POOL_TIMEOUT", 30)
DATABASE_ECHO = get_env_bool("DATABASE_ECHO", False)

# ============================================================================
# API ADVANCED
# ============================================================================

API_WORKERS = get_env_int("API_WORKERS", 4)
API_REQUEST_TIMEOUT = get_env_int("API_REQUEST_TIMEOUT", 60)
API_RATE_LIMIT = get_env_int("API_RATE_LIMIT", 100)
CORS_ENABLED = get_env_bool("CORS_ENABLED", False)
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "")
SERVER_MAX_CONNECTIONS = get_env_int("SERVER_MAX_CONNECTIONS", 1000)
SERVER_BACKLOG = get_env_int("SERVER_BACKLOG", 100)

# ============================================================================
# CACHE ADVANCED
# ============================================================================

CACHE_TYPE = os.getenv("CACHE_TYPE", "memory")  # memory, redis
CACHE_MAX_SIZE = get_env_int("CACHE_MAX_SIZE", 10000)

# ============================================================================
# LOGGING ADVANCED
# ============================================================================

LOG_FILE = os.getenv("LOG_FILE", "./logs/angel-x.log")
LOG_ROTATION_TIME = os.getenv("LOG_ROTATION_TIME", "midnight")
LOG_COMPRESSION = os.getenv("LOG_COMPRESSION", "gzip")  # gzip, bz2, or none

# ============================================================================
# MONITORING & METRICS
# ============================================================================

PROMETHEUS_ENABLED = get_env_bool("PROMETHEUS_ENABLED", False)
PROMETHEUS_PORT = get_env_int("PROMETHEUS_PORT", 9090)
PROMETHEUS_SCRAPE_INTERVAL = get_env_int("PROMETHEUS_SCRAPE_INTERVAL", 15)

GRAFANA_ENABLED = get_env_bool("GRAFANA_ENABLED", False)
GRAFANA_PORT = get_env_int("GRAFANA_PORT", 3000)
GRAFANA_PASSWORD = os.getenv("GRAFANA_PASSWORD", "admin")

METRICS_EXPORT_INTERVAL = get_env_int("METRICS_EXPORT_INTERVAL", 60)
HEALTH_CHECK_INTERVAL = get_env_int("HEALTH_CHECK_INTERVAL", 30)

# ============================================================================
# BACKTESTING ADVANCED
# ============================================================================

BACKTEST_SLIPPAGE_PERCENT = get_env_float("BACKTEST_SLIPPAGE_PERCENT", 0.05)
BACKTEST_COMMISSION_PER_LOT = get_env_float("BACKTEST_COMMISSION_PER_LOT", 20)

# ============================================================================
# FEATURE FLAGS
# ============================================================================

DATA_COLLECTION_ENABLED = get_env_bool("DATA_COLLECTION_ENABLED", True)
LIVE_DATA_ENABLED = get_env_bool("LIVE_DATA_ENABLED", True)
ANALYZER_MODE = get_env_bool("ANALYZER_MODE", False)
DRY_RUN = get_env_bool("DRY_RUN", False)

# ============================================================================
# BACKWARD COMPATIBILITY
# ============================================================================
# Legacy variable names (deprecated, will be removed)

ANGELONE_CLIENT_ID = ANGELONE_CLIENT_CODE  # Deprecated
MINIMUM_LOT_SIZE = MIN_LOT_SIZE  # Deprecated
USE_BROKER_WEBSOCKET = WEBSOCKET_ENABLED  # Deprecated

# ============================================================================
# CONFIGURATION VALIDATION
# ============================================================================

def validate_config() -> Tuple[bool, List[str]]:
    """
    Validate configuration settings.
    Returns (is_valid, list_of_errors)
    """
    errors = []
    
    # Check critical settings in production
    if ENVIRONMENT == "production":
        if PAPER_TRADING:
            errors.append("PAPER_TRADING must be False in production")
        
        if not all([ANGELONE_API_KEY, ANGELONE_CLIENT_CODE, ANGELONE_PASSWORD, ANGELONE_TOTP_SECRET]):
            errors.append("All AngelOne credentials required in production")
        
        if DEBUG:
            errors.append("DEBUG must be False in production")
        
        if SECRET_KEY == "change-me-to-a-strong-random-key-before-production":
            errors.append("SECRET_KEY must be changed for production")
    
    # Validate risk parameters
    if not (0 < RISK_PER_TRADE <= 0.1):
        errors.append(f"RISK_PER_TRADE must be between 0 and 0.1, got {RISK_PER_TRADE}")
    
    if MAX_DAILY_LOSS <= 0:
        errors.append(f"MAX_DAILY_LOSS must be positive, got {MAX_DAILY_LOSS}")
    
    if MAX_DAILY_TRADES <= 0:
        errors.append(f"MAX_DAILY_TRADES must be positive, got {MAX_DAILY_TRADES}")
    
    # Validate underlyings
    if PRIMARY_UNDERLYING not in ALLOWED_UNDERLYING:
        errors.append(f"PRIMARY_UNDERLYING '{PRIMARY_UNDERLYING}' not in ALLOWED_UNDERLYING {ALLOWED_UNDERLYING}")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if LOG_LEVEL not in valid_log_levels:
        errors.append(f"LOG_LEVEL must be one of {valid_log_levels}, got {LOG_LEVEL}")
    
    return (len(errors) == 0, errors)

def print_config_summary():
    """Print configuration summary."""
    print("=" * 80)
    print(f"ANGEL-X Configuration Summary")
    print("=" * 80)
    print(f"Environment:     {ENVIRONMENT.upper()}")
    print(f"Debug Mode:      {DEBUG}")
    print(f"Paper Trading:   {PAPER_TRADING}")
    print(f"Data Source:     {DATA_SOURCE}")
    print(f"Primary Symbol:  {PRIMARY_UNDERLYING}")
    print(f"Dashboard:       {DASHBOARD_HOST}:{DASHBOARD_PORT} ({'Enabled' if DASHBOARD_ENABLED else 'Disabled'})")
    print(f"API Server:      {API_HOST}:{API_PORT} ({'Enabled' if API_ENABLED else 'Disabled'})")
    print(f"Log Level:       {LOG_LEVEL}")
    print(f"Max Daily Loss:  ₹{MAX_DAILY_LOSS:,.0f}")
    print(f"Max Daily Profit: ₹{MAX_DAILY_PROFIT:,.0f}")
    print(f"Risk Per Trade:  {RISK_PER_TRADE*100:.1f}%")
    print("=" * 80)
    
    # Validate and show warnings
    is_valid, errors = validate_config()
    if not is_valid:
        print("\n⚠️  CONFIGURATION WARNINGS:")
        for error in errors:
            print(f"   - {error}")
        print()
    else:
        print("✅ Configuration validated successfully")
        print("=" * 80)

# Run validation on import
if __name__ != "__main__":
    is_valid, errors = validate_config()
    if not is_valid and ENVIRONMENT == "production":
        print("\n❌ CRITICAL: Invalid production configuration!")
        for error in errors:
            print(f"   - {error}")
        print()
        sys.exit(1)

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Environment
    "ENVIRONMENT", "DEBUG", "APP_NAME", "PROJECT_ROOT",
    
    # Broker
    "ANGELONE_API_KEY", "ANGELONE_CLIENT_CODE", "ANGELONE_PASSWORD", "ANGELONE_TOTP_SECRET",
    "ANGELONE_API_TIMEOUT", "ANGELONE_MAX_RETRIES", "ANGELONE_RETRY_DELAY",
    
    # Trading
    "PAPER_TRADING", "PAPER_INITIAL_CAPITAL", "PAPER_SLIPPAGE_PCT",
    
    # Risk
    "RISK_PER_TRADE", "MAX_DAILY_LOSS", "MAX_DAILY_PROFIT", "MAX_DAILY_TRADES",
    "MAX_CONCURRENT_POSITIONS", "POSITION_SIZE_MULTIPLIER", "MIN_LOT_SIZE", "MAX_LOT_SIZE",
    "DEFAULT_STOP_LOSS_PCT", "TRAILING_STOP_LOSS", "TRAILING_STOP_PCT",
    "MAX_NET_DELTA", "MAX_NET_GAMMA", "MAX_DAILY_THETA",
    
    # Market Data
    "DATA_SOURCE", "WEBSOCKET_ENABLED", "WEBSOCKET_RECONNECT_ATTEMPTS",
    "WEBSOCKET_RECONNECT_DELAY", "WEBSOCKET_PING_INTERVAL", "WEBSOCKET_TICK_TIMEOUT",
    "WEBSOCKET_NO_DATA_FALLBACK", "MARKET_DATA_REFRESH", "GREEKS_CALCULATION_INTERVAL",
    "OI_REFRESH_INTERVAL", "DATA_FRESHNESS_TOLERANCE",
    
    # Strategy
    "PRIMARY_UNDERLYING", "ALLOWED_UNDERLYING", "UNDERLYING_EXCHANGE",
    "OPTION_EXPIRY", "ALLOWED_STRIKES_RANGE", "OPTION_PRODUCT",
    "TRADING_SESSION_START", "TRADING_SESSION_END",
    "NO_TRADE_START_TIME", "NO_TRADE_END_TIME", "NO_TRADE_LAST_MINUTES",
    
    # Security
    "SECRET_KEY", "ENCRYPTION_ENABLED", "TRADING_ENABLED", "LIVE_TRADING_CONFIRMATION",
    
    # Dashboard & API
    "DASHBOARD_ENABLED", "DASHBOARD_HOST", "DASHBOARD_PORT", "DASHBOARD_DEBUG",
    "DASHBOARD_VERSION", "DASHBOARD_REFRESH_RATE", "DASHBOARD_THEME",
    "DASHBOARD_CHARTS_ENABLED", "DASHBOARD_EXPORT_ENABLED", "DASHBOARD_ALERTS_ENABLED",
    "API_ENABLED", "API_HOST", "API_PORT", "API_CORS_ENABLED",
    "API_WORKERS", "API_REQUEST_TIMEOUT", "API_RATE_LIMIT",
    "CORS_ENABLED", "CORS_ORIGINS", "SERVER_MAX_CONNECTIONS", "SERVER_BACKLOG",
    
    # Logging
    "LOG_LEVEL", "LOG_TO_CONSOLE", "LOG_TO_FILE", "LOG_DIR",
    "LOG_MAX_BYTES", "LOG_BACKUP_COUNT", "LOG_FORMAT", "LOG_DATE_FORMAT",
    "LOG_FILE", "LOG_ROTATION_TIME", "LOG_COMPRESSION",
    
    # Database
    "DB_ENABLED", "DB_TYPE", "DB_PATH",
    "DATABASE_HOST", "DATABASE_PORT", "DATABASE_NAME", "DATABASE_USER", "DATABASE_PASSWORD",
    "DATABASE_POOL_SIZE", "DATABASE_POOL_RECYCLE", "DATABASE_MAX_OVERFLOW", "DATABASE_POOL_TIMEOUT",
    "DATABASE_ECHO",
    
    # Alerts
    "EMAIL_ALERTS_ENABLED", "SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "ALERT_EMAIL",
    "TELEGRAM_ALERTS_ENABLED", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID",
    "ALERT_ON_TRADE_ENTRY", "ALERT_ON_TRADE_EXIT", "ALERT_ON_STOP_LOSS",
    "ALERT_ON_PROFIT_TARGET", "ALERT_ON_ERRORS", "ALERT_ON_CONNECTION_LOSS",
    
    # Advanced Features
    "ML_ENABLED", "ML_MODEL_PATH", "ML_RETRAIN_INTERVAL",
    "ADAPTIVE_LEARNING_ENABLED", "ADAPTIVE_MIN_TRADES",
    "USE_REAL_GREEKS_DATA", "GREEKS_BACKGROUND_REFRESH", "GREEKS_REFRESH_INTERVAL",
    "SMART_EXIT_ENABLED", "TRAILING_STOP_ENABLED", "PROFIT_LADDER_ENABLED",
    
    # Performance
    "WORKER_THREADS", "MAX_QUEUE_SIZE",
    "CACHE_ENABLED", "CACHE_TTL", "CACHE_TYPE", "CACHE_MAX_SIZE",
    "RATE_LIMIT_ENABLED", "MAX_REQUESTS_PER_MINUTE",
    
    # Testing & Development
    "TEST_MODE", "TEST_CAPITAL", "TEST_DATA_PATH",
    "BACKTEST_ENABLED", "BACKTEST_START_DATE", "BACKTEST_END_DATE",
    "BACKTEST_SLIPPAGE_PERCENT", "BACKTEST_COMMISSION_PER_LOT",
    "ENABLE_PROFILING", "PROFILE_OUTPUT_DIR",
    
    # Monitoring
    "PROMETHEUS_ENABLED", "PROMETHEUS_PORT", "PROMETHEUS_SCRAPE_INTERVAL",
    "GRAFANA_ENABLED", "GRAFANA_PORT", "GRAFANA_PASSWORD",
    "METRICS_EXPORT_INTERVAL", "HEALTH_CHECK_INTERVAL",
    
    # Exports
    "EXPORT_TRADES_CSV", "EXPORT_METRICS_CSV", "CSV_EXPORT_DIR",
    
    # Feature Flags
    "DATA_COLLECTION_ENABLED", "LIVE_DATA_ENABLED", "ANALYZER_MODE", "DRY_RUN",
    
    # Strategy Parameters
    "IV_EXTREMELY_LOW_THRESHOLD", "IV_EXTREMELY_HIGH_THRESHOLD", "IV_SAFE_ZONE",
    "BULLISH_DELTA_MIN", "BEARISH_DELTA_MAX", "NO_TRADE_DELTA_WEAK",
    "IDEAL_DELTA_CALL", "IDEAL_DELTA_PUT", "IDEAL_GAMMA_MIN", "IDEAL_THETA_MAX",
    "MIN_BID_ASK_SPREAD_PCT", "MAX_BID_ASK_SPREAD_PCT", "MIN_OPEN_INTEREST", "MIN_VOLUME",
]
