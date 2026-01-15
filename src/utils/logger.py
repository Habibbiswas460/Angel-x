"""
Logging module - DEPRECATED (consolidation wrapper)

This module is now consolidated into app/utils/logger.py
All imports have been redirected to maintain backward compatibility.
"""

# Consolidation wrapper: Forward all imports to canonical location
from app.utils.logger import StrategyLogger, logger

__all__ = ["StrategyLogger", "logger"]
