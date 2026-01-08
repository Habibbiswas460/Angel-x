# Angel-X Production Deployment Guide

## Version 10.0.0 - Complete Production Setup

---

## 🎯 Overview

This guide covers production deployment of Angel-X trading system with all 10 phases integrated.

**System Capabilities:**
- ✅ Phase 1-9: Core trading engines (Bias, Entry, Greeks, Smart Money, Market Bias)
- ✅ Phase 10: Adaptive Learning System with self-correction
- ✅ Real-time dashboard and monitoring
- ✅ Institutional-grade risk management
- ✅ Production-ready configuration management

---

## 📋 Prerequisites

### System Requirements
- **OS:** Linux (Ubuntu 20.04+ recommended) / Windows 10+ / macOS 10.15+
- **Python:** 3.8 - 3.11
- **RAM:** Minimum 4GB, Recommended 8GB+
- **Storage:** 10GB free space for logs and data
- **Network:** Stable internet connection with low latency

### Account Requirements
- AngelOne Trading Account (with API access)
- API Key, Client Code, and Password
- TOTP Secret for 2FA authentication

---

## 🚀 Installation

### Option 1: Standard Installation

```bash
# Clone repository
git clone https://github.com/angelx/Angel-x.git
cd Angel-x

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Install production dependencies
pip install -e .[production]
```

### Option 2: Development Installation

```bash
# Install with development tools
pip install -e .[dev]

# Verify installation
angelx-version
```

---

## ⚙️ Configuration

### 1. Copy Configuration Template

```bash
cp config/config.example.py config/config.py
```

### 2. Configure API Credentials

Edit `config/config.py`:

```python
# Section 1: ANGELONE API CREDENTIALS
API_KEY = "your_api_key_here"
CLIENT_CODE = "your_client_code"
PASSWORD = "your_password"
TOTP_SECRET = "your_totp_secret"

# Section 2: TRADING PARAMETERS
SYMBOL = "NIFTY"  # or "BANKNIFTY"
CAPITAL = 50000
MAX_POSITIONS = 2
RISK_PER_TRADE = 0.02  # 2% max risk per trade
```

### 3. Adaptive System Configuration

```python
# Section 12.5: ADAPTIVE LEARNING SYSTEM
ADAPTIVE_ENABLED = True
ADAPTIVE_MIN_SAMPLE_SIZE = 20
ADAPTIVE_MAX_DAILY_ADJUSTMENTS = 5
ADAPTIVE_MIN_LEARNING_INTERVAL = 24  # hours
```

### 4. Environment-Specific Settings

Create `.env` file:

```bash
# Production environment
ENV=production
DEBUG=False
SECRET_KEY=your-random-secret-key-change-this-in-production
ENCRYPTION_ENABLED=True

# Logging
LOG_LEVEL=INFO
MAX_LOG_SIZE_MB=100
BACKUP_COUNT=10
```

---

## 🔐 Security Setup

### 1. Generate Secret Key

```python
import secrets
print(secrets.token_hex(32))
```

Add to `.env`:
```bash
SECRET_KEY=<generated_key>
```

### 2. Enable Encryption (Production)

```python
# In config/config.py
ENCRYPTION_ENABLED = True
```

### 3. Secure Credentials Storage

**Never commit sensitive data to git:**

```bash
# .gitignore already includes:
config/config.py
.env
logs/
data/
*.key
```

---

## 🧪 Testing

### 1. Credentials Validation

```bash
python scripts/test_credentials.py
```

Expected output:
```
✅ AngelOne API credentials validated
✅ Connection successful
✅ Profile data retrieved
```

### 2. Integration Testing

```bash
# Test adaptive integration
python scripts/test_adaptive_integration.py
```

Expected: 6/6 tests passing

### 3. Quick Verification

```bash
# Verify all systems operational
python scripts/verify_integration.py
```

---

## 🏃 Running in Production

### Method 1: Direct Execution

```bash
# Activate environment
source venv/bin/activate

# Run main bot
python main.py
```

### Method 2: Using Console Script

```bash
# After pip install
angelx
```

### Method 3: Background Service (Systemd - Linux)

Create `/etc/systemd/system/angelx.service`:

