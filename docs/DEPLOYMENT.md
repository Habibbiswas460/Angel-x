# Production Deployment Guide

## Pre-Deployment Checklist

- [ ] All credentials configured (config/config.py)
- [ ] Database schema created
- [ ] Logs directory created
- [ ] Broker connectivity tested
- [ ] ML models trained
- [ ] Tests passing

## Deployment Steps

### 1. Prepare Environment

```bash
# Clone and setup
git clone <repo>
cd Angel-x

# Create config file
cp config/config.example.py config/config.py
# Edit with real credentials

# Create .env file
cat > .env << EOF
# Broker
ANGELONE_CLIENT_CODE=your_code
ANGELONE_API_KEY=your_key
ANGELONE_FEED_TOKEN=your_token

# Alerts
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Database
POSTGRES_PASSWORD=secure_password_here

# Grafana
GRAFANA_PASSWORD=strong_password_here
EOF

# Create required directories
mkdir -p logs data ticks
```

### 2. Build and Test Locally

```bash
# Build image
docker build -t angelx:latest .

# Test with docker-compose
docker-compose up -d angel-x postgres

# Check health
curl http://localhost:5000/health

# View logs
docker-compose logs -f angel-x

# Run tests
docker-compose exec angel-x pytest tests/
```

### 3. Enable Monitoring (Optional)

```bash
# Start monitoring stack
docker-compose --profile monitoring up -d

# Access dashboards
# Prometheus: http://localhost:9090
# Grafana: http://localhost:3000
```

### 4. Production Deployment

#### Option A: Docker Swarm

```bash
# Initialize swarm
docker swarm init

# Create network
docker network create -d overlay angelx-network

# Deploy stack
docker stack deploy -c docker-compose.yml angelx

# Check status
docker stack services angelx
```

#### Option B: Kubernetes

```bash
# Create namespace
kubectl create namespace angelx

# Create secrets
kubectl create secret generic angelx-secrets \
  --from-literal=api-key=$ANGELONE_API_KEY \
  --from-literal=client-code=$ANGELONE_CLIENT_CODE \
  -n angelx

# Deploy
kubectl apply -f infra/kubernetes/ -n angelx

# Check pods
kubectl get pods -n angelx
```

#### Option C: Cloud (AWS, GCP, Azure)

```bash
# ECS Fargate (AWS)
ecs-cli compose -f docker-compose.yml up

# Cloud Run (GCP)
gcloud run deploy angelx \
  --source . \
  --platform managed \
  --region us-central1

# Container Instances (Azure)
az container create \
  --resource-group angelx \
  --name angelx-trading \
  --image angelx:latest
```

### 5. Post-Deployment Verification

```bash
# Check health
curl -s http://localhost:5000/health | jq .

# Check API
curl -s http://localhost:5000/api/dashboard | jq '.status'

# Check broker
curl -s http://localhost:5000/api/market | jq '.broker_status'

# Check metrics
curl -s http://localhost:5000/metrics/prometheus | head -20
```

## Monitoring Setup

### Grafana Dashboards

```bash
# Access Grafana
# URL: http://localhost:3000
# Default: admin/admin

# Import dashboards:
# 1. Trading System Overview
# 2. Market Metrics
# 3. Strategy Performance
# 4. System Health
```

### Alerting Rules

Create `infra/monitoring/alert.rules.yml`:

```yaml
groups:
  - name: angelx
    interval: 30s
    rules:
      - alert: BrokerDown
        expr: angelx_broker_connected == 0
        for: 1m
        annotations:
          summary: Broker connection lost

      - alert: HighErrorRate
        expr: rate(angelx_errors_total[5m]) > 0.05
        for: 5m
        annotations:
          summary: Error rate above 5%

      - alert: HighMemory
        expr: angelx_memory_mb > 2000
        for: 5m
        annotations:
          summary: Memory usage > 2GB

      - alert: NoPredictions
        expr: angelx_model_predictions == 0
        for: 10m
        annotations:
          summary: ML model not making predictions
```

### Telegram Integration

Set up Telegram alerts:

```bash
# Create bot
# 1. Message @BotFather on Telegram
# 2. Create new bot: /newbot
# 3. Get bot token
# 4. Get your chat ID:
#    - Message bot: /start
#    - Get chat_id from: https://api.telegram.org/bot<TOKEN>/getUpdates

# Add to .env
TELEGRAM_BOT_TOKEN=<bot_token>
TELEGRAM_CHAT_ID=<your_chat_id>
```

## Scaling Considerations

### Horizontal Scaling

For multiple instances:

```yaml
version: '3.8'
services:
  angel-x:
    deploy:
      replicas: 3
      placement:
        constraints:
          - node.role == worker
    networks:
      - angel-x-network
    depends_on:
      - postgres
      - redis-cache  # Add for session sharing
```

### Load Balancing

```bash
# Add nginx load balancer
docker-compose -f docker-compose.yml \
               -f docker-compose.lb.yml \
               up -d
```

### Database Optimization

```sql
-- Create indices
CREATE INDEX idx_trades_date ON trades(created_at);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_performance_time ON performance(timestamp);

-- Enable connection pooling
-- Set in config: pool_size=10, max_overflow=20
```

## Backup & Recovery

### Database Backup

```bash
# Backup PostgreSQL
docker-compose exec postgres pg_dump -U angelx angelx_ml > backup.sql

# Restore
docker-compose exec -T postgres psql -U angelx angelx_ml < backup.sql
```

### Volume Backup

```bash
# Backup volumes
docker run --rm -v angelx_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres.tar.gz -C /data .

# Restore
docker run --rm -v angelx_postgres-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/postgres.tar.gz -C /data
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs angel-x

# Check image
docker images | grep angelx

# Rebuild
docker-compose build --no-cache angel-x

# Clean restart
docker-compose down -v
docker-compose up -d
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Increase limits in docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '1'
      memory: 2G
    reservations:
      cpus: '0.5'
      memory: 1G
```

### Broker Connection Failures

```bash
# Check credentials
cat config/config.py | grep ANGELONE

# Test connection manually
python3 -c "from src.integrations.broker_integration import get_broker; print(get_broker().connect())"

# Check network
curl -I https://smartapi.angelbroking.com

# View logs
docker-compose logs broker
```

## Maintenance

### Regular Tasks

```bash
# Weekly
- Review logs for errors
- Check database size
- Verify backups
- Test disaster recovery

# Monthly
- Update dependencies
- Review performance metrics
- Clean old data
- Update documentation
```

### Updates

```bash
# Safe deployment
docker-compose pull
docker-compose up -d

# Watch health
watch -n 1 'curl -s http://localhost:5000/health'

# Rollback if needed
docker-compose up -d angel-x:previous-tag
```

## Cost Optimization

- Use spot instances for backtesting
- Scale down monitoring during low-volume hours
- Archive old logs to cold storage
- Use CDN for static dashboards

## Security

```bash
# Generate HTTPS certificates
certbot certonly --standalone -d yourdomain.com

# Add to docker-compose for SSL
volumes:
  - /etc/letsencrypt:/etc/letsencrypt:ro

# Update nginx config to use SSL
```

## Support

- Documentation: `/docs/`
- Issue tracking: GitHub Issues
- Logs: `/logs/`
- Metrics: `http://localhost:9090`
- Dashboard: `http://localhost:3000`
