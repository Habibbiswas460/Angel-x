"""
Utility modules - Consolidation Layer

CONSOLIDATION STATUS:
This module provides backward-compatible imports from the consolidated app/utils
and app/services locations.

CANONICAL LOCATIONS:
- Logger: app.utils.logger
- Alert System: app.services.monitoring.alert_system
- Other utils: Unique implementations kept in src/utils

IMPORT STRATEGY:
1. Consolidated modules route to canonical app/ locations
2. Unique src/utils modules are imported directly
3. All legacy code continues to work without changes
"""

# Re-export consolidated utilities for backward compatibility
from app.utils.logger import StrategyLogger, logger
from app.services.monitoring.alert_system import (
    AlertSystem,
    AlertSeverity,
    AlertType,
    Alert,
    AlertHandler,
    LogAlertHandler,
    WebhookAlertHandler,
    EmailAlertHandler,
)

__all__ = [
    "StrategyLogger",
    "logger",
    "AlertSystem",
    "AlertSeverity",
    "AlertType",
    "Alert",
    "AlertHandler",
    "LogAlertHandler",
    "WebhookAlertHandler",
    "EmailAlertHandler",
]
