"""
Development environment settings
"""

# Debug mode
DEBUG = True

# API settings
API_TIMEOUT = 30
MAX_RETRIES = 3

# Trading parameters
POSITION_SIZE_MULTIPLIER = 1.0
RISK_PER_TRADE = 0.02  # 2%

# Data refresh intervals (seconds)
MARKET_DATA_REFRESH = 5
GREEKS_CALCULATION_INTERVAL = 10

# Logging
LOG_LEVEL = 'DEBUG'
LOG_TO_FILE = True
LOG_TO_CONSOLE = True
