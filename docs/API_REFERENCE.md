# Angel-X REST API Documentation

Complete API reference for Angel-X trading platform including all endpoints, request/response formats, and authentication.

## Base URL

```
http://localhost:5000
https://api.angel-x.com  (Production)
```

## Authentication

### Current Implementation
- No authentication currently enabled (development mode)
- Ready for JWT/API key integration

### Recommended Production Authentication (TODO)
```bash
# Add to config
AUTH_ENABLED = True
SECRET_KEY = "your-secret-key"
JWT_EXPIRATION_HOURS = 24
```

---

## API Endpoints

### System Health & Monitoring

#### GET `/health`
**Comprehensive system health check**

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-01-11T16:00:00",
  "services": {
    "database": "connected",
    "broker": "connected",
    "redis": "connected",
    "alerts": "operational"
  },
  "metrics": {
    "uptime_hours": 2.5,
    "memory_usage_mb": 256,
    "cpu_percent": 15.2
  }
}
```

**Status Codes:**
- `200 OK` - All systems healthy
- `503 Service Unavailable` - Critical service down

---

#### GET `/monitor/ready`
**Kubernetes readiness probe**

**Response:**
```json
{
  "ready": true,
  "database_ready": true,
  "broker_ready": true,
  "cache_ready": true
}
```

**Status Codes:**
- `200 OK` - Ready to accept traffic
- `503 Service Unavailable` - Not ready

---

#### GET `/monitor/live`
**Kubernetes liveness probe**

**Response:**
```json
{
  "alive": true,
  "uptime_seconds": 9000
}
```

---

#### GET `/monitor/ping`
**Simple connectivity check**

**Response:**
```json
{
  "status": "pong"
}
```

---

#### GET `/monitor/metrics`
**Prometheus-format metrics for monitoring systems**

**Response (text/plain):**
```
# HELP angel_x_alerts_sent Total alerts sent
# TYPE angel_x_alerts_sent counter
angel_x_alerts_sent 42

# HELP angel_x_alerts_failed Total alerts failed
# TYPE angel_x_alerts_failed counter
angel_x_alerts_failed 1

# HELP angel_x_alert_queue_size Current alert queue size
# TYPE angel_x_alert_queue_size gauge
angel_x_alert_queue_size 5

