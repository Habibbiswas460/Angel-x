"""System monitoring and metrics collection"""

from .health_monitor import HealthMonitor, AlertConfig, TelegramAlerter, MetricsCollector, get_monitor

# Optional imports for Flask
try:
    from .prometheus import PrometheusMetrics, create_prometheus_blueprint, get_prometheus_metrics
except ImportError:
    # Flask not installed; skip Prometheus blueprint setup
    PrometheusMetrics = None
    create_prometheus_blueprint = None
    get_prometheus_metrics = None

__all__ = [
    'HealthMonitor',
    'AlertConfig',
    'TelegramAlerter',
    'MetricsCollector',
    'PrometheusMetrics',
    'create_prometheus_blueprint',
    'get_monitor',
    'get_prometheus_metrics',
]
