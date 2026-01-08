"""Development Configuration"""

from .base import *

ENVIRONMENT = "development"
DEBUG = True
TESTING = False

LOG_LEVEL = "DEBUG"

# Database (local development)
DATABASE_HOST = "localhost"
DATABASE_NAME = "angelx_ml_dev"

# API
API_DEBUG = True
API_WORKERS = 1

# API settings (legacy - kept for compatibility)
API_TIMEOUT = 30
MAX_RETRIES = 3

# Trading parameters
POSITION_SIZE_MULTIPLIER = 1.0
RISK_PER_TRADE = 0.02  # 2%
TRADING_ENABLED = False
PAPER_TRADING = True

# Data refresh intervals (seconds)
MARKET_DATA_REFRESH = 5
GREEKS_CALCULATION_INTERVAL = 10

# Logging (legacy)
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# Monitoring
METRICS_COLLECTION_ENABLED = False
PERFORMANCE_TRACKING_ENABLED = False
