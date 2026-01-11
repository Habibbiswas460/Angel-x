# Production Deployment Guide

## Overview
Angel-X is production-ready for algorithmic options trading. This guide covers deployment on Linux servers (Ubuntu 20.04+) or Docker containers.

## Pre-Deployment Checklist

### 1. System Requirements
- Python 3.10+ (3.12 recommended)
- PostgreSQL 13+
- Redis 6+ (for caching)
- 4GB RAM minimum (8GB recommended)
- 20GB disk space
- Stable internet connection (99.5% uptime required)
- Broker account with API access (Angel One SmartAPI)

### 2. Credentials & Configuration
Create `.env` file with:
```bash
# Broker Configuration
ANGELONE_API_KEY=your_api_key
ANGELONE_CLIENT_CODE=your_client_code
ANGELONE_PASSWORD=your_password
ANGELONE_TOTP_SECRET=your_totp_secret

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/angelx
REDIS_URL=redis://localhost:6379/0

# Trading Configuration
CAPITAL=100000  # In INR
PAPER_TRADING=False  # Set to True for testing

# Alert Configuration
ALERT_WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
ALERT_EMAIL_CONFIG={
  "server": "smtp.gmail.com",
  "port": 587,
  "sender_email": "your-email@gmail.com",
  "sender_password": "your-app-password",
  "recipient_email": "alerts@yourdomain.com"
}

# Flask & API
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Clone and setup
git clone https://github.com/your-org/Angel-x.git
cd Angel-x
cp .env.example .env
# Edit .env with your configuration

# Build and start
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs -f angel-x

# Stop
docker-compose down
```

### Option 2: Linux Systemd Service

```bash
# 1. Install dependencies
sudo apt update
sudo apt install -y python3.12 python3.12-venv postgresql redis-server

# 2. Create service directory
sudo mkdir -p /opt/angel-x
sudo chown $USER:$USER /opt/angel-x
cd /opt/angel-x

# 3. Clone project
git clone https://github.com/your-org/Angel-x.git .

# 4. Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Create systemd service file
sudo tee /etc/systemd/system/angel-x.service > /dev/null <<EOF
[Unit]
Description=Angel-X Trading System
After=network.target postgresql.service redis-server.service

[Service]
Type=simple
User=$USER
WorkingDirectory=/opt/angel-x
Environment="PATH=/opt/angel-x/venv/bin"
EnvironmentFile=/opt/angel-x/.env
ExecStart=/opt/angel-x/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# 7. Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable angel-x
sudo systemctl start angel-x

# 8. Monitor logs
sudo journalctl -u angel-x -f
```

### Option 3: Kubernetes Deployment

```bash
# 1. Apply manifests (update docker image references)
kubectl apply -f infra/kubernetes/namespace.yaml
kubectl apply -f infra/kubernetes/configmap.yaml
kubectl apply -f infra/kubernetes/secrets.yaml
kubectl apply -f infra/kubernetes/deployment.yaml
kubectl apply -f infra/kubernetes/service.yaml

# 2. Verify deployment
kubectl -n angel-x get pods
kubectl -n angel-x describe pod <pod-name>

# 3. View logs
kubectl -n angel-x logs -f deployment/angel-x

# 4. Port forward
kubectl -n angel-x port-forward service/angel-x 5000:5000
```

## Post-Deployment Verification

### 1. Health Checks
```bash
# API Health
curl http://localhost:5000/monitor/health

# Readiness
curl http://localhost:5000/monitor/ready

# Liveness
curl http://localhost:5000/monitor/live

# Prometheus Metrics
curl http://localhost:5000/monitor/metrics
```

### 2. Database Setup
```bash
# Run migrations
python3 -c "from src.database import migrate; migrate()"

# Verify tables
psql $DATABASE_URL -c "\dt"
```

### 3. Broker Connection
```bash
# Test Angel One API connection
python3 -c "from app.services.broker.angelone_adapter import AngelOneAdapter; a = AngelOneAdapter(); print(a.login())"
```

### 4. Run Paper Trading Test
```bash
# Start paper trading for validation
python3 -c "
from src.core.paper_trading import PaperTradingEngine
engine = PaperTradingEngine()
success, order, msg = engine.place_order('NIFTY_25JAN26_19000CE', 'BUY', 75, 100.0)
print(f'Paper Trade: {success}, {order.status}')
"
```

