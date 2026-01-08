"""
Angel-X Dashboard Module
Real-time monitoring and performance tracking
"""

from src.dashboard.dashboard_aggregator import DashboardAggregator
from src.dashboard.dashboard_backend import DashboardDataProvider, start_dashboard

__all__ = [
    "DashboardAggregator",
    "DashboardDataProvider",
    "start_dashboard"
]
