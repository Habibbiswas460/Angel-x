"""
Monitoring API Endpoints
Provides health checks, metrics, and readiness probes for monitoring systems
"""

from flask import Blueprint, jsonify
from app.utils.health_check import (
    get_health_status,
    get_readiness_status,
    get_liveness_status
)

monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitor')

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

# Register blueprint (in your Flask app initialization):
# app.register_blueprint(monitoring_bp)
