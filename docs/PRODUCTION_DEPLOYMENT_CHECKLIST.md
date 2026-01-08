# Production Deployment Checklist - Angel-X Trading System

## 🎯 Pre-Deployment Verification

### Code & Build
- [ ] All 7 phases completed and verified
- [ ] Unit tests passing (3/3)
- [ ] Integration tests passing (4/4)
- [ ] E2E tests passing (9/9)
- [ ] Import paths migrated (76 files)
- [ ] Dockerfile validated
- [ ] Docker image builds successfully
- [ ] Requirements.txt complete and tested

### Configuration
- [ ] config/config.py created from config.example.py
- [ ] Production credentials configured
- [ ] Environment variables set correctly
- [ ] Database connection details verified
- [ ] Broker credentials configured
- [ ] API keys and secrets secured
- [ ] Timezone set to Asia/Kolkata
- [ ] Log level set to INFO or WARN

### Database
- [ ] PostgreSQL database created (angelx_ml)
- [ ] Database schema initialized
- [ ] User permissions configured (angelx user)
- [ ] Connection pool size appropriate (8-16)
- [ ] Backup strategy in place
- [ ] Migration scripts tested

### Security
- [ ] No hardcoded credentials in code
- [ ] Secrets stored in environment variables
- [ ] SSL/TLS certificates configured (if applicable)
- [ ] Firewall rules configured
- [ ] Port 5000 accessible only from intended sources
- [ ] .env file added to .gitignore
- [ ] Credentials not committed to git
- [ ] Read-only permissions on config files

### Infrastructure
- [ ] Docker daemon running
- [ ] Docker networks created
- [ ] Volume directories created and permissions set
- [ ] Resource limits configured
- [ ] Log rotation configured
- [ ] Backup storage available
- [ ] Monitoring infrastructure accessible

### Monitoring
- [ ] Prometheus configured and accessible
- [ ] Grafana accessible and configured
- [ ] Alert rules verified
- [ ] Alert notification channels tested
- [ ] Dashboards loaded and functional
- [ ] Health check endpoints responding
- [ ] Metrics collection working

### System Requirements Verified
- [ ] Python 3.12+ available
- [ ] Docker installed (version 20+)
- [ ] Docker Compose installed (version 1.29+)
- [ ] Minimum 4GB RAM available
- [ ] Minimum 10GB disk space available
- [ ] Network connectivity verified
- [ ] Broker API accessible
- [ ] Market data feed accessible

## 🚀 Deployment Steps

### 1. Initial Deployment

```bash
# 1. Navigate to project directory
cd /home/lora/git_clone_projects/Angel-x

# 2. Set production environment
export ENVIRONMENT=production
export TRADING_ENABLED=false  # Enable after verification

# 3. Create required directories
mkdir -p logs data backups

# 4. Verify configuration
python3 -c "from config.config import *; print('Config loaded successfully')"

# 5. Build Docker image
./deploy.sh build

# 6. Start application
./deploy.sh run

# 7. Wait for startup (40 seconds for health check)
sleep 45

# 8. Verify health
./deploy.sh health

# 9. Check logs
./deploy.sh logs
```

### 2. System Verification

```bash
# Check API responding
curl -v http://localhost:5000/monitor/health

# Check Prometheus scraping
curl http://localhost:9090/api/v1/targets

# Check Grafana accessible
curl http://localhost:3000/api/health

# Verify database connection
curl http://localhost:5000/monitor/health | grep database

# Check broker connection
curl http://localhost:5000/monitor/health | grep broker
```

### 3. Smoke Tests

```bash
# Test API endpoint
curl -X GET http://localhost:5000/api/health

# Test market data endpoint
curl -X GET http://localhost:5000/api/market-data/NSE

# Test trading endpoint (should return empty or demo data)
curl -X GET http://localhost:5000/api/trades

# Test health endpoint
curl -X GET http://localhost:5000/monitor/health
```

### 4. Enable Live Trading (When Ready)

```bash
# Only after all tests pass!
docker exec angel-x-trading bash -c "export TRADING_ENABLED=true"

# Or update environment and restart
docker stop angel-x-trading
export TRADING_ENABLED=true
./deploy.sh run
```

## 📊 Monitoring & Verification

### Production Monitoring
- [ ] Access Grafana dashboards
- [ ] Verify System Overview Dashboard
- [ ] Verify Trading Metrics Dashboard
- [ ] Check alert thresholds appropriate
- [ ] Verify no immediate alerts firing
- [ ] Monitor for 24 hours in demo mode

### Performance Verification
- [ ] API response time < 500ms
- [ ] Broker latency < 1 second
- [ ] Database queries < 100ms
- [ ] Memory usage stable (< 2GB)
- [ ] CPU usage < 50% at idle
- [ ] No continuous error logs

