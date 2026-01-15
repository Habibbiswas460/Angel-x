# 🚀 Angel-X Deployment Checklist

## Pre-Deployment Verification

### 1. Environment Setup
- [ ] Python 3.8+ installed
- [ ] Docker & Docker Compose installed (for containerized deployment)
- [ ] PostgreSQL database accessible
- [ ] AngelOne trading account with API credentials

### 2. Configuration
- [ ] Copy `.env.example` to `.env.production`
- [ ] Set `ANGELONE_API_KEY` and `ANGELONE_CLIENT_ID`
- [ ] Set `ANGELONE_PASSWORD` and `ANGELONE_TOTP_SECRET`
- [ ] Configure database credentials (`DB_HOST`, `DB_USER`, `DB_PASSWORD`)
- [ ] Set `ENVIRONMENT=production`
- [ ] Review risk parameters in `config/settings.py`

### 3. Security Checks
- [ ] No `.env` files committed to git
- [ ] API credentials are secure
- [ ] Database password is strong
- [ ] SSL/TLS enabled for database connections
- [ ] Firewall rules configured
- [ ] Log rotation configured

### 4. Database Setup
```bash
# Initialize database
python init_db.py

# Verify tables created
python -c "from app.domains.database import verify_database; verify_database()"
```

### 5. Dependency Check
```bash
# Install production dependencies
pip install -r requirements.txt

# Validate configuration
python validate_config.py
```

## Deployment Options

### Option A: Docker Deployment (Recommended)
```bash
# Build and start containers
./docker-deploy.sh

# Verify containers running
docker-compose ps

# Check logs
docker-compose logs -f angelx
```

### Option B: Direct Deployment
```bash
# Run production deployment script
./production-deploy.sh

# Or start manually
python main.py
```

### Option C: Systemd Service (Linux)
```bash
# Copy systemd service file
sudo cp infra/systemd/angelx.service /etc/systemd/system/

# Enable and start service
sudo systemctl enable angelx
sudo systemctl start angelx
sudo systemctl status angelx
```

## Post-Deployment Verification

### 1. Health Checks
- [ ] Application started successfully
- [ ] Database connection established
- [ ] WebSocket connection to AngelOne active
- [ ] All strategies loaded
- [ ] Monitoring endpoints responding

```bash
# Check application health
curl http://localhost:5000/health

# Verify WebSocket connection
curl http://localhost:5000/api/v1/status/websocket
```

### 2. Trading Verification
- [ ] Start with paper trading mode (`PAPER_TRADING=true`)
- [ ] Monitor first 30 minutes without real orders
- [ ] Verify signal generation working
- [ ] Check order execution flow (dry-run)
- [ ] Review logs for any errors

### 3. Monitoring Setup
- [ ] Prometheus metrics accessible at `:9090/metrics`
- [ ] Grafana dashboard configured (if using)
- [ ] Alert rules configured
- [ ] Log aggregation working
- [ ] Health check alerts enabled

## Production Checklist

### Before Going Live
- [ ] Tested thoroughly in paper trading mode (minimum 7 days)
- [ ] All alerts and notifications working
- [ ] Capital allocation verified
- [ ] Risk limits configured correctly
- [ ] Stop-loss mechanisms tested
- [ ] Backup and recovery procedures in place
- [ ] Monitoring dashboards accessible

### Risk Management
- [ ] Max position size configured
- [ ] Max daily loss limit set
- [ ] Circuit breaker thresholds defined
- [ ] Emergency stop procedures documented
- [ ] Contact information for support updated

### Compliance
- [ ] Trading within account limits
- [ ] Proper logging for audit trail
- [ ] Data retention policy configured
- [ ] Regulatory requirements reviewed

## Rollback Procedure

If deployment fails:
```bash
# Stop the application
docker-compose down
# OR
sudo systemctl stop angelx

# Restore previous version
git checkout <previous-version-tag>

# Redeploy
./docker-deploy.sh
```

## Support & Monitoring

### Log Locations
- Application logs: `logs/angelx_YYYYMMDD.log`
- Trade logs: `logs/trades_YYYYMMDD.log`
- Error logs: `logs/error_YYYYMMDD.log`

### Monitoring Commands
```bash
# View real-time logs
tail -f logs/angelx_$(date +%Y%m%d).log

# Check system resources
docker stats

# Database connections
docker-compose exec db psql -U angelx -c "SELECT count(*) FROM pg_stat_activity;"
```

## Emergency Contacts
- System Admin: [Your Contact]
- Trading Desk: [Broker Contact]
- Technical Support: [Support Email]

---

**Version:** 2.1.0  
**Last Updated:** 2026-01-15  
**Deployment Environment:** Production
