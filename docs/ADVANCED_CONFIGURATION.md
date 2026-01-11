# Advanced Configuration Guide

Comprehensive guide to configure Angel-X for production trading, performance optimization, and risk management.

## Table of Contents
1. [Performance Tuning](#performance-tuning)
2. [Risk Management](#risk-management)
3. [Broker Configuration](#broker-configuration)
4. [Data Management](#data-management)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Database Optimization](#database-optimization)
7. [Caching Strategy](#caching-strategy)

---

## Performance Tuning

### Thread Pool Configuration

**File:** `config/config.py`

```python
# Thread pool for concurrent operations
THREAD_POOL_SIZE = 16  # Number of worker threads
MAX_QUEUE_SIZE = 1000  # Maximum queued tasks
THREAD_TIMEOUT_SECONDS = 30

# Optimal values based on CPU cores:
# - Single core: 4-8
# - Quad core: 16-32
# - Octa core: 32-64
```

**Performance Impact:**
- Larger pool = lower latency, higher memory
- Smaller pool = lower memory, potential bottlenecks
- Rule of thumb: 2-4x CPU cores

### Order Processing Optimization

```python
# Batch order processing
ORDER_BATCH_SIZE = 50  # Process orders in batches
ORDER_BATCH_TIMEOUT_MS = 100  # Wait up to 100ms to fill batch

# Order queue
ORDER_QUEUE_SIZE = 10000  # Maximum pending orders
ORDER_PROCESSING_WORKERS = 8  # Parallel order processors

# Expected performance:
# - 50 orders/batch * 8 workers = 400+ orders/second
# - Sub-100ms order processing latency
```

### Market Data Optimization

```python
# Real-time data streaming
MARKET_DATA_BUFFER_SIZE = 5000  # Ticks to buffer
MARKET_DATA_FLUSH_INTERVAL_MS = 100  # Flush buffer every 100ms
PRICE_UPDATE_BATCH_SIZE = 100  # Batch price updates

# Greeks calculation
GREEKS_CALCULATION_BATCH = 50  # Calculate 50 options' Greeks at once
GREEKS_CACHE_TTL_SECONDS = 30  # Cache Greeks for 30 seconds
PARALLEL_GREEK_WORKERS = 4  # Parallel Greeks calculation threads
```

### Database Query Optimization

```python
# Connection pooling
DB_POOL_SIZE = 20  # Minimum connections
DB_MAX_POOL_SIZE = 40  # Maximum connections
DB_POOL_TIMEOUT_SECONDS = 5  # Connection timeout

# Query optimization
DB_STATEMENT_CACHE_SIZE = 500  # Prepared statement cache
DB_QUERY_TIMEOUT_SECONDS = 30  # Max query execution time
```

**Connection Pool Configuration Example:**
```python
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    'postgresql://user:password@localhost/trading_db',
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=20,
    pool_timeout=5,
    pool_recycle=3600,  # Recycle connections after 1 hour
    echo=False  # Set to True for SQL query logging
)
```

### Redis Caching Optimization

```python
# Redis connection
REDIS_HOST = 'localhost'
REDIS_PORT = 6379
REDIS_DB = 0
REDIS_PASSWORD = None

# Connection pool
REDIS_POOL_SIZE = 50
REDIS_SOCKET_CONNECT_TIMEOUT = 5
REDIS_SOCKET_TIMEOUT = 5

# Cache TTLs
CACHE_TTL_MARKET_DATA = 60  # 1 minute
CACHE_TTL_POSITION_DATA = 30  # 30 seconds
CACHE_TTL_GREEKS = 30  # 30 seconds
CACHE_TTL_PORTFOLIO = 10  # 10 seconds

# Cache warming
WARM_CACHE_ON_STARTUP = True
CACHE_PRELOAD_SYMBOLS = [
    'NIFTY_25JAN26_19000CE',
    'BANKNIFTY_25JAN26_47000CE',
    # Add frequently traded symbols
]
```

**Cache Invalidation Strategy:**
```python
# Automatic cache invalidation
CACHE_INVALIDATION_RULES = {
    'POSITION_CHANGE': ['position_data', 'portfolio_greeks'],
    'PRICE_CHANGE': ['market_data', 'greeks', 'pnl'],
    'ORDER_FILLED': ['positions', 'cash_balance', 'margin'],
}
```

---

## Risk Management

### Position Sizing

```python
# Capital allocation
CAPITAL = 100000  # Starting capital in rupees
DAILY_LOSS_LIMIT = 0.02 * CAPITAL  # ₹2,000 (2% of capital)
MAX_POSITION_SIZE = 150  # Maximum lot size per trade
MAX_CONCURRENT_POSITIONS = 5  # Maximum simultaneous positions

# Position sizing calculation
POSITION_SIZE_METHOD = 'kelly'  # 'fixed', 'kelly', or 'volatility'

# Fixed method
FIXED_POSITION_SIZE = 75

# Kelly criterion method (optimal but risky)
KELLY_FRACTION = 0.25  # Use 25% of Kelly (1/4 Kelly for safety)
KELLY_WIN_RATE = 0.65  # Expected win rate
KELLY_AVG_WIN = 400  # Average winning trade (₹)
KELLY_AVG_LOSS = 300  # Average losing trade (₹)

# Volatility-based method
MIN_POSITION_SIZE = 25
MAX_POSITION_SIZE = 150
BASE_POSITION_SIZE = 75
VOLATILITY_MULTIPLIER = 1.5
```

**Position Sizing Formula:**
```python
# Kelly criterion: f* = (bp - q) / b
# where b = odds, p = win probability, q = loss probability
# 
# Recommended: Use 25% Kelly for safer trading
# f = 0.25 * f*

kelly_fraction = 0.25  # 1/4 Kelly
position_size = kelly_fraction * base_size * volatility_factor
position_size = max(MIN_POSITION_SIZE, min(MAX_POSITION_SIZE, position_size))
```

### Drawdown Management

```python
# Maximum drawdown limits
MAX_DAILY_DRAWDOWN_PERCENT = 5.0  # Stop trading if 5% drawdown
MAX_WEEKLY_DRAWDOWN_PERCENT = 10.0  # Stop trading if 10% weekly drawdown
MAX_MONTHLY_DRAWDOWN_PERCENT = 15.0  # Stop trading if 15% monthly drawdown

# Drawdown recovery
DRAWDOWN_RECOVERY_PERIOD_DAYS = 7  # Wait 7 days to recover from max drawdown
SCALE_DOWN_AFTER_LOSS = 0.75  # Reduce position size to 75% after loss
SCALE_UP_AFTER_WINS = 1.1  # Increase position size to 110% after wins

# Max consecutive losses
MAX_CONSECUTIVE_LOSSES = 5  # Stop after 5 consecutive losses
CONSECUTIVE_LOSS_RECOVERY_MINUTES = 60  # Wait 60 minutes before resuming
```

### Stop-Loss Management

```python
# Stop-loss configuration
STOP_LOSS_TYPE = 'percent'  # 'percent', 'fixed', or 'atr'
STOP_LOSS_PERCENT = 2.0  # 2% stop loss
STOP_LOSS_FIXED_AMOUNT = 250  # ₹250 fixed stop loss
STOP_LOSS_ATR_MULTIPLIER = 1.5  # 1.5x ATR stop loss

# Trailing stop loss
TRAILING_STOP_ENABLED = True
TRAILING_STOP_PERCENT = 1.5  # Trail by 1.5%
TRAILING_STOP_ACTIVATION_PERCENT = 2.0  # Activate after 2% profit

# Time-based stop loss
TIME_STOP_ENABLED = True
TIME_STOP_MINUTES = 120  # Exit position after 2 hours
```

### Risk Per Trade

```python
# Risk per trade
RISK_PER_TRADE_PERCENT = 1.0  # Risk 1% per trade
REWARD_RISK_RATIO = 2.5  # Target 2.5:1 reward:risk

# Margin requirements
INITIAL_MARGIN_PERCENT = 15.0  # 15% for options
MAINTENANCE_MARGIN_PERCENT = 10.0  # 10% maintenance
MARGIN_CALL_ALERT_PERCENT = 75.0  # Alert at 75% margin usage
```

---

## Broker Configuration

### SmartAPI Configuration

```python
# Angel One (SmartAPI) broker settings
BROKER_NAME = 'ANGEL_ONE'
BROKER_API_KEY = 'your_api_key'
BROKER_ACCESS_TOKEN = 'your_access_token'
BROKER_FEED_TOKEN = 'your_feed_token'
BROKER_CLIENT_CODE = 'your_client_code'

# API endpoints
SMARTAPI_BASE_URL = 'https://apiconnect.angelbroking.com'
SMARTAPI_FEED_URL = 'wss://feedapi.angelbroking.com/socket/stream'

# Connection settings
API_TIMEOUT_SECONDS = 30
API_RETRY_ATTEMPTS = 3
API_RETRY_DELAY_SECONDS = 2
WEBSOCKET_TIMEOUT_SECONDS = 60
WEBSOCKET_RECONNECT_DELAY_SECONDS = 5
```

### Paper Trading Simulation

```python
# Paper trading parameters
PAPER_TRADING_ENABLED = True  # Use paper trading engine

# Slippage simulation
BACKTEST_SLIPPAGE_PERCENT = 0.05  # 0.05% slippage on orders
SLIPPAGE_DIRECTION = 'both'  # 'buy', 'sell', or 'both'

# Market impact
MARKET_IMPACT_ENABLED = True
MARKET_IMPACT_PERCENT = 0.01  # 0.01% per ₹1M traded

# Execution delays
MARKET_ORDER_EXECUTION_DELAY_MS = 50  # Simulate 50ms delay
LIMIT_ORDER_ACCEPTANCE_RATE = 0.95  # 95% of limit orders filled

# Realistic market conditions
SIMULATE_GAPS = True  # Simulate gap moves
SIMULATE_HALTS = True  # Simulate trading halts
SIMULATE_LIQUIDITY_ISSUES = False  # Simulate illiquid conditions
```

### Order Management

```python
# Order settings
ORDER_TYPE_DEFAULT = 'MARKET'  # 'MARKET' or 'LIMIT'
ORDER_TIME_IN_FORCE = 'DAY'  # 'DAY', 'IOC', or 'GTD'
ORDER_VALIDITY_DAYS = 5  # Days valid for GTD orders

# Order validation
VALIDATE_ORDERS_BEFORE_SUBMIT = True
CHECK_MARGIN_AVAILABILITY = True
CHECK_POSITION_LIMITS = True

# Order cancellation
AUTO_CANCEL_UNFILLED_ORDERS_MINUTES = 15  # Cancel orders unfilled for 15 min
PARTIAL_FILL_HANDLING = 'accept'  # 'accept' or 'cancel_remainder'
```

---

## Data Management

### Data Retention

```python
# Historical data retention
RETAIN_TICK_DATA_DAYS = 30  # Keep tick data for 30 days
RETAIN_TRADE_DATA_DAYS = 365  # Keep trade data for 1 year
RETAIN_ALERT_LOGS_DAYS = 90  # Keep alerts for 90 days

# Data archival
ARCHIVE_OLD_DATA = True
ARCHIVE_DESTINATION = 's3://angel-x-backup/archive/'  # S3 bucket
COMPRESS_ARCHIVED_DATA = True  # Use gzip compression
```

### Data Export

```python
# Export settings
EXPORT_DAILY_REPORT = True
EXPORT_FORMAT = 'csv'  # 'csv', 'json', or 'excel'
EXPORT_SCHEDULE = '17:00'  # 5 PM daily
EXPORT_DESTINATION = '/data/exports/'

# Report contents
EXPORT_TRADES = True
EXPORT_POSITIONS = True
EXPORT_PERFORMANCE_METRICS = True
EXPORT_RISK_ANALYTICS = True
```

---

## Monitoring & Alerts

### Alert Configuration

```python
# Alert types and handlers
ALERTS_ENABLED = True

ALERT_HANDLERS = {
    'log': {
        'enabled': True,
        'level': 'INFO'
    },
    'webhook': {
        'enabled': True,
        'url': 'https://your-domain.com/alerts',
        'timeout_seconds': 30,
        'retry_attempts': 3
    },
    'email': {
        'enabled': True,
        'from': 'alerts@angel-x.com',
        'to': ['trader@example.com'],
        'smtp_server': 'smtp.gmail.com',
        'smtp_port': 587,
        'rate_limit': 10  # Max 10 emails per hour
    }
}

# Alert types
ALERT_ON_TRADE_ENTRY = True
ALERT_ON_TRADE_EXIT = True
ALERT_ON_POSITION_CHANGE = True
ALERT_ON_LOSS_LIMIT_HIT = True
ALERT_ON_MARGIN_CALL = True
ALERT_ON_SYSTEM_ERROR = True
ALERT_ON_BROKER_DISCONNECT = True

# Alert thresholds
ALERT_DRAWDOWN_THRESHOLD_PERCENT = 2.0  # Alert at 2% drawdown
ALERT_MARGIN_USAGE_THRESHOLD_PERCENT = 80.0  # Alert at 80% margin
ALERT_DAILY_LOSS_THRESHOLD_PERCENT = 50.0  # Alert at 50% of daily loss limit
```

### Monitoring Metrics

```python
# Metrics collection
METRICS_ENABLED = True
METRICS_COLLECTION_INTERVAL_SECONDS = 60

# Prometheus metrics
PROMETHEUS_ENABLED = True
PROMETHEUS_PORT = 8000
PROMETHEUS_ENDPOINT = '/metrics'

# Tracked metrics
TRACK_ORDER_LATENCY = True
TRACK_DATA_LAG = True
TRACK_GREEK_CALCULATION_TIME = True
TRACK_POSITION_PNL_REAL_TIME = True
TRACK_API_RESPONSE_TIMES = True

# Metric retention
METRICS_RETENTION_DAYS = 30
METRICS_AGGREGATION_INTERVAL = 300  # Aggregate every 5 minutes
```

### Health Checks

```python
# Health check configuration
HEALTH_CHECK_INTERVAL_SECONDS = 30

# Dependency checks
CHECK_DATABASE_HEALTH = True
CHECK_REDIS_HEALTH = True
CHECK_BROKER_CONNECTION = True
CHECK_API_CONNECTIVITY = True

# Health check timeouts
DATABASE_HEALTH_CHECK_TIMEOUT_SECONDS = 5
REDIS_HEALTH_CHECK_TIMEOUT_SECONDS = 2
BROKER_HEALTH_CHECK_TIMEOUT_SECONDS = 10

# Health thresholds
DISK_SPACE_WARNING_PERCENT = 80
MEMORY_USAGE_WARNING_PERCENT = 85
CPU_USAGE_WARNING_PERCENT = 90
```

---

## Database Optimization

### Connection Management

```python
# PostgreSQL connection
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'angel_x_trading'
DB_USER = 'trader'
DB_PASSWORD = 'secure_password'

# Connection tuning
SQLALCHEMY_ECHO = False  # Set to True for query logging
SQLALCHEMY_RECORD_QUERIES = False
DATABASE_QUERY_TIMEOUT = 30
```

### Index Strategy

```sql
-- Essential indexes for performance

-- Trade execution queries
CREATE INDEX idx_trades_date ON trades(created_at DESC);
CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_user ON trades(user_id);
CREATE INDEX idx_trades_status ON trades(status);

-- Position queries
CREATE INDEX idx_positions_active ON positions(user_id, status);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_entry_time ON positions(entry_time DESC);

-- Alert queries
CREATE INDEX idx_alerts_timestamp ON alerts(timestamp DESC);
CREATE INDEX idx_alerts_type ON alerts(alert_type);
CREATE INDEX idx_alerts_status ON alerts(status);

-- Greeks cache
CREATE INDEX idx_greeks_symbol_time ON greeks_snapshot(symbol, snapshot_time DESC);
CREATE INDEX idx_greeks_recent ON greeks_snapshot(snapshot_time DESC) WHERE snapshot_time > NOW() - INTERVAL '1 hour';

-- Market data
CREATE INDEX idx_ticks_symbol_time ON ticks(symbol, tick_time DESC);
CREATE INDEX idx_ticks_recent ON ticks(tick_time DESC) WHERE tick_time > NOW() - INTERVAL '1 day';
```

### Query Optimization

```python
# Common query patterns

# 1. Get active positions with Greeks (optimized)
@cache.cached(timeout=10)
def get_active_positions():
    return (
        db.session.query(Position)
        .filter(Position.status == 'OPEN')
        .options(joinedload(Position.greeks))
        .all()
    )

# 2. Get trades for today (with indexes)
@cache.cached(timeout=60)
def get_todays_trades():
    today = datetime.now().date()
    return (
        db.session.query(Trade)
        .filter(
            Trade.created_at >= today,
            Trade.status == 'CLOSED'
        )
        .order_by(Trade.created_at.desc())
        .limit(100)
        .all()
    )

# 3. Get Greeks data efficiently
def get_greeks_snapshot(symbols, expiry):
    return (
        db.session.query(GreeksSnapshot)
        .filter(
            GreeksSnapshot.symbol.in_(symbols),
            GreeksSnapshot.expiry == expiry
        )
        .order_by(GreeksSnapshot.snapshot_time.desc())
        .all()
    )
```

---

## Caching Strategy

### Multi-Layer Caching

```
┌─────────────────────────────────────────────┐
│ Level 1: In-Memory Cache (Python Dict)      │
│ TTL: 1-10 seconds, Size: Small              │
├─────────────────────────────────────────────┤
│ Level 2: Redis Cache                        │
│ TTL: 30-300 seconds, Size: Medium           │
├─────────────────────────────────────────────┤
│ Level 3: Database                           │
│ TTL: Permanent with indexing                │
└─────────────────────────────────────────────┘
```

### Cache Configuration

```python
# In-memory cache
from functools import lru_cache

@lru_cache(maxsize=1000, typed=True)
def calculate_position_pnl(symbol, entry_price, current_price):
    # Cached for repeated calls within timeout
    return (current_price - entry_price) * 1  # Simplified

# Redis cache with TTL
import redis
from datetime import timedelta

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# Cache with automatic expiration
def cache_market_data(symbol, data, ttl_seconds=60):
    key = f"market_data:{symbol}"
    redis_client.setex(key, timedelta(seconds=ttl_seconds), json.dumps(data))

# Cache-aside pattern
def get_market_data_with_fallback(symbol):
    # Try cache first
    cached = redis_client.get(f"market_data:{symbol}")
    if cached:
        return json.loads(cached)
    
    # Fall back to database/API
    data = fetch_market_data(symbol)
    cache_market_data(symbol, data)
    return data
```

### Cache Invalidation

```python
# Event-based cache invalidation
def invalidate_position_cache(position_id):
    redis_client.delete(f"position:{position_id}")
    redis_client.delete("portfolio_summary")
    redis_client.delete("active_positions_list")

# Pattern-based invalidation
def invalidate_greeks_cache(symbol):
    pattern = f"greeks:{symbol}:*"
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)

# Time-based cache warming
def warm_cache_on_market_open():
    """Called at market open to pre-populate cache"""
    symbols = get_trading_symbols()
    for symbol in symbols:
        market_data = fetch_market_data(symbol)
        cache_market_data(symbol, market_data, ttl_seconds=300)
```

---

## Configuration Management

### Environment-Specific Configuration

```python
# config/development.py
CAPITAL = 100000
DAILY_LOSS_LIMIT = 2000
DEBUG = True
PAPER_TRADING_ENABLED = True

# config/production.py
CAPITAL = 500000
DAILY_LOSS_LIMIT = 10000
DEBUG = False
PAPER_TRADING_ENABLED = False
ALERTS_ENABLED = True
BROKER_CONNECTION = 'live'

# Select configuration
import os
config_env = os.getenv('ENVIRONMENT', 'development')
if config_env == 'production':
    from config.production import *
else:
    from config.development import *
```

### Configuration Validation

```python
def validate_configuration():
    """Validate configuration on startup"""
    errors = []
    
    # Validate capital
    if CAPITAL < 10000:
        errors.append("CAPITAL must be >= ₹10,000")
    
    # Validate loss limits
    if DAILY_LOSS_LIMIT > CAPITAL * 0.1:
        errors.append("DAILY_LOSS_LIMIT should not exceed 10% of capital")
    
    # Validate position sizes
    if MAX_POSITION_SIZE > 200:
        errors.append("MAX_POSITION_SIZE should not exceed 200 lots")
    
    if errors:
        raise ConfigurationError(f"Configuration errors: {errors}")
    
    logger.info("Configuration validated successfully")
```

---

## Performance Benchmarks

### Expected Performance Metrics

| Operation | Latency | Throughput |
|-----------|---------|-----------|
| Order submission | <50ms | 1000 orders/sec |
| Position update | <100ms | 5000 updates/sec |
| Greeks calculation | <200ms | 500 options/sec |
| Price update | <20ms | 50000 ticks/sec |
| Database query | <50ms | 200 queries/sec |

### Optimization Checklist

- [ ] Database indexes created for all key queries
- [ ] Redis cache configured with appropriate TTLs
- [ ] Connection pools sized for concurrent load
- [ ] Thread pool configured based on CPU cores
- [ ] Prometheus metrics enabled for monitoring
- [ ] Alert thresholds configured appropriately
- [ ] Batch processing enabled for operations
- [ ] Query caching implemented where applicable
- [ ] Slow query logs enabled (PostgreSQL)
- [ ] Performance tests passed with acceptable results

---

## Troubleshooting

### High Latency Issues

1. **Check database queries**
   ```bash
   # Enable slow query log
   ALTER SYSTEM SET log_min_duration_statement = 100;  # Log queries > 100ms
   SELECT pg_reload_conf();
   ```

2. **Check Redis performance**
   ```bash
   redis-cli --latency
   redis-cli --bigkeys
   ```

3. **Check thread pool saturation**
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   # Look for "Queue full" warnings
   ```

### Memory Issues

1. **Monitor memory usage**
   ```python
   import psutil
   process = psutil.Process()
   print(process.memory_info().rss / 1024 / 1024)  # MB
   ```

2. **Check cache sizes**
   ```bash
   redis-cli INFO memory
   ```

### Connection Pool Issues

1. **Monitor pool usage**
   ```python
   from sqlalchemy import event
   @event.listens_for(Engine, "connect")
   def receive_connect(dbapi_conn, connection_record):
       print(f"Pool size: {dbapi_conn.pool.size()}")
   ```

---

## References

- [PostgreSQL Performance Tuning](https://www.postgresql.org/docs/current/performance-tips.html)
- [Redis Optimization Guide](https://redis.io/topics/optimization)
- [SQLAlchemy Connection Pooling](https://docs.sqlalchemy.org/en/14/core/pooling.html)
- [Python Async/Threading Best Practices](https://docs.python.org/3/library/threading.html)

