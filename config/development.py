"""
Development environment settings

⚠️ DEPRECATED: This file is deprecated!
================================================================================
PLEASE USE .env FILE INSTEAD!

This file is kept for backward compatibility only.
All configuration should now be done in the .env file.

Migration Guide:
1. Copy .env.example to .env
2. Add your settings to .env
3. Delete or ignore this file
4. Use: from config import DEBUG, API_TIMEOUT, etc.

Benefits of using .env:
✅ All settings in one place
✅ Easy to manage different environments (.env.development, .env.production)
✅ Secure (credentials not in source code)
✅ Bilingual comments (English + Bengali/Banglish)
✅ Beginner-friendly documentation

For more help:
📖 Read docs/CONFIGURATION.md
📚 Check .env.example for all available settings
================================================================================
"""

import warnings
import sys

warnings.warn(
    "config/development.py is deprecated! Use .env file instead.\n"
    "Please read: docs/CONFIGURATION.md",
    DeprecationWarning,
    stacklevel=2
)

print("⚠️  WARNING: config/development.py is DEPRECATED!")
print("    Use .env file instead. See docs/CONFIGURATION.md for details.")
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