## Monitoring & Alerting

### 1. Alert Configuration
- **Webhook**: Sends JSON alerts to specified URL
- **Email**: SMTP-based critical alerts
- **Logs**: All alerts also logged to system logs

### 2. Prometheus Metrics
- `angel_x_alerts_sent` - Total alerts dispatched
- `angel_x_alerts_failed` - Failed alert deliveries
- `angel_x_alert_queue_size` - Current queue depth
- `angel_x_system_healthy` - System health status

### 3. Alert Types
- **TRADE_ENTRY**: Entry signals with price and quantity
- **TRADE_EXIT**: Exit events with P&L
- **LOSS_LIMIT**: Daily loss limit breaches
- **POSITION_RISK**: Position approaching max loss
- **SYSTEM_ERROR**: Application errors
- **BROKER_DISCONNECT**: Connection failures

## Production Best Practices

### 1. Risk Management
- Always start with PAPER_TRADING=True for validation
- Set appropriate DAILY_LOSS_LIMIT (typically 2-5% of capital)
- Use MAX_CONSECUTIVE_LOSSES to prevent drawdown
- Monitor MAX_POSITION_SIZE to limit single-trade risk

### 2. Performance Optimization
- Use Redis caching for market data
- Enable connection pooling in PostgreSQL
- Run analytics in separate worker processes
- Configure appropriate thread pool sizes

### 3. Security
- Store credentials in .env file (never in code)
- Rotate API keys monthly
- Enable firewall rules (allow only necessary ports)
- Use VPN for broker connections if possible
- Enable SSL/TLS for all external communications

### 4. Backup & Recovery
```bash
# PostgreSQL backup
pg_dump $DATABASE_URL > backup.sql

# Restore
psql $DATABASE_URL < backup.sql

# Configuration backup
cp .env .env.backup
cp config/production.py config/production.py.backup
```

### 5. Scaling
- Use load balancer for multiple API instances
- Separate worker processes for trade execution
- Use message queue (Celery) for async tasks
- Monitor resource usage and scale horizontally

## Troubleshooting

### Service Won't Start
```bash
# Check logs
docker-compose logs angel-x
# or
sudo journalctl -u angel-x -n 50

# Common issues:
# - Database not running: sudo systemctl start postgresql
# - Port already in use: lsof -i :5000
# - Missing dependencies: pip install -r requirements.txt
```

### Broker Connection Fails
```bash
# Verify credentials in .env
# Test connectivity:
python3 -c "
from app.services.broker.angelone_adapter import AngelOneAdapter
adapter = AngelOneAdapter()
adapter.login()
"
```

### High Memory Usage
- Check if paper trading positions are accumulating
- Monitor database connection pool
- Clear old logs: `find logs/ -type f -mtime +30 -delete`

## CI/CD Integration

Angel-X includes GitHub Actions workflows:
- **test.yml**: Runs pytest on every push
- **docker.yml**: Builds Docker image and pushes to registry
- **security.yml**: Security scanning (bandit, safety, semgrep)

Configure GitHub Secrets:
- `DOCKER_USERNAME`
- `DOCKER_PASSWORD`

## Support & Monitoring

### Useful Commands
```bash
# Real-time market data check
curl http://localhost:5000/api/market-data/NIFTY

# Current positions
curl http://localhost:5000/api/positions

# Trade history
curl http://localhost:5000/api/trades

# Alert history
curl http://localhost:5000/monitor/alerts
```

### Performance Metrics
```bash
# Check CPU/Memory
top -u angel-x

# Database performance
psql $DATABASE_URL -c "SELECT * FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10;"

# API response time
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/monitor/health
```

## Emergency Procedures

### Graceful Shutdown
```bash
# Wait for active trades to complete
docker-compose down
# or
sudo systemctl stop angel-x
```

### Force Restart
```bash
docker-compose restart angel-x
# or
sudo systemctl restart angel-x
```

### Disable Trading
Set `ENABLE_TRADING=False` in .env and restart service.

---

## Additional Resources

- [Architecture Documentation](./architecture/README.md)
- [API Documentation](./api/README.md)
- [Configuration Guide](../config/README.md)
- [Troubleshooting](./troubleshooting.md)

For support: support@your-domain.com