# HELP angel_x_system_healthy System health status
# TYPE angel_x_system_healthy gauge
angel_x_system_healthy 1
```

**Integration:**
```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'angel-x'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/monitor/metrics'
```

---

#### GET `/monitor/alerts`
**Alert history and statistics**

**Query Parameters:**
- `limit` (int, default=50) - Number of recent alerts to return

**Response:**
```json
{
  "stats": {
    "alerts_sent": 156,
    "alerts_failed": 3,
    "queue_size": 0,
    "history_size": 150,
    "by_type": {
      "TRADE_ENTRY": 45,
      "TRADE_EXIT": 42,
      "LOSS_LIMIT": 15,
      "SYSTEM_ERROR": 3
    },
    "by_handler": {
      "log": 150,
      "webhook": 120,
      "email": 45
    }
  },
  "recent_alerts": [
    {
      "timestamp": "2026-01-11T16:05:00",
      "type": "TRADE_ENTRY",
      "level": "INFO",
      "message": "Entry signal: BUY 50 NIFTY_25JAN26_19000CE @ ₹125.50",
      "status": "sent"
    }
  ]
}
```

---

### Trading Data

#### GET `/api/positions`
**Get all open positions**

**Response:**
```json
{
  "positions": [
    {
      "symbol": "NIFTY_25JAN26_19000CE",
      "type": "CE",
      "strike": 19000,
      "quantity": 50,
      "entry_price": 125.50,
      "current_price": 130.00,
      "entry_time": "2026-01-11T15:00:00",
      "pnl_rupees": 225.00,
      "pnl_percent": 3.57,
      "greeks": {
        "delta": 0.65,
        "gamma": 0.02,
        "theta": -0.15,
        "vega": 0.10
      }
    }
  ],
  "portfolio_greeks": {
    "delta": 32.5,
    "gamma": 1.0,
    "theta": -7.5,
    "vega": 5.0
  },
  "total_open_pnl": 225.00
}
```

---

#### GET `/api/trades`
**Get trading history**

**Query Parameters:**
- `days` (int, default=1) - Number of days to look back
- `limit` (int, default=100) - Maximum trades to return
- `status` (string) - Filter: "closed", "open", or "all"

**Response:**
```json
{
  "trades": [
    {
      "id": "PAPER_20260111150000_000001",
      "symbol": "NIFTY_25JAN26_19000CE",
      "action": "BUY",
      "quantity": 50,
      "entry_price": 125.50,
      "entry_time": "2026-01-11T15:00:00",
      "exit_price": 130.00,
      "exit_time": "2026-01-11T15:45:00",
      "pnl_rupees": 225.00,
      "pnl_percent": 3.57,
      "duration_minutes": 45,
      "status": "closed",
      "reason": "Take profit hit"
    }
  ],
  "summary": {
    "total_trades": 8,
    "winning_trades": 6,
    "losing_trades": 2,
    "win_rate_percent": 75.0,
    "total_pnl": 1850.50,
    "avg_winner": 425.25,
    "avg_loser": -287.50
  }
}
```

---

#### GET `/api/dashboard`
**Complete dashboard snapshot**

**Response:**
```json
{
  "timestamp": "2026-01-11T16:05:00",
  "account": {
    "capital": 100000,
    "current_value": 101850.50,
    "daily_pnl": 1850.50,
    "daily_return_percent": 1.85
  },
  "positions": {
    "active_count": 2,
    "open_pnl": 450.00,
    "portfolio_delta": 65.0
  },
  "trades": {
    "today_count": 8,
    "winning": 6,
    "losing": 2,
    "win_rate": 75.0
  },
  "risk": {
    "daily_loss_limit": 2000.00,
    "daily_loss_remaining": 2000.00,
    "margin_used_percent": 15.5,
    "max_drawdown": 500.00
  }
}
```

---

#### GET `/api/portfolio`
**Portfolio analysis and Greeks**

**Response:**
```json
{
  "portfolio": {
    "net_value": 101850.50,
    "gross_exposure": 6250.00,
    "net_exposure": 3125.00,
    "hedge_ratio": 0.5
  },
  "greeks": {
    "delta": 65.0,
    "gamma": 2.5,
    "theta": -15.0,
    "vega": 10.0,
    "interpretation": "Bullish bias, positive theta decay favors position"
  },
  "risk_metrics": {
    "max_loss_1_sigma": 850.00,
    "max_loss_2_sigma": 2100.00,
    "var_95": 1500.00
  }
}
```

---

#### GET `/api/performance`
**Performance metrics and statistics**

**Query Parameters:**
- `period` (string, default="all") - "today", "week", "month", or "all"

**Response:**
```json
{
  "period": "all",
  "statistics": {
    "total_trades": 28,
    "winning_trades": 21,
    "losing_trades": 7,
    "win_rate_percent": 75.0,
    "profit_factor": 2.85,
    "sharpe_ratio": 1.95,
    "sortino_ratio": 2.65,
    "max_drawdown_percent": 2.15,
    "calmar_ratio": 3.20
  },
  "profitability": {
    "gross_profit": 12850.00,
    "gross_loss": -4500.00,
    "net_profit": 8350.00,
    "roi_percent": 8.35
  },
  "trade_analysis": {
    "avg_trade_pnl": 298.21,
    "avg_winning_trade": 612.38,
    "avg_losing_trade": -642.86,
    "best_trade": 1250.00,
    "worst_trade": -1200.00,
    "consecutive_wins": 5,
    "consecutive_losses": 2,
    "avg_win_to_loss_ratio": 0.95
  },
  "time_analysis": {
    "total_trades_duration_hours": 24.5,
    "avg_trade_duration_minutes": 52.5,
    "most_profitable_hour": "10:00-11:00",
    "trades_by_hour": {
      "09:00": 4,
      "10:00": 6,
      "11:00": 5
    }
  }
}
```

---

#### GET `/api/market`
**Current market data snapshot**

**Query Parameters:**
- `symbols` (string, comma-separated) - Optional specific symbols

**Response:**
```json
{
  "market": {
    "nifty_ltp": 19850.50,
    "nifty_change_percent": 0.85,
    "banknifty_ltp": 47250.00,
    "vix": 18.5,
    "market_status": "open",
    "time_to_market_close": "01:15:00"
  },
  "option_chain_snapshot": {
    "underlying": "NIFTY",
    "expiry": "25JAN26",
    "atm_strike": 19850,
    "volatility_skew": 0.15,
    "implied_volatility": {
      "call_vol": 18.5,
      "put_vol": 17.8,
      "index_vol": 18.2
    },
    "option_data": [
      {
        "strike": 19700,
        "call_bid": 215.50,
        "call_ask": 218.50,
        "call_ltp": 217.00,
        "call_oi": 850000,
        "put_bid": 60.50,
        "put_ask": 62.50,
        "put_ltp": 61.50,
        "put_oi": 920000
      }
    ]
  }
}
```

---

### Advanced Features

#### GET `/api/greeks-heatmap`
**Greeks heatmap for option chain**

**Query Parameters:**
- `underlying` (string, default="NIFTY") - Underlying asset
- `expiry` (string, default="current") - Expiry date

**Response:**
```json
{
  "heatmap": [
    {
      "strike": 19700,
      "call_delta": 0.85,
      "call_gamma": 0.005,
      "put_delta": -0.15,
      "put_gamma": 0.005,
      "call_vega": 0.25,
      "put_vega": 0.20,
      "call_theta": -0.15,
      "put_theta": 0.08
    }
  ],
  "color_scale": {
    "min": -1.0,
    "max": 1.0,
    "neutral": 0.0
  }
}
```

---

## Response Codes

| Code | Meaning | Typical Response |
|------|---------|-----------------|
| 200 | OK | Request successful, data returned |
| 201 | Created | Resource created successfully |
| 204 | No Content | Request successful, no data to return |
| 400 | Bad Request | Invalid parameters or malformed request |
| 401 | Unauthorized | Missing/invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Service temporarily down |

---

## Error Response Format

All error responses follow this format:

```json
{
  "error": true,
  "code": 400,
  "message": "Invalid symbol format",
  "details": {
    "field": "symbol",
    "value": "INVALID123",
    "expected": "NIFTY_25JAN26_19000CE"
  },
  "timestamp": "2026-01-11T16:05:00",
  "request_id": "req_abc123xyz"
}
```

---

## Rate Limiting

| Endpoint Category | Limit | Window |
|------------------|-------|--------|
| Monitoring | 1000/min | Per minute |
| Trading Data | 500/min | Per minute |
| Market Data | 1000/min | Per minute |
| Webhooks | 100/min | Per minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 500
X-RateLimit-Remaining: 492
X-RateLimit-Reset: 1672491901
```

