"""
Prometheus Metrics Exporter
Export system metrics for Prometheus/Grafana monitoring
"""

from typing import Dict, Optional
from datetime import datetime
from flask import Blueprint, jsonify
import logging

logger = logging.getLogger(__name__)


class PrometheusMetrics:
    """Collect and export Prometheus metrics"""

    def __init__(self):
        self.metrics = {}
        self._init_counters()

    def _init_counters(self):
        """Initialize metric counters"""
        self.metrics = {
            "trades_total": 0,
            "trades_winning": 0,
            "trades_losing": 0,
            "pnl_total": 0.0,
            "errors_total": 0,
            "api_requests_total": 0,
            "api_errors_total": 0,
            "broker_reconnects": 0,
            "model_predictions": 0,
        }

    def increment(self, metric: str, value: float = 1.0):
        """Increment metric"""
        if metric in self.metrics:
            self.metrics[metric] += value
        else:
            logger.warning(f"Unknown metric: {metric}")

    def set(self, metric: str, value: float):
        """Set metric value"""
        self.metrics[metric] = value

    def get_text_format(self) -> str:
        """Export metrics in Prometheus text format"""
        lines = [
            "# HELP angelx_system Angel-X Trading System",
            "# TYPE angelx_system gauge",
        ]

        for name, value in self.metrics.items():
            lines.append(f'angelx_{name}{{job="angelx"}} {value}')

        lines.append("")  # Blank line at end
        return "\n".join(lines)

    def get_json_format(self) -> Dict:
        """Export metrics as JSON"""
        return {"timestamp": datetime.now().isoformat(), "metrics": self.metrics}


def create_prometheus_blueprint(metrics: PrometheusMetrics) -> Blueprint:
    """Create Flask blueprint for Prometheus metrics endpoint"""

    bp = Blueprint("prometheus", __name__, url_prefix="/metrics")

    @bp.route("/prometheus", methods=["GET"])
    def prometheus_metrics():
        """Prometheus text format endpoint"""
        return metrics.get_text_format(), 200, {"Content-Type": "text/plain; charset=utf-8"}

    @bp.route("/json", methods=["GET"])
    def metrics_json():
        """JSON format endpoint"""
        return jsonify(metrics.get_json_format()), 200

    return bp


# Global metrics instance
_metrics: Optional[PrometheusMetrics] = None


def get_prometheus_metrics() -> PrometheusMetrics:
    """Get or create global Prometheus metrics"""
    global _metrics
    if _metrics is None:
        _metrics = PrometheusMetrics()
    return _metrics
