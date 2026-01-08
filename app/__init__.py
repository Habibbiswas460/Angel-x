"""
Angel-X Trading System

Ultra-professional enterprise trading platform for options trading with
adaptive learning, market bias detection, and intelligent risk management.

Structure:
  - domains/: Business logic domains (market, options, trading, learning)
  - services/: Core services layer (broker, data, database, monitoring)
  - api/: REST API layer
  - web/: Web UI assets
  - utils/: Utility modules
"""

__version__ = "10.0.0"
__author__ = "Angel-X Team"
__license__ = "MIT"

import logging

logger = logging.getLogger(__name__)

# Version info
VERSION_INFO = {
    "major": 10,
    "minor": 0,
    "patch": 0,
    "phase": "Production",
    "architecture": "Ultra-Enterprise",
}
