"""
Consolidated Application Utilities

Central hub for all application utilities. This module consolidates
utilities from both app/utils and src/utils for backward compatibility.

CONSOLIDATION STRATEGY:
- app/utils/ = canonical location for all utilities
- src/utils/ = imports wrapped from app/utils for backward compatibility
- All new imports should use app.utils

STRUCTURE:
- decorators: Common decorators (retry, caching, etc.)
- exceptions: Custom exception classes
- logger: Centralized logging system
- validators: Data validation utilities
- health_check: System health checks
- prometheus_metrics: Metric collection
- helpers: General helper functions
"""

# Core utilities
from app.utils.logger import StrategyLogger, logger

__all__ = [
    'StrategyLogger',
    'logger',
]
