"""Production Configuration"""

import os
from .base import *

ENVIRONMENT = "production"
DEBUG = False
TESTING = False

LOG_LEVEL = "INFO"

# Database (production cluster)
DATABASE_HOST = os.getenv("DB_HOST_PROD", "db-prod.angelx.internal")
DATABASE_NAME = "angelx_ml_prod"
DATABASE_PASSWORD = os.getenv("DB_PASSWORD_PROD", "")

# API
API_DEBUG = False
API_WORKERS = 8

# API settings (legacy)
API_TIMEOUT = 60
MAX_RETRIES = 5

# Trading (ENABLED in production)
TRADING_ENABLED = True
PAPER_TRADING = False

# Trading parameters (legacy)
POSITION_SIZE_MULTIPLIER = 1.0
RISK_PER_TRADE = 0.015  # 1.5%

# Risk limits (stricter for production)
MAX_DAILY_LOSS_PERCENT = 1.0
MAX_POSITION_SIZE = 50000

# Data refresh intervals (seconds)
MARKET_DATA_REFRESH = 3
GREEKS_CALCULATION_INTERVAL = 5

# Logging (legacy)
LOG_TO_FILE = True
LOG_TO_CONSOLE = False

# Performance
ENABLE_CACHE = True
CACHE_TTL = 60

# Monitoring (fully enabled)
METRICS_COLLECTION_ENABLED = True
HEALTH_CHECK_INTERVAL = 30
PERFORMANCE_TRACKING_ENABLED = True
