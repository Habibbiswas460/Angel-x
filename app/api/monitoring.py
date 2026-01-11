"""
Monitoring API Endpoints
Provides health checks, metrics, and readiness probes for monitoring systems
Includes Prometheus metrics export for observability
"""

from flask import Blueprint, jsonify
from app.utils.health_check import (
    get_health_status,
    get_readiness_status,
    get_liveness_status
)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitor')


def _generate_prometheus_metrics() -> str:
    """Generate Prometheus-format metrics"""
    try:
        from app.services.monitoring.alert_system import get_alert_system
        alert_system = get_alert_system()
        stats = alert_system.get_stats()
        
        metrics = [
            '# HELP angel_x_alerts_sent Total alerts sent',
            '# TYPE angel_x_alerts_sent counter',
            f'angel_x_alerts_sent {stats.get("alerts_sent", 0)}',
            '',
            '# HELP angel_x_alerts_failed Total alerts failed',
            '# TYPE angel_x_alerts_failed counter',
            f'angel_x_alerts_failed {stats.get("alerts_failed", 0)}',
            '',
            '# HELP angel_x_alert_queue_size Current alert queue size',
            '# TYPE angel_x_alert_queue_size gauge',
            f'angel_x_alert_queue_size {stats.get("queue_size", 0)}',
            '',
            '# HELP angel_x_alert_history_size Alert history size',
            '# TYPE angel_x_alert_history_size gauge',
            f'angel_x_alert_history_size {stats.get("history_size", 0)}',
            '',
        ]
        
        # Add system health metrics
        health = get_health_status()
        metrics.append('# HELP angel_x_system_healthy System health status')
        metrics.append('# TYPE angel_x_system_healthy gauge')
        metrics.append(f'angel_x_system_healthy {1 if health.get("status") == "healthy" else 0}')
        metrics.append('')
        
        return '\n'.join(metrics)
    except Exception as e:
        print(f"Error generating Prometheus metrics: {e}")
        return ""


@monitoring_bp.route('/health', methods=['GET'])
def health():
    """Comprehensive health check endpoint"""
    return jsonify(get_health_status()), 200


@monitoring_bp.route('/ready', methods=['GET'])
def readiness():
    """Readiness probe for Kubernetes/container orchestration"""
    status = get_readiness_status()
    http_status = 200 if status['ready'] else 503
    return jsonify(status), http_status


@monitoring_bp.route('/live', methods=['GET'])
def liveness():
    """Liveness probe for Kubernetes/container orchestration"""
    return jsonify(get_liveness_status()), 200


@monitoring_bp.route('/ping', methods=['GET'])
def ping():
    """Simple ping endpoint"""
    return jsonify({'status': 'pong'}), 200


@monitoring_bp.route('/metrics', methods=['GET'])
def metrics():
    """Prometheus metrics endpoint"""
    prometheus_metrics = _generate_prometheus_metrics()
    return prometheus_metrics, 200, {'Content-Type': 'text/plain'}


@monitoring_bp.route('/alerts', methods=['GET'])
def alerts():
    """Get alert history and stats"""
    try:
        from app.services.monitoring.alert_system import get_alert_system
        alert_system = get_alert_system()
        
        return jsonify({
            'stats': alert_system.get_stats(),
            'recent_alerts': alert_system.get_history(limit=50)
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@monitoring_bp.route('/alert-stats', methods=['GET'])
def alert_stats():
    """Get alert system statistics"""
    try:
        from app.services.monitoring.alert_system import get_alert_system
        alert_system = get_alert_system()
        return jsonify(alert_system.get_stats()), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Register blueprint (in your Flask app initialization):
# app.register_blueprint(monitoring_bp)

