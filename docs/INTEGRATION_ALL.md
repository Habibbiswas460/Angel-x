# Complete Integration Guide

## 1. Live Broker Integration

### Setup AngelOne Credentials

Add to `config/config.py`:

```python
# AngelOne SmartAPI Configuration
ANGELONE_CLIENT_CODE = "YOUR_CLIENT_CODE"
ANGELONE_API_KEY = "YOUR_API_KEY"
ANGELONE_FEED_TOKEN = "YOUR_FEED_TOKEN"
```

### Connect to Broker

```python
from src.integrations.broker_integration import get_broker

# Get broker instance
broker = get_broker()

# Connect
success = broker.connect()
if success:
    print("✓ Connected to AngelOne broker")
    
    # Subscribe to index
    broker.subscribe_nifty_banknifty()
    
    # Or subscribe to option chain
    broker.subscribe_option_chain(
        underlying="NIFTY",
        expiry="20260115",
        strikes=[23000, 23100, 23200]
    )
    
    # Register tick callback
    def on_new_tick(tick):
        print(f"Price: {tick['ltp']}, Volume: {tick['volume']}")
    
    broker.on_tick(on_new_tick)
```

### Get Connection Stats

```python
stats = broker.get_stats()
print(f"Total ticks received: {stats['total_ticks']}")
print(f"Instruments subscribed: {stats['subscribed_instruments']}")
```

---

## 2. Strategy Backtesting

### Simple Backtest

```python
import pandas as pd
from src.backtesting import load_backtest_data, run_strategy_backtest

# Load historical data
df = load_backtest_data("NIFTY", period='5min')

# Define strategy function
def my_strategy(row, trades, capital):
    """
    row: Current candle (open, high, low, close, volume)
    trades: List of TradeExecution objects
    capital: Current capital
    
    Returns: {'action': 'BUY'|'SELL'|'CLOSE', 'price': float, 'qty': int}
    """
    
    # Example: Simple MA crossover
    if row['close'] > row['open'] * 1.01:  # 1% up
        return {'action': 'BUY', 'price': row['close'], 'qty': 1}
    elif row['close'] < row['open'] * 0.99:  # 1% down
        return {'action': 'CLOSE', 'price': row['close']}
    
    return None

# Run backtest
result = run_strategy_backtest(df, my_strategy, "NIFTY", initial_capital=100000)

# Print report
print(result)
```

### Advanced Backtest with Multi-Leg Strategy

```python
from src.strategies.multi_leg.iron_condor import IronCondor
from src.backtesting import BacktestEngine
import numpy as np

def iron_condor_strategy(row, trades, capital):
    """Iron Condor strategy"""
    
    # Current price
    spot = row['close']
    
    # Build Iron Condor
    ic = IronCondor(underlying="NIFTY", spot=spot, expiry_days=2)
    
    # Check Greeks and decide
    if not trades and capital > 50000:
        return {'action': 'BUY', 'price': spot, 'qty': 1}
    elif trades and len(trades) > 0:
        # Close if profit target hit or SL hit
        pnl_percent = trades[-1].pnl_percent
        if pnl_percent > 5 or pnl_percent < -3:
            return {'action': 'CLOSE', 'price': spot}
    
    return None

# Run with custom engine
engine = BacktestEngine(initial_capital=100000)
result = engine.run(df, iron_condor_strategy, symbol="NIFTY")
print(f"Total P&L: ₹{result.total_pnl:.2f}")
print(f"Win Rate: {result.win_rate:.2%}")
print(f"Sharpe Ratio: {result.sharpe_ratio:.2f}")
```

### Load Custom Data

```python
from src.backtesting import TickDataLoader

loader = TickDataLoader()

# Load from CSV
df_ticks = loader.load_ticks_csv("ticks_20260110.csv")

# Convert to OHLCV
df_ohlcv = loader.convert_ticks_to_ohlcv(df_ticks, period='5min')

# Find latest tick file
latest_file = loader.find_latest_tick_file()
print(f"Latest: {latest_file}")

# Load all available files
all_files = loader.find_all_tick_files()
print(f"Available: {all_files}")
```

---

## 3. Monitoring & Alerts

### Setup Telegram Alerts