---

## Pagination

Large response sets support pagination:

```json
{
  "data": [...],
  "pagination": {
    "total_items": 1250,
    "page_size": 100,
    "current_page": 1,
    "total_pages": 13,
    "has_next": true,
    "has_prev": false
  }
}
```

**Query Parameters:**
- `page` (int, default=1) - Page number
- `limit` (int, default=50) - Items per page

---

## Webhooks

### Alert Webhooks

**Endpoint Configuration:**
```json
{
  "webhook_url": "https://your-domain.com/webhooks/alerts",
  "events": ["TRADE_ENTRY", "TRADE_EXIT", "LOSS_LIMIT"],
  "retry_policy": "exponential",
  "timeout_seconds": 30
}
```

**Webhook Payload:**
```json
{
  "event": "TRADE_ENTRY",
  "timestamp": "2026-01-11T16:05:00",
  "data": {
    "symbol": "NIFTY_25JAN26_19000CE",
    "action": "BUY",
    "quantity": 50,
    "price": 125.50,
    "confidence": 0.92
  },
  "signature": "sha256=..."
}
```

---

## Code Examples

### Python - Get Positions

```python
import requests

response = requests.get('http://localhost:5000/api/positions')
positions = response.json()

for pos in positions['positions']:
    print(f"{pos['symbol']}: {pos['pnl_rupees']:+.2f}")
```

### JavaScript - Monitor Alerts

```javascript
async function monitorAlerts() {
  const response = await fetch('http://localhost:5000/monitor/alerts');
  const data = await response.json();
  
  console.log(`Recent alerts: ${data.stats.alerts_sent}`);
  data.recent_alerts.forEach(alert => {
    console.log(`[${alert.type}] ${alert.message}`);
  });
}

// Check every 5 seconds
setInterval(monitorAlerts, 5000);
```

### cURL - Health Check

```bash
curl -v http://localhost:5000/health

# With Prometheus Scrape
curl -H "Accept: text/plain" http://localhost:5000/monitor/metrics
```

### Docker Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
```

---

## WebSocket Events (Future Enhancement)

Planned real-time endpoints:

```javascript
// Connect to live data stream
const ws = new WebSocket('wss://api.angel-x.com/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  if (data.type === 'POSITION_UPDATE') {
    console.log(`Position updated: ${data.symbol}`);
  } else if (data.type === 'TRADE_ALERT') {
    console.log(`Trade alert: ${data.message}`);
  }
};
```

---

## Best Practices

1. **Use Monitoring Endpoints** - Integrate `/monitor/metrics` with Prometheus
2. **Implement Backoff** - Use exponential backoff for failed requests
3. **Cache Data** - Cache market data and portfolio data locally
4. **Handle Errors** - Implement proper error handling and retry logic
5. **Validate Input** - Always validate query parameters and filters
6. **Log Requests** - Log important API calls for debugging
7. **Rate Limiting** - Implement client-side rate limiting
8. **Security** - Use HTTPS in production, enable JWT authentication

---

## Troubleshooting

### Common Issues

**503 Service Unavailable**
- Check broker connection status via `/health`
- Verify database connectivity
- Check Redis cache status

**404 Not Found**
- Verify endpoint path spelling
- Check API version compatibility
- Review base URL configuration

**429 Too Many Requests**
- Implement request queuing
- Reduce polling frequency
- Cache responses locally

---

## Support & Feedback

- **Documentation**: [GitHub Wiki](https://github.com/angel-x/docs)
- **Issues**: [GitHub Issues](https://github.com/angel-x/issues)
- **Slack**: [angel-x.slack.com](https://angel-x.slack.com)
- **Email**: api-support@angel-x.com