```ini
[Unit]
Description=Angel-X Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/Angel-x
Environment="PATH=/path/to/Angel-x/venv/bin"
ExecStart=/path/to/Angel-x/venv/bin/python main.py
Restart=on-failure
RestartSec=10s

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable angelx
sudo systemctl start angelx
sudo systemctl status angelx
```

### Method 4: Using Supervisor

Install supervisor:
```bash
pip install supervisor
```

Create `angelx.conf`:

```ini
[program:angelx]
command=/path/to/venv/bin/python main.py
directory=/path/to/Angel-x
user=your_username
autostart=true
autorestart=true
stderr_logfile=/var/log/angelx/err.log
stdout_logfile=/var/log/angelx/out.log
```

Start:
```bash
supervisord -c angelx.conf
supervisorctl status angelx
```

---

## 📊 Dashboard Access

### Start Dashboard

```bash
# Separate terminal
python src/dashboard/dashboard.py

# Or using console script
angelx-dashboard
```

Access at: `http://localhost:5000`

**Dashboard Features:**
- Real-time P&L tracking
- Position monitoring
- Adaptive system status
- Learning insights
- Performance metrics

---

## 📝 Logging

### Log Structure

```
logs/
├── main.log              # Main bot logs
├── adaptive.log          # Adaptive system logs
├── dashboard.log         # Dashboard logs
├── errors.log            # Error-only logs
└── archive/              # Rotated logs (timestamped)
```

### Log Levels

```python
# Production (in .env)
LOG_LEVEL=INFO

# Development
LOG_LEVEL=DEBUG

# Minimal logging
LOG_LEVEL=WARNING
```

### Log Rotation

Automatic rotation when file exceeds 100MB:
- Keeps last 10 backup files
- Compressed format: `main.log.2024-01-15.gz`

---

## 🔍 Monitoring

### Health Checks

```python
# Check system health
from src.utils.greeks_health import GreeksHealthMonitor

monitor = GreeksHealthMonitor()
status = monitor.get_system_status()
print(status)
```

### Adaptive System Status

```python
from src.adaptive import AdaptiveController

adaptive = AdaptiveController()
status = adaptive.get_status()

print(f"Total Trades Learned: {status['total_trades']}")
print(f"Current Confidence: {status['overall_score']:.2%}")
print(f"Market Regime: {status['current_regime']}")
```

### Performance Tracking

```bash
# View dashboard at http://localhost:5000
angelx-dashboard

# Check performance tracker
from src.dashboard import PerformanceTracker

tracker = PerformanceTracker()
metrics = tracker.get_daily_metrics()
```

---

## 🛡️ Safety Features

### 1. Position Limits

```python
# config/config.py
MAX_POSITIONS = 2
MAX_OPEN_ORDERS = 3
```

### 2. Loss Limits

```python
MAX_DAILY_LOSS = 0.05  # 5% of capital
MAX_LOSS_PER_TRADE = 0.02  # 2% per trade
```

### 3. Adaptive Safety Guards

```python
ADAPTIVE_SHADOW_TEST_MODE = False  # Set True for testing
ADAPTIVE_EMERGENCY_RESET_ON_LOSS_STREAK = 5
ADAPTIVE_AUTO_REVIEW_INTERVAL = 7  # days
```

### 4. Circuit Breaker

```python
# Automatic shutdown on excessive losses
CIRCUIT_BREAKER_ENABLED = True
CIRCUIT_BREAKER_LOSS_THRESHOLD = 0.10  # 10%
```

---

## 🔧 Troubleshooting

### Issue: API Connection Failed

```bash
# Test credentials
python scripts/test_credentials.py

# Check network
ping api.angelone.in

# Verify TOTP sync
# Ensure system time is accurate
```

### Issue: Adaptive System Not Learning

```python
# Check minimum sample size
# Default: 20 trades required

# Force learning cycle
adaptive = AdaptiveController()
adaptive.daily_learning_cycle()
```

### Issue: Dashboard Not Loading

```bash
# Check port availability
lsof -i :5000

# Try different port
FLASK_RUN_PORT=8080 angelx-dashboard
```

### Issue: High Memory Usage

