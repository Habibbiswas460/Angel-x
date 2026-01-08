"""
Testing environment settings
"""

# Debug mode
DEBUG = True

# API settings
API_TIMEOUT = 10
MAX_RETRIES = 2

# Trading parameters (reduced for testing)
POSITION_SIZE_MULTIPLIER = 0.1  # 10% of normal
RISK_PER_TRADE = 0.01  # 1%

# Data refresh intervals (seconds)
MARKET_DATA_REFRESH = 60
GREEKS_CALCULATION_INTERVAL = 30

# Logging
LOG_LEVEL = 'DEBUG'
LOG_TO_FILE = True
LOG_TO_CONSOLE = True

# Testing flags
MOCK_API_CALLS = True
PAPER_TRADING = True
