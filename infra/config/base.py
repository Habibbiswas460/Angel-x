"""
Base Configuration

All environments inherit from this base configuration.
Override specific settings in environment-specific config files.
"""

import os
from pathlib import Path

# Project root
PROJECT_ROOT = Path(__file__).parent.parent.parent
APP_ROOT = PROJECT_ROOT / "app"
LOGS_ROOT = PROJECT_ROOT / "logs"
DATA_ROOT = PROJECT_ROOT / "data"

# Ensure log directories exist
LOGS_ROOT.mkdir(exist_ok=True)
(LOGS_ROOT / "trades").mkdir(exist_ok=True)
(LOGS_ROOT / "metrics").mkdir(exist_ok=True)
(LOGS_ROOT / "reports").mkdir(exist_ok=True)

# Application settings
DEBUG = False
TESTING = False
ENVIRONMENT = "development"

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_FILE = str(LOGS_ROOT / "angel-x.log")

# Database
DATABASE_ENABLED = True
DATABASE_HOST = os.getenv("DB_HOST", "localhost")
DATABASE_PORT = int(os.getenv("DB_PORT", 5432))
DATABASE_NAME = os.getenv("DB_NAME", "angelx_ml")
DATABASE_USER = os.getenv("DB_USER", "angelx")
# ⚠️ SECURITY: Require explicit password in production
DATABASE_PASSWORD = os.getenv("DB_PASSWORD", "")
if not DATABASE_PASSWORD and os.getenv("ENVIRONMENT") == "production":
    raise ValueError("DB_PASSWORD environment variable must be set for production")

# API
API_HOST = "0.0.0.0"
API_PORT = int(os.getenv("API_PORT", 5000))
API_DEBUG = False
API_WORKERS = 4

# Broker
BROKER_NAME = "AngelOne"
BROKER_API_KEY = os.getenv("BROKER_API_KEY", "")
BROKER_CLIENT_CODE = os.getenv("BROKER_CLIENT_CODE", "")

# Trading
TRADING_ENABLED = False
PAPER_TRADING = True
MAX_DAILY_LOSS_PERCENT = 2.0
MAX_POSITION_SIZE = 100000
MIN_TRADE_DISTANCE = 1.0

# Market
MARKET_SYMBOLS = ["NIFTY", "BANKNIFTY"]
MARKET_EXPIRY = "WEEKLY"
TRADING_HOURS_START = 9 * 60 + 15  # 09:15
TRADING_HOURS_END = 15 * 60 + 30   # 15:30

# Greeks
GREEKS_CACHE_TTL = 60  # seconds
GREEKS_CALC_METHOD = "BLACK_SCHOLES"

# Risk Management
RISK_FREE_RATE = 0.06  # 6% annual
USE_DYNAMIC_RISK_LIMITS = True
ADAPTIVE_LEARNING_ENABLED = True

# Monitoring
METRICS_COLLECTION_ENABLED = True
HEALTH_CHECK_INTERVAL = 60  # seconds
PERFORMANCE_TRACKING_ENABLED = True