```bash
# Clear old logs
find logs/ -name "*.log.*" -mtime +30 -delete

# Reduce log level
LOG_LEVEL=WARNING

# Limit trade history in memory
MAX_TRADES_IN_MEMORY = 1000  # In config
```

---

## 📈 Performance Optimization

### 1. Database Setup (Optional)

For production scale, consider database:

```bash
pip install sqlalchemy psycopg2-binary

# Configure in config/config.py
DATABASE_URL = "postgresql://user:pass@localhost/angelx"
USE_DATABASE = True
```

### 2. Caching

```python
# Enable Redis caching (optional)
REDIS_ENABLED = True
REDIS_HOST = "localhost"
REDIS_PORT = 6379
```

### 3. Multi-Symbol Trading

```python
# Trade multiple symbols
SYMBOLS = ["NIFTY", "BANKNIFTY", "FINNIFTY"]
CAPITAL_PER_SYMBOL = CAPITAL / len(SYMBOLS)
```

---

## 🔄 Updating

### Pulling Latest Changes

```bash
# Stop bot
sudo systemctl stop angelx  # Or Ctrl+C

# Pull updates
git pull origin main

# Update dependencies
pip install -e . --upgrade

# Run tests
python scripts/test_adaptive_integration.py

# Restart bot
sudo systemctl start angelx
```

### Version Check

```bash
angelx-version

# Output:
# ============================================
# Angel-X Trading System v10.0.0
# Institutional-Grade Algorithmic Trading
# ============================================
# Status: 10/10 Phases Complete
```

---

## 📊 Production Checklist

Before going live:

- [ ] API credentials configured and tested
- [ ] Secret key changed from default
- [ ] Encryption enabled (`ENCRYPTION_ENABLED=True`)
- [ ] Environment set to production (`ENV=production`)
- [ ] Log rotation configured
- [ ] Position/loss limits set appropriately
- [ ] Dashboard accessible
- [ ] All integration tests passing (6/6)
- [ ] Credentials test passing
- [ ] Backup strategy in place
- [ ] Monitoring alerts configured
- [ ] Emergency stop procedure documented
- [ ] Small capital test run completed

---

## 🆘 Emergency Procedures

### Emergency Stop

```bash
# Immediate shutdown
sudo systemctl stop angelx

# Or if running directly
# Press Ctrl+C in terminal

# Close all positions manually via AngelOne app/web
```

### Reset Adaptive System

```python
# In Python REPL or script
from src.adaptive import AdaptiveController

adaptive = AdaptiveController()
adaptive.reset_weights()
adaptive.clear_history()

print("Adaptive system reset to defaults")
```

### Disaster Recovery

```bash
# Backup critical data
cp -r data/ data_backup_$(date +%Y%m%d)/
cp config/config.py config_backup.py
cp logs/main.log logs/main_backup.log

# Restore from backup
cp data_backup_20240115/adaptive_state.json data/
```

---

## 📞 Support

### Documentation
- [Phase 10 Integration Guide](PHASE10_INTEGRATION_COMPLETE.md)
- [Quick Reference](PHASE10_INTEGRATION_SUMMARY.md)
- [API Documentation](docs/)

### Community
- GitHub Issues: [Report bugs/features]
- Discord: [Community support]
- Email: contact@angelx.dev

---

## 📄 License

MIT License - See [LICENSE](../LICENSE) file

---

## ✅ Production Success Indicators

**System is production-ready when:**
1. ✅ All 10 phases operational
2. ✅ 6/6 integration tests passing
3. ✅ Credentials validated
4. ✅ Dashboard accessible
5. ✅ Adaptive learning functional
6. ✅ Logs rotating properly
7. ✅ Safety guards active
8. ✅ Test trades executing correctly

**First Week Monitoring:**
- Monitor every trade execution
- Review adaptive learning decisions
- Check log files daily
- Verify P&L tracking accuracy
- Validate position sizing
- Ensure risk limits respected

**Ongoing Maintenance:**
- Weekly performance review
- Monthly adaptive system audit
- Quarterly dependency updates
- Regular backup verification

---

**Angel-X v10.0.0 - Production Ready ✅**

*Last Updated: 2024-01-15*
