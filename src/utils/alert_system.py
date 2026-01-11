"""
Alert System - DEPRECATED (consolidation wrapper)

This module is now consolidated into app/services/monitoring/alert_system.py
All imports have been redirected to maintain backward compatibility.
"""

# Consolidation wrapper: Forward all imports to canonical location
from app.services.monitoring.alert_system import (
    AlertSeverity,
    AlertType,
    Alert,
    AlertHandler,
    LogAlertHandler,
    WebhookAlertHandler,
    EmailAlertHandler,
    AlertSystem,
)

__all__ = [
    'AlertSeverity',
    'AlertType',
    'Alert',
    'AlertHandler',
    'LogAlertHandler',
    'WebhookAlertHandler',
    'EmailAlertHandler',
    'AlertSystem',
]