Get your Telegram bot token and chat ID:
1. Create bot: [@BotFather](https://t.me/BotFather)
2. Get chat ID: Send message to bot, check `/getMe`

Add to `config/config.py`:

```python
# Telegram Alerts
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN"
TELEGRAM_CHAT_ID = "YOUR_CHAT_ID"
```

### Use Health Monitor

```python
from src.monitoring import AlertConfig, get_monitor

# Setup alerts
alert_config = AlertConfig(
    telegram_bot_token="YOUR_BOT_TOKEN",
    telegram_chat_id="YOUR_CHAT_ID",
    alert_levels={
        'critical': True,
        'warning': True,
        'info': False
    }
)

monitor = get_monitor(alert_config)

# Check health
metric = monitor.check_health(
    broker_connected=True,
    database_healthy=True,
    api_responding=True,
    memory_usage_mb=1024,
    cpu_percent=25,
    model_trained=True,
    error_count=0
)

# Get status report
report = monitor.get_status_report()
print(report)
```

### Prometheus Metrics

```python
from src.monitoring import get_prometheus_metrics
from flask import Flask

app = Flask(__name__)
metrics = get_prometheus_metrics()

# Track metrics
metrics.increment('trades_total')
metrics.increment('trades_winning')
metrics.set('pnl_total', 50000)

# Export endpoint
from src.monitoring import create_prometheus_blueprint
bp = create_prometheus_blueprint(metrics)
app.register_blueprint(bp)

# Prometheus text format: /metrics/prometheus
# JSON format: /metrics/json
```

---

## 4. Production Deployment

### Docker Compose with Monitoring

Update `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - ANGELONE_CLIENT_CODE=${ANGELONE_CLIENT_CODE}
      - ANGELONE_API_KEY=${ANGELONE_API_KEY}
      - ANGELONE_FEED_TOKEN=${ANGELONE_FEED_TOKEN}
      - TELEGRAM_BOT_TOKEN=${TELEGRAM_BOT_TOKEN}
      - TELEGRAM_CHAT_ID=${TELEGRAM_CHAT_ID}
    depends_on:
      - postgres
    healthcheck:
      test: curl -f http://localhost:5000/health
      interval: 30s
      timeout: 5s
      retries: 3

  postgres:
    image: postgres:16
    environment:
      - POSTGRES_PASSWORD=angelx_secure
      - POSTGRES_DB=angelx
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./infra/monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana

volumes:
  postgres_data:
  grafana_data:
```

Create `infra/monitoring/prometheus.yml`:

```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'angelx'
    static_configs:
      - targets: ['localhost:5000']
    metrics_path: '/metrics/prometheus'
```

### Deploy

```bash
# Set credentials
export ANGELONE_CLIENT_CODE="YOUR_CODE"
export ANGELONE_API_KEY="YOUR_KEY"
export ANGELONE_FEED_TOKEN="YOUR_TOKEN"
export TELEGRAM_BOT_TOKEN="YOUR_BOT_TOKEN"
export TELEGRAM_CHAT_ID="YOUR_CHAT_ID"

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f app

# Access dashboards
# App: http://localhost:5000
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

---

## 5. Advanced Features

### Custom Strategy Development

```python
from src.strategies.multi_leg.base import MultiLegStrategy, Leg
from src.strategies.multi_leg.spreads import BullCallSpread

class MyCustomStrategy(MultiLegStrategy):
    def build_legs(self):
        """Define strategy legs"""
        spot = 23000
        
        return [
            Leg(
                instrument="NIFTY",
                strike=23000,
                kind="CE",
                qty=1,
                side="BUY"
            ),
            Leg(
                instrument="NIFTY",
                strike=23100,
                kind="CE",
                qty=1,
                side="SELL"
            ),
        ]

# Use in backtest
strategy = MyCustomStrategy()
print(strategy.build_legs())
```

### ML Signal Integration

```python
from src.ml.integration import get_ml_engine
from src.integrations.broker_integration import get_broker

ml = get_ml_engine()
broker = get_broker()

# Train on historical data
train_info = ml.train(
    ticks_df=df_ticks,
    lookback=50,
    features=['sma', 'rsi', 'atr']
)

# Get predictions
broker.on_tick(lambda tick: {
    'predictions': ml.infer(tick),
    'direction': predictions.get('direction', [])
})
```

---

## Quick Commands

```bash
# Load data and run backtest
python3 -c "
from src.backtesting import load_backtest_data, run_strategy_backtest
df = load_backtest_data()
# Define strategy...
result = run_strategy_backtest(df, strategy)
print(result)
"

# Check broker connection
docker-compose exec app python3 -c "
from src.integrations.broker_integration import get_broker
broker = get_broker()
print('Connected:', broker.connect())
"

# View Prometheus metrics
curl http://localhost:5000/metrics/prometheus

# View monitoring status
curl http://localhost:5000/api/dashboard | jq '.monitoring'
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Broker not connecting | Check credentials in config.py; run `broker.connect()` |
| No backtest data | Place CSV in `ticks/` or `data/`; loader finds automatically |
| Telegram alerts not sent | Verify bot token and chat ID; check network |
| Prometheus not scraping | Ensure `app:5000/metrics/prometheus` is accessible |
| Memory leak in monitor | Limit `metrics_history` size; clear old entries |

---

## Next Steps

✅ Broker integration setup  
✅ Backtest any strategy  
✅ Monitor with alerts  
✅ Deploy to production  
✅ Export metrics to Grafana  

Ready for:
- Live trading with AngelOne
- Strategy optimization
- Risk management
- Portfolio analysis
