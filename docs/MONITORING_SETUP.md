# Monitoring Setup Guide - Angel-X Trading System

## 📋 Overview

Comprehensive monitoring infrastructure for Angel-X using Prometheus, Grafana, and AlertManager with custom trading-specific metrics.

## 🏗️ Architecture

### Components

```
┌─────────────────┐
│  Angel-X App    │
│   (Metrics)     │
└────────┬────────┘
         │ Scrapes /metrics
         │
    ┌────▼────────────┐
    │  Prometheus     │
    │  (TSDB & Rules) │
    └────┬────────────┘
         │ Queries
         │
    ┌────▼────────────┐
    │  Grafana        │
    │  (Dashboards)   │
    └────┬────────────┘
         │ Visualizes
         │
    ┌────▼────────────┐
    │  AlertManager   │
    │  (Alerting)     │
    └─────────────────┘
```

### Services
- **Prometheus**: Time-series database + rule evaluation
- **Grafana**: Visualization and dashboards
- **AlertManager**: Alert routing and notification
- **Angel-X**: Metrics exporter + health checks

## 📦 Files Created

### Prometheus Configuration
```
infra/monitoring/
├── prometheus.yml           # Prometheus scrape config + rules
└── alert.rules.yml          # 20+ alert rules for trading system
```

### Grafana Configuration
```
infra/monitoring/grafana-dashboards/
├── dashboard-provider.json  # Dashboard provisioning config
├── system-overview.json     # System metrics dashboard
└── trading-metrics.json     # Trading-specific dashboard
```

### Monitoring Code
```
app/utils/
├── prometheus_metrics.py    # Metrics definitions (40+ metrics)
└── health_check.py          # Health check implementation
```

### Monitoring API
```
app/api/
└── monitoring.py            # Health/readiness/liveness endpoints
```

## 🚀 Quick Start

### Using Docker Compose

**Run monitoring stack:**
```bash
# Start app with monitoring
docker-compose --profile monitoring up -d

# View logs
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

**Access dashboards:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)

### Manual Setup

**Prerequisites:**
```bash
pip install prometheus-client flask
```

**Start Prometheus:**
```bash
prometheus --config.file=infra/monitoring/prometheus.yml
```

**Start Grafana:**
```bash
docker run -d -p 3000:3000 grafana/grafana
```

## 📊 Metrics Overview

### Application Metrics (40+)

**API Metrics:**
- `http_requests_total` - Total HTTP requests
- `http_request_duration_seconds` - Request latency (histogram)

**Trading Metrics:**
- `trades_executed_total` - Trades by strategy/instrument
- `trades_won_total` - Winning trades count
- `signals_generated_total` - Signals by type/domain
- `active_positions_count` - Open positions
- `trading_profit_loss_cumulative` - Cumulative P&L
- `risk_exposure_ratio` - Current risk level

**Greeks Metrics:**
- `greeks_calculation_duration_seconds` - Calculation speed
- `greeks_calculation_errors_total` - Calculation failures
- `option_chain_update_lag_seconds` - Data freshness

**Market Data Metrics:**
- `market_data_last_update_timestamp` - Last data update
- `market_data_updates_total` - Update frequency
- `market_data_errors_total` - Data failures

**Database Metrics:**
- `db_connection_pool_available` - Connection pool status
- `db_query_duration_seconds` - Query performance
- `db_query_errors_total` - Database errors
- `db_transaction_duration_seconds` - Transaction time

**Broker Metrics:**
- `broker_connection_status` - Broker connectivity
- `broker_order_latency_seconds` - Order execution time
- `broker_orders_placed_total` - Order count
- `broker_orders_rejected_total` - Rejected orders
- `broker_fill_rate` - Fill rate percentage

**Learning Metrics:**
- `learning_model_accuracy` - Model performance
- `learning_model_training_duration_seconds` - Training time
- `learning_feedback_processed_total` - Feedback samples
- `learning_feedback_queue_size` - Queue status

## 🚨 Alert Rules (20+)

### Critical Alerts (Immediate Action)
- `Angel_X_Down` - Application not responding
- `TradingEngineStalled` - No trades for 10 minutes
- `BrokerConnectionLost` - Broker unreachable
- `RiskLimitBreach` - Risk > 90% of limit
- `DatabaseConnectionPoolExhausted` - <2 connections available

### Warning Alerts (Investigation)
- `HighAPILatency` - Response time > 1 second
- `HighErrorRate` - 5xx errors > 5%
- `HighMemoryUsage` - Memory > 2GB
- `HighCPUUsage` - CPU > 80%
- `MarketDataStale` - No updates > 60 seconds
- `OptionChainUpdateLag` - Lag > 30 seconds
- `GreeksCalculationSlow` - Calculation > 500ms
- `SlowDatabaseQueries` - Query time > 1 second
- `LowSignalGeneration` - Signals < 0.1/minute
- `PrometheusHighMemory` - Prometheus > 4GB
- `DiskSpaceLow` - <10% disk free
- `LearningModelAccuracyLow` - Accuracy < 50%
- `FeedbackProcessingLag` - Queue > 1000 items

## 📈 Dashboards

### System Overview Dashboard
- Application Status (up/down)
- API Response Time (gauge)
- Requests per Second (rate)
- Memory Usage (MB)
- CPU Usage (%)
- Error Rate (%)

### Trading Metrics Dashboard
- Trades Executed (counter)
- Signals Generated (counter)
- Win Rate (gauge)
- Risk Exposure Ratio (gauge)
- Trading Activity (rate)
- P&L Over Time (graph)
- Active Positions (counter)
- Greeks Health (histogram)

## 🔧 Configuration

### Prometheus Config (prometheus.yml)

**Scrape targets:**
```yaml
scrape_configs:
  - job_name: 'angel-x'
    targets: ['angel-x:5000']
    scrape_interval: 10s
    
  - job_name: 'postgres'
    targets: ['postgres-exporter:9187']
    scrape_interval: 30s
