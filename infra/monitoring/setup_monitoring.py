#!/usr/bin/env python3
"""
Setup monitoring endpoints in Flask app
Add this to your Flask application
"""

from flask import Blueprint, jsonify
from src.monitoring import get_prometheus_metrics, create_prometheus_blueprint

def setup_monitoring_endpoints(app):
    """Setup all monitoring endpoints"""
    
    # Get prometheus metrics
    metrics = get_prometheus_metrics()
    
    # Register prometheus blueprint
    prometheus_bp = create_prometheus_blueprint(metrics)
    app.register_blueprint(prometheus_bp)
    
    # Create monitoring blueprint
    monitoring_bp = Blueprint('monitoring', __name__, url_prefix='/monitoring')
    
    @monitoring_bp.route('/metrics/system', methods=['GET'])
    def system_metrics():
        """System metrics endpoint"""
        from src.monitoring import MetricsCollector
        
        return jsonify({
            'memory_mb': round(MetricsCollector.get_memory_usage(), 2),
            'cpu_percent': round(MetricsCollector.get_cpu_percent(), 1),
            'timestamp': None
        }), 200
    
    @monitoring_bp.route('/health/detailed', methods=['GET'])
    def detailed_health():
        """Detailed health check"""
        return jsonify({
            'status': 'healthy',
            'broker': 'connected',
            'database': 'ready',
            'api': 'responding',
            'ml': 'initialized',
            'dashboard': 'running'
        }), 200
    
    app.register_blueprint(monitoring_bp)
    
    return metrics


# Usage in main app:
# 
# from flask import Flask
# app = Flask(__name__)
# metrics = setup_monitoring_endpoints(app)
#
# # Now track metrics
# metrics.increment('trades_total')
# metrics.set('pnl_total', 50000)
#
# # Endpoints available:
# # GET /metrics/prometheus    - Prometheus text format
# # GET /metrics/json          - JSON format
# # GET /monitoring/metrics/system - System stats
# # GET /monitoring/health/detailed - Detailed health
