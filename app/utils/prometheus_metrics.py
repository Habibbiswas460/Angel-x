"""
Prometheus Metrics for Angel-X Trading System
Exposes trading metrics, system metrics, and application health
"""

from prometheus_client import Counter, Gauge, Histogram, start_http_server
import time

# ============================================================================
# Application Metrics
# ============================================================================

# API Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'path', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'path']
)

# Trading Metrics
trades_executed_total = Counter(
    'trades_executed_total',
    'Total trades executed',
    ['strategy', 'instrument']
)

trades_won_total = Counter(
    'trades_won_total',
    'Total winning trades',
    ['strategy']
)

signals_generated_total = Counter(
    'signals_generated_total',
    'Total signals generated',
    ['signal_type', 'domain']
)

active_positions_count = Gauge(
    'active_positions_count',
    'Number of active trading positions',
    ['instrument_type']
)

trading_profit_loss_cumulative = Gauge(
    'trading_profit_loss_cumulative',
    'Cumulative trading profit/loss',
    ['strategy']
)

trading_profit_loss_daily = Gauge(
    'trading_profit_loss_daily',
    'Daily trading profit/loss',
    ['strategy']
)

risk_exposure_ratio = Gauge(
    'risk_exposure_ratio',
    'Current risk exposure ratio (0-1)',
    ['strategy']
)

# ============================================================================
# Greeks Metrics
# ============================================================================

greeks_calculation_duration_seconds = Histogram(
    'greeks_calculation_duration_seconds',
    'Greeks calculation duration in seconds',
    ['greeks_type']
)

greeks_calculation_errors_total = Counter(
    'greeks_calculation_errors_total',
    'Total Greeks calculation errors',
    ['greeks_type', 'error_type']
)

option_chain_update_lag_seconds = Gauge(
    'option_chain_update_lag_seconds',
    'Option chain data update lag in seconds'
)

# ============================================================================
# Market Data Metrics
# ============================================================================

market_data_last_update_timestamp = Gauge(
    'market_data_last_update_timestamp',
    'Timestamp of last market data update',
    ['data_source']
)

market_data_updates_total = Counter(
    'market_data_updates_total',
    'Total market data updates received',
    ['data_source', 'symbol']
)

market_data_errors_total = Counter(
    'market_data_errors_total',
    'Total market data errors',
    ['data_source', 'error_type']
)

# ============================================================================
# Database Metrics
# ============================================================================

db_connection_pool_available = Gauge(
    'db_connection_pool_available',
    'Available database connections in pool'
)

db_query_duration_seconds = Histogram(
    'db_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

db_query_errors_total = Counter(
    'db_query_errors_total',
    'Total database query errors',
    ['operation', 'error_type']
)

db_transaction_duration_seconds = Histogram(
    'db_transaction_duration_seconds',
    'Database transaction duration in seconds'
)

# ============================================================================
# Broker Integration Metrics
# ============================================================================

broker_connection_status = Gauge(
    'broker_connection_status',
    'Broker connection status (1=connected, 0=disconnected)',
    ['broker']
)

broker_order_latency_seconds = Histogram(
    'broker_order_latency_seconds',
    'Broker order execution latency in seconds'
)

broker_orders_placed_total = Counter(
    'broker_orders_placed_total',
    'Total orders placed with broker',
    ['order_type', 'instrument']
)

broker_orders_rejected_total = Counter(
    'broker_orders_rejected_total',
    'Total orders rejected by broker',
    ['reason']
)

broker_fill_rate = Gauge(
    'broker_fill_rate',
    'Order fill rate (0-1)',
    ['instrument']
)

# ============================================================================
# Learning System Metrics
# ============================================================================

learning_model_accuracy = Gauge(
    'learning_model_accuracy',
    'Learning model accuracy (0-1)',
    ['model_name']
)

learning_model_training_duration_seconds = Histogram(
    'learning_model_training_duration_seconds',
    'Model training duration in seconds',
    ['model_name']
)

learning_feedback_processed_total = Counter(
    'learning_feedback_processed_total',
    'Total feedback samples processed',
    ['model_name']
)

learning_feedback_queue_size = Gauge(
    'learning_feedback_queue_size',
    'Current learning feedback queue size'
)

# ============================================================================
# System Metrics (using prometheus_client built-ins)
# ============================================================================

from prometheus_client import (
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
    REGISTRY
)

def get_metrics_registry():
    """Get the default Prometheus registry"""
    return REGISTRY

def start_metrics_server(port=8000):
    """Start Prometheus metrics HTTP server"""
    try:
        start_http_server(port)
        print(f"Prometheus metrics server started on port {port}")
        return True
    except Exception as e:
        print(f"Error starting metrics server: {e}")
        return False

def record_http_request(method, path, status, duration):
    """Record HTTP request metrics"""
    http_requests_total.labels(method=method, path=path, status=status).inc()
    http_request_duration_seconds.labels(method=method, path=path).observe(duration)

def record_trade_executed(strategy, instrument, is_winning):
    """Record trade execution"""
    trades_executed_total.labels(strategy=strategy, instrument=instrument).inc()
    if is_winning:
        trades_won_total.labels(strategy=strategy).inc()

def record_signal_generated(signal_type, domain):
    """Record signal generation"""
    signals_generated_total.labels(signal_type=signal_type, domain=domain).inc()

def record_greeks_calculation(greeks_type, duration, error=None):
    """Record Greeks calculation"""
    greeks_calculation_duration_seconds.labels(greeks_type=greeks_type).observe(duration)
    if error:
        greeks_calculation_errors_total.labels(
            greeks_type=greeks_type,
            error_type=type(error).__name__
        ).inc()

def record_db_query(operation, table, duration, error=None):
    """Record database query"""
    db_query_duration_seconds.labels(operation=operation, table=table).observe(duration)
    if error:
        db_query_errors_total.labels(
            operation=operation,
            error_type=type(error).__name__
        ).inc()

def set_broker_connection_status(broker, connected):
    """Set broker connection status"""
    broker_connection_status.labels(broker=broker).set(1 if connected else 0)

def record_order_placed(order_type, instrument):
    """Record order placement"""
    broker_orders_placed_total.labels(order_type=order_type, instrument=instrument).inc()

def update_learning_accuracy(model_name, accuracy):
    """Update learning model accuracy"""
    learning_model_accuracy.labels(model_name=model_name).set(accuracy)