```

**Alert rules:**
```yaml
rule_files:
  - 'alert.rules.yml'
```

### Grafana Datasources

Add Prometheus as datasource:
```json
{
  "name": "Prometheus",
  "type": "prometheus",
  "url": "http://prometheus:9090",
  "isDefault": true
}
```

## 🔍 Health Check Endpoints

### /monitor/health
**Comprehensive health status:**
```bash
curl http://localhost:5000/monitor/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-08T10:30:00",
  "version": "1.0.0",
  "environment": "production",
  "checks": {
    "application": {
      "status": "healthy",
      "uptime_seconds": 3600
    },
    "system": {
      "status": "healthy",
      "cpu_percent": 25.5,
      "memory_percent": 45.2,
      "disk_percent": 32.1
    },
    "services": {
      "database": {"status": "healthy"},
      "broker": {"status": "healthy"},
      "market_data": {"status": "healthy"},
      "cache": {"status": "healthy"}
    }
  }
}
```

### /monitor/ready
**Readiness probe (for orchestration):**
```bash
curl http://localhost:5000/monitor/ready
```

### /monitor/live
**Liveness probe (for orchestration):**
```bash
curl http://localhost:5000/monitor/live
```

### /metrics
**Prometheus metrics (scraped by Prometheus):**
```bash
curl http://localhost:5000/metrics
```

## 📋 Usage Examples

### Recording Metrics

**In your application code:**
```python
from app.utils.prometheus_metrics import *

# Record HTTP request
record_http_request('GET', '/api/trades', 200, 0.125)

# Record trade
record_trade_executed('momentum_strategy', 'NIFTY', True)

# Record signal
record_signal_generated('entry', 'options_domain')

# Record Greeks calculation
record_greeks_calculation('delta', 0.045)

# Record DB query
record_db_query('SELECT', 'trades', 0.050)

# Update broker status
set_broker_connection_status('angelone', True)

# Update model accuracy
update_learning_accuracy('pattern_recognition', 0.87)
```

### Querying Prometheus

**PromQL examples:**
```promql
# API request rate (5 min)
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# Memory usage
process_resident_memory_bytes / 1024 / 1024 / 1024

# Trades per minute
rate(trades_executed_total[1m])

# Win rate
trades_won_total / trades_executed_total

# Current P&L
trading_profit_loss_cumulative

# Greeks calculation speed (avg)
rate(greeks_calculation_duration_seconds_sum[5m]) / rate(greeks_calculation_duration_seconds_count[5m])
```

### Creating Custom Dashboards

1. Open Grafana: http://localhost:3000
2. New Dashboard → New Panel
3. Select Prometheus data source
4. Enter PromQL query
5. Save dashboard

## 🔒 Security Best Practices

### Prometheus
- No authentication by default (use reverse proxy)
- Limit scrape targets to internal network
- Monitor disk usage (TSDB grows quickly)
- Retention policy: 15 days by default

### Grafana
- Change default password (admin/admin)
- Use authentication (LDAP, OAuth)
- Restrict dashboard access
- Audit user activity

### AlertManager
- Verify alert webhook URLs
- Use HTTPS for alert notifications
- Implement rate limiting
- Test alert channels

## 📊 Performance Tuning

### Prometheus
```bash
# Increase scrape concurrency
prometheus --query.concurrency=10

# Increase memory for large datasets
docker run -e JAVA_OPTS="-Xmx4g" prometheus
```

### Grafana
```bash
# Adjust query timeout
GF_PANELS_QUERY_TIMEOUT=600s

# Increase session timeout
GF_SESSION_LIFE_TIME=43200
```

### Storage
```bash
# Prometheus data directory
--storage.tsdb.path=/prometheus

# Retention policy
--storage.tsdb.retention.time=15d
--storage.tsdb.retention.size=50GB
```

## 🆘 Troubleshooting

### Prometheus not scraping
```bash
# Check targets status
curl http://localhost:9090/api/v1/targets

# Check config syntax
prometheus --config.file=prometheus.yml --dry-run
```

### No metrics appearing in Grafana
1. Verify Prometheus data source is configured
2. Check Prometheus scrape targets are up
3. Verify metric names in PromQL query
4. Check time range selection

### Alerts not firing
```bash
# Check alert rules
curl http://localhost:9090/api/v1/rules

# Verify alert conditions
curl http://localhost:9090/api/v1/alerts
```

### High Prometheus memory usage
- Reduce scrape interval
- Implement lower retention policy
- Drop unnecessary metrics
- Scale horizontally with federation

## 📚 Additional Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Query Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Alert Rule Examples](https://prometheus.io/docs/prometheus/latest/configuration/alerting_rules/)
- [Best Practices](https://prometheus.io/docs/practices/naming/)

## 🎯 Production Checklist

- [ ] Prometheus retention configured for your data volume
- [ ] AlertManager configured with notification channels
- [ ] Grafana dashboards created and tested
- [ ] Alert rules tuned to your thresholds
- [ ] Monitoring endpoints health checked
- [ ] Metrics scraping verified working
- [ ] Backup strategy for Prometheus TSDB
- [ ] Resource limits set for containers
- [ ] Authentication configured for Grafana
- [ ] Alert notification channels tested

---

**Status**: Phase 6 Complete - Monitoring Infrastructure Ready ✅
**Next Phase**: Phase 7 - Production Deployment
