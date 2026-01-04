"""
Production environment settings
"""

# Debug mode
DEBUG = False

# API settings
API_TIMEOUT = 60
MAX_RETRIES = 5

# Trading parameters
POSITION_SIZE_MULTIPLIER = 1.0
RISK_PER_TRADE = 0.015  # 1.5%

# Data refresh intervals (seconds)
MARKET_DATA_REFRESH = 3
GREEKS_CALCULATION_INTERVAL = 5

# Logging
LOG_LEVEL = 'INFO'
LOG_TO_FILE = True
LOG_TO_CONSOLE = False

# Performance
ENABLE_CACHE = True
CACHE_TTL = 60