### Trading System Verification
- [ ] Market data updating correctly
- [ ] Option chain refreshing
- [ ] Greeks calculating
- [ ] Signals generating
- [ ] Position tracking working
- [ ] P&L calculations accurate

## 🔄 Post-Deployment Tasks

### Monitoring Setup
```bash
# Access Grafana at http://localhost:3000
# 1. Login (admin/admin)
# 2. Change password
# 3. Add AlertManager configuration
# 4. Setup notification channels (email, Slack, etc.)
# 5. Create custom dashboards if needed
```

### Backup Configuration
```bash
# Setup daily backups
sudo crontab -e

# Add: 0 2 * * * /home/lora/git_clone_projects/Angel-x/backup.sh

# Create backup script
chmod +x backup.sh
```

### Log Rotation
```bash
# Configure logrotate
sudo nano /etc/logrotate.d/angel-x

# Add:
/home/lora/git_clone_projects/Angel-x/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 angelx angelx
}
```

## 📋 Configuration Checklist

### Production Settings
- [ ] ENVIRONMENT=production
- [ ] DEBUG=false
- [ ] LOG_LEVEL=INFO
- [ ] TRADING_ENABLED=false (initially)
- [ ] DATABASE_URL set correctly
- [ ] BROKER_CREDENTIALS set
- [ ] API_KEYS configured
- [ ] TIMEZONE=Asia/Kolkata

### Docker Settings
- [ ] Image tagged with version (1.0.0)
- [ ] Restart policy: unless-stopped
- [ ] Memory limit: 4GB
- [ ] CPU limit: 2 cores
- [ ] Health check enabled
- [ ] Volumes mounted correctly
- [ ] Network isolation configured

### Monitoring Settings
- [ ] Prometheus retention: 15d
- [ ] Scrape interval: 15s
- [ ] Alert evaluation: 30s
- [ ] Alert notification delay: 5m
- [ ] Grafana session timeout: 12h

## 🆘 Emergency Procedures

### Container Issues
```bash
# Stop container
docker stop angel-x-trading

# Remove container (keeps volumes)
docker rm angel-x-trading

# Restart fresh
./deploy.sh run

# Check logs
docker logs -f angel-x-trading --tail 100
```

### Database Issues
```bash
# Verify connection
psql -U angelx -d angelx_ml -c "SELECT 1"

# Check pool status
curl http://localhost:5000/monitor/health | grep pool

# Restart container to reset pool
docker restart angel-x-trading
```

### Broker Connection Issues
```bash
# Verify broker API accessible
curl https://api.angelone.in/health

# Check credentials
python3 scripts/test_credentials.py

# Review logs for broker errors
docker logs angel-x-trading | grep broker
```

### Trading Stall
```bash
# Check if trading is enabled
curl http://localhost:5000/monitor/health | grep trading

# Check for errors
docker logs angel-x-trading | grep ERROR

# Verify market data flowing
curl http://localhost:5000/api/market-data/NSE

# Restart trading engine
docker restart angel-x-trading
```

## 📈 Performance Tuning

### Optimization Parameters
- [ ] Database connection pool: 8-16
- [ ] API worker threads: 4-8
- [ ] Greeks cache size: 10000
- [ ] Market data buffer: 1000
- [ ] Order queue depth: 100

### Resource Limits
```yaml
# In docker-compose.yml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G
```

## 🎯 Success Criteria

### All criteria must be met for production deployment:
- [ ] All 7 phases completed (100%)
- [ ] 16/16 tests passing (100%)
- [ ] Health check endpoint responding
- [ ] Monitoring dashboards functional
- [ ] Alert rules configured
- [ ] No ERROR level logs
- [ ] API response time < 500ms
- [ ] Broker connection established
- [ ] Database connection working
- [ ] 24-hour stability achieved
- [ ] No memory leaks detected
- [ ] Backup process verified

## 📞 Rollback Plan

If critical issues occur after deployment:

1. **Immediate**: Stop trading by setting TRADING_ENABLED=false
2. **Container**: Stop and remove current container
3. **Database**: Restore from latest backup if data corruption
4. **Code**: Rollback to previous version tag
5. **Verify**: Re-run all health checks
6. **Resume**: Restart in safe mode before resuming trading

## ✅ Sign-Off

- [ ] DevOps Lead reviewed and approved
- [ ] QA verified all test cases
- [ ] Security reviewed configuration
- [ ] Business approved trading parameters
- [ ] Documentation complete and reviewed
- [ ] Runbook created and tested
- [ ] Support team trained
- [ ] Deployment authorized

---

**Deployment Date**: ________________
**Deployed By**: ________________
**Verified By**: ________________
**Status**: ⬜ Pending → 🟦 In Progress → 🟩 Completed
