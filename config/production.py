"""
Production environment settings

⚠️ DEPRECATED: This file is deprecated!
================================================================================
PLEASE USE .env FILE INSTEAD!

This file is kept for backward compatibility only.
All configuration should now be done in the .env file.

Migration Guide:
1. Copy .env.production to .env
2. Add your credentials and production settings to .env
3. Delete or ignore this file
4. Use: from config import DEBUG, API_TIMEOUT, etc.

Benefits of using .env:
✅ All settings in one place
✅ Easy to manage different environments
✅ Secure (credentials not in source code)
✅ Better organization and documentation
✅ Production-ready with validation

For more help:
📖 Read docs/CONFIGURATION.md
📚 Check .env.production for all production settings
📚 Check .env.example for full parameter list

SECURITY WARNING:
🔒 Production configuration with .env.production includes:
   - DATABASE_URL for PostgreSQL
   - PROMETHEUS and GRAFANA enabled
   - EMAIL and TELEGRAM alerts
   - Strict risk management
   - Advanced monitoring

================================================================================
"""

import warnings
import sys

warnings.warn(
    "config/production.py is deprecated! Use .env file instead.\n"
    "Please read: docs/CONFIGURATION.md",
    DeprecationWarning,
    stacklevel=2
)

print("⚠️  WARNING: config/production.py is DEPRECATED!")
print("    Use .env file instead. See docs/CONFIGURATION.md for details.")
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
