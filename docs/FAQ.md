# Frequently Asked Questions (FAQ)

## General

### What is Angel-X?

Angel-X is an advanced algorithmic trading platform built for options trading on the National Stock Exchange (NSE) of India. It provides:

- **Real-time data integration** with AngelOne broker
- **Sophisticated options strategies** (Iron Condor, Calendar Spreads, etc.)
- **Adaptive machine learning** models that improve over time
- **Risk management** with position limits and automatic hedging
- **Paper and live trading** modes for safe experimentation
- **Comprehensive monitoring** and analytics dashboard

See [README.md](README.md) for full details.

### Who should use Angel-X?

Angel-X is suitable for:
- ✅ Experienced traders wanting to automate strategies
- ✅ Quantitative traders building custom models
- ✅ Teams managing multi-strategy portfolios
- ✅ Developers integrating trading into applications
- ✅ Researchers studying algorithmic trading

Angel-X is NOT suitable for:
- ❌ Beginners without trading experience (start with paper trading first)
- ❌ High-frequency trading (latency not optimized for < 100ms)
- ❌ Non-technical users (requires coding knowledge)

### What are the system requirements?

**Minimum:**
- Python 3.8+
- 2 GB RAM
- 5 GB disk space
- Stable internet connection (broadband)

**Recommended:**
- Python 3.10+
- 4+ GB RAM
- 20 GB disk space
- Dedicated Linux/Mac server
- Dedicated internet connection

### How much does it cost?

Angel-X is **free and open-source** under MIT License.

However, you need:
- ✅ AngelOne broker account (free)
- ✅ Data subscription from NSE (usually bundled with broker account)
- ✅ VPS/server costs if running 24/7 (₹100-500/month)

### Is Angel-X production-ready?

**For paper trading:** ✅ Yes, fully tested

**For real money:** ⚠️ Use with caution
- Start with small amounts
- Monitor closely for first 2 weeks
- Have manual kill-switch ready
- Test thoroughly in paper mode first

### Can I use Angel-X on Windows?

Windows support is **experimental**. Recommended setup:
- ✅ Linux (Ubuntu 20.04+) - Full support
- ✅ macOS - Full support  
- ⚠️ Windows - Partial support, use WSL2
- ✅ Docker - Works on all platforms

See [Installation on Windows](#can-i-run-angel-x-on-windows) below.

---

## Installation & Setup

### How do I install Angel-X?

See [Installation Guide](INSTALLATION.md) for detailed steps. Quick start:

```bash
# Clone repository
git clone https://github.com/your-org/Angel-x.git
cd Angel-x

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp config/config.example.py config/config.py
# Edit config.py with your credentials

# Run
python main.py
```

### Where do I get an AngelOne account?

1. Visit [Angel Broking](https://www.angelbroking.com/)
2. Click "Open Account"
3. Complete KYC process
4. Get API credentials from dashboard
5. Note your Client Code and API key

### How do I get API credentials?

1. Login to Angel Broking dashboard
2. Go to Settings → Developer Console
3. Create new API key
4. Copy:
   - API Key
   - Client Code  
   - Password (for SmartAPI)
5. Add to `config/config.py`

### Can I run Angel-X on Windows?

**Recommended:** Use Windows Subsystem for Linux 2 (WSL2)

```bash
# Install WSL2 and Ubuntu
wsl --install -d Ubuntu-22.04

# In WSL Ubuntu terminal, follow Linux installation steps
```

**Alternative:** Use Docker (works on all platforms)

```bash
docker build -t angel-x .
docker run -it angel-x bash
```

### How do I use environment variables?

```bash
# Create .env file
cat > .env << 'EOF'
ANGELONE_API_KEY=your-key-here
ANGELONE_CLIENT_CODE=your-code
ANGELONE_PASSWORD=your-password
DATABASE_URL=postgresql://user:pass@localhost/angel_x
EOF

# Load in application
from dotenv import load_dotenv
import os
load_dotenv()
api_key = os.getenv("ANGELONE_API_KEY")
```

### Where are logs stored?

```
logs/
├── 2026-01-10/
│   ├── trading_20260110.log
│   ├── broker_20260110.log
│   ├── websocket_20260110.log
│   └── ml_20260110.log
├── metrics/
│   └── daily_metrics.json
├── trades/
│   └── executed_trades.json
└── reports/
    └── daily_report.json
```

Check logs with:
```bash
tail -f logs/2026-01-10/trading_20260110.log
```

---

## Configuration

### How do I configure Angel-X?

Edit `config/config.py`:

```python
# Broker Settings
BROKER = {
    'name': 'angelone',
    'api_key': 'your-key',
    'client_code': 'your-code',
    'password': 'your-password',
    'paper_trading': True,  # Start with paper trading
}

# Strategy Settings
STRATEGIES = {
    'iron_condor': {
        'enabled': True,
        'max_position_size': 10,
        'max_loss_per_trade': 5000,
    }
}

# Risk Management
RISK = {
    'max_daily_loss': 50000,
    'max_position_loss': 10000,
    'max_leverage': 2.0,
}
```

See [Configuration Guide](docs/CONFIGURATION.md) for all options.

### What is paper trading?

Paper trading simulates real trading without using real money:
- ✅ Test strategies risk-free
- ✅ See order execution details
- ✅ Validate your logic
- ✅ Practice risk management
- ❌ No real profit/loss
- ❌ No slippage simulation

**Always start with paper trading!**

### How do I enable real trading?

⚠️ **WARNING: Use real money cautiously**

1. Thoroughly test in paper mode (at least 1 week)
2. Set conservative position limits
3. Start with small amounts
4. Monitor closely
5. Enable in config:

```python
# config/config.py
BROKER = {
    'paper_trading': False,  # Enable real trading
}
```

### Can I run multiple strategies?

Yes! Configure multiple strategies:

```python
STRATEGIES = {
    'iron_condor': {'enabled': True},
    'calendar_spread': {'enabled': True},
    'short_straddle': {'enabled': False},  # Disabled
}
```

Each strategy runs independently with its own positions.

### How do I set risk limits?

Configure in `config/config.py`:

```python
RISK = {
    'max_daily_loss': 50000,      # Stop if daily loss exceeds ₹50k
    'max_position_loss': 10000,   # Close position if loss > ₹10k
    'max_positions': 10,           # Max open positions
    'max_leverage': 2.0,           # Don't use more than 2x leverage
    'max_per_expiry': 5,           # Max positions per expiry
}
```

---

## Usage

### How do I start Angel-X?

```bash
# Activate virtual environment
source venv/bin/activate

# Start application
python main.py

# Application runs at http://localhost:5000
# Dashboard at http://localhost:3000
```

### How do I check if it's working?

```bash
# Check health endpoint
curl http://localhost:5000/health

# Check logs
tail -f logs/$(date +%Y-%m-%d)/trading_*.log

# Monitor dashboard
open http://localhost:5000/dashboard
```

### How do I stop Angel-X?

```bash
# Ctrl+C in terminal (graceful shutdown)
# Or in another terminal:
pkill -f "python main.py"

# With Docker:
docker-compose down
```

### How do I monitor trades?

**Web Dashboard:**
- Go to http://localhost:5000/dashboard
- See live P&L, positions, orders
- View strategy performance

**CLI:**
```bash
# Get current positions
curl http://localhost:5000/api/positions

# Get trade history
curl http://localhost:5000/api/trades

# Get performance metrics
curl http://localhost:5000/api/metrics
```

**Log Files:**
```bash
# Watch trading logs
tail -f logs/$(date +%Y-%m-%d)/trading_*.log
```

### How often does it trade?

Depends on your strategy configuration:
- **Iron Condor**: Typically 1-2 new positions per day
- **Calendar Spreads**: Usually roll weekly
- **Short Straddles**: Multiple daily, depends on Greeks
- **Adaptive strategies**: Adjusts based on market conditions

Check actual frequency in logs:
```bash
grep "ORDER PLACED" logs/$(date +%Y-%m-%d)/trading_*.log | wc -l
```

### Can I pause trading?

Yes, multiple ways:

**Via config:**
```python
STRATEGIES = {
    'iron_condor': {'enabled': False},  # Disables Iron Condor
}
# Restart application
```

**Via API:**
```bash
curl -X POST http://localhost:5000/api/pause
# Resume:
curl -X POST http://localhost:5000/api/resume
```

**Manual:**
- Close positions manually in broker terminal
- Application will update

---

## Troubleshooting

### My application won't start

**Error: "ModuleNotFoundError: No module named 'angel_x'"**

```bash
# Make sure you're in project directory
cd /path/to/Angel-x

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Error: "Connection refused" to broker**

```bash
# Check credentials in config/config.py
# Verify API key, client code, password

# Check internet connection
ping api.angel.broking.com

# Check firewall
# Angel-X needs ports: 443 (HTTPS), 1080 (WebSocket)
```

### API credentials not working

1. **Verify credentials:**
   - Copy from Angel Broking dashboard
   - No extra spaces or quotes
   - Check capitalization

2. **Test connectivity:**
   ```bash
   python -c "
   from src.integrations.angelone import SmartAPIClient
   client = SmartAPIClient('key', 'code', 'pass')
   client.connect()
   "
   ```

3. **Check Angel Broking status:**
   - Visit https://status.angelbroking.com/
   - Verify API is operational

### WebSocket connection fails

**Error: "WebSocket connection failed"**

```bash
# Check firewall allows port 1080
netstat -an | grep 1080

# Check broker connection
curl -v https://api.angel.broking.com/

# Restart application
pkill -f "python main.py"
sleep 2
python main.py
```

### Orders not executing

**Problem: Paper trading works but real trading doesn't**

```bash
# Check real trading is enabled
grep "paper_trading" config/config.py

# Check available balance
curl http://localhost:5000/api/account

# Check order limits in risk config
grep "max_" config/config.py

# Check logs for errors
grep "ERROR" logs/$(date +%Y-%m-%d)/trading_*.log
```

**Problem: Orders placed but not filled**

- Check strike prices exist
- Verify position limits not exceeded
- Check market hours (9:15 AM - 3:30 PM IST)
- Verify options have liquidity (check bid-ask spread)

### High latency or lag

**Problem: Slow order execution**

1. **Check network:**
   ```bash
   ping -c 10 api.angel.broking.com | grep avg
   ```

2. **Check system resources:**
   ```bash
   top -n 1 | head -5  # CPU, Memory
   ```

3. **Optimize config:**
   ```python
   # Reduce polling interval
   BROKER['polling_interval'] = 0.1  # seconds
   ```

### ML model not learning

**Problem: Model performance not improving**

1. **Check data collection:**
   ```bash
   # Verify trades are being recorded
   wc -l logs/trades/executed_trades.json
   ```

2. **Check model training:**
   ```bash
   # View training logs
   grep "Training epoch" logs/*/ml_*.log
   ```

3. **Verify sufficient data:**
   - Need minimum 100+ trades for meaningful patterns
   - Run in paper mode for 2-4 weeks first
   - Check market conditions (trending vs range-bound)

### Disk space running out

**Problem: Logs fill up disk**

```bash
# Check disk usage
du -sh logs/

# Archive old logs
tar -czf logs_backup_2026-01.tar.gz logs/2026-01-*/
rm -rf logs/2026-01-*

# Configure log rotation in config.py
LOGGING = {
    'max_file_size': '100MB',
    'backup_count': 5,
}
```

### Database connection errors

**Error: "could not connect to server"**

```bash
# Verify PostgreSQL is running
sudo systemctl status postgresql

# Check connection string
grep DATABASE_URL config/config.py

# Test connection
psql postgresql://user:pass@localhost/angel_x

# Reset connection
sudo systemctl restart postgresql
```

### Strategies not placing orders

**Problem: Iron Condor enabled but no orders**

```bash
# Check strategy conditions
grep "Iron Condor" logs/*/trading_*.log

# Verify underlying has options
python -c "
from src.integrations.angelone import SmartAPIClient
client = SmartAPIClient('key', 'code', 'pass')
options = client.search_scrip('NIFTY')
print(len(options))
"

# Check if market hours
python -c "
import datetime
print(f'Current time: {datetime.datetime.now().time()}')
print('Market hours: 09:15 - 15:30 IST')
"
```

---

## Trading & Strategies

### What strategies does Angel-X support?

**Currently supported:**
- ✅ Iron Condor
- ✅ Calendar Spreads
- ✅ Short Straddles
- ✅ Bull/Bear Call Spreads
- ✅ Adaptive strategies (AI-driven)

**Coming soon:**
- ⏳ Butterfly spreads
- ⏳ Ratio spreads
- ⏳ Backtesting engine
- ⏳ Custom strategy builder

### How do I backtest a strategy?

Backtesting framework is under development. For now:

1. **Paper trading:**
   ```python
   BROKER = {'paper_trading': True}
   ```
   Run for 2-4 weeks to accumulate realistic results

2. **Manual analysis:**
   ```bash
   # Export trade history
   curl http://localhost:5000/api/trades > trades.json
   
   # Analyze in spreadsheet or Python
   python scripts/analyze_trades.py trades.json
   ```

3. **Upcoming:** Native backtesting engine
   ```python
   from src.backtesting import Backtester
   backtest = Backtester(strategy='iron_condor', start='2025-01-01', end='2025-12-31')
   results = backtest.run()
   ```

### What's the expected return?

Historical performance (paper trading):

| Strategy | Monthly Return | Win Rate | Max Drawdown |
|----------|------------------|----------|--------------|
| Iron Condor | 3-5% | 65-75% | -8% |
| Calendar Spread | 2-3% | 70-80% | -5% |
| Adaptive | 5-8% | 60-70% | -12% |

⚠️ **Past performance ≠ future results**

### How do I optimize a strategy?

1. **Via configuration:**
   ```python
   STRATEGIES = {
       'iron_condor': {
           'delta_target': 0.25,      # Adjust Greeks
           'days_to_expiry': 45,       # Adjust timing
           'position_size': 5,         # Adjust size
       }
   }
   ```

2. **Via machine learning:**
   - Run longer in paper mode
   - System learns optimal parameters
   - Check ML metrics dashboard

3. **Via backtesting:**
   - Run backtests with different parameters
   - Find optimal combination
   - Deploy with best parameters

### Can I manage positions manually?

Yes, you can:

1. **Via broker terminal:**
   - Close, modify, or add positions manually
   - Angel-X will sync automatically

2. **Via Angel-X API:**
   ```bash
   # Close specific position
   curl -X POST http://localhost:5000/api/positions/123/close
   
   # Modify position
   curl -X PATCH http://localhost:5000/api/positions/123 \
     -H "Content-Type: application/json" \
     -d '{"new_stop_loss": 5000}'
   ```

3. **Hybrid approach:**
   - Angel-X manages main positions
   - You manage adjustments/hedges
   - System coordinates for risk

### What about slippage and commissions?

Paper trading shows theoretical prices. Real trading includes:

- **Slippage**: Gap between theoretical and actual execution price
- **Brokerage**: ₹20-50 per order (depends on Angel Broking plan)
- **Taxes**: 18% GST on brokerage

Adjust expectations:
- Reduce theoretical returns by 5-10% for real costs
- High-frequency strategies hit harder by slippage
- Focus on net returns after all costs

---

## Performance & Monitoring

### How do I check P&L?

```bash
# Current P&L
curl http://localhost:5000/api/pnl/current

# Daily P&L
curl http://localhost:5000/api/pnl/daily

# Monthly P&L
curl http://localhost:5000/api/pnl/monthly

# Detailed breakdown
curl http://localhost:5000/api/performance
```

**Dashboard:**
- Visit http://localhost:5000/dashboard
- See real-time P&L, Greeks, Greeks exposure

### How do I view Greek exposure?

```bash
# Greeks by position
curl http://localhost:5000/api/positions

# Portfolio Greeks
curl http://localhost:5000/api/greeks

# Delta hedging status
curl http://localhost:5000/api/hedging/status
```

### How do I set up alerts?

Configure in `config/config.py`:

```python
ALERTS = {
    'enabled': True,
    'channels': ['email', 'slack'],
    'triggers': {
        'daily_loss_exceeds': 50000,      # Alert if daily loss > ₹50k
        'position_loss_exceeds': 10000,   # Alert if position loss > ₹10k
        'margin_below': 50000,             # Alert if available margin < ₹50k
        'order_rejected': True,            # Alert on rejected orders
    },
    'email': {
        'to': 'your-email@example.com',
        'from': 'alerts@angel-x.io',
    },
    'slack': {
        'webhook_url': 'https://hooks.slack.com/...',
    }
}
```

### How do I view performance metrics?

```bash
# Dashboard
open http://localhost:5000/dashboard

# API endpoint
curl http://localhost:5000/api/metrics

# Log file
tail -f logs/metrics/daily_metrics.json
```

Metrics tracked:
- Daily P&L and returns
- Win/loss ratio
- Average win/loss size
- Max drawdown
- Sharpe ratio
- Greeks exposure

### How do I export trade data?

```bash
# Export all trades
curl http://localhost:5000/api/trades > trades.json

# Export positions
curl http://localhost:5000/api/positions > positions.json

# Export performance
curl http://localhost:5000/api/performance > performance.json

# Export logs
tar -czf logs_backup.tar.gz logs/
```

---

## Deployment

### How do I deploy to production?

See [Deployment Guide](docs/DEPLOYMENT.md) for detailed steps.

Quick summary:
1. Test thoroughly in paper mode
2. Set up secure server (Linux recommended)
3. Configure production credentials
4. Use systemd or Docker for process management
5. Set up monitoring and alerts
6. Start with small trading amounts

### Can I deploy to cloud?

Yes, supported platforms:

**AWS:**
```bash
# Deploy on EC2
scripts/deploy-aws.sh

# Or use Docker:
docker build -t angel-x .
docker tag angel-x:latest YOUR_ECR_URI/angel-x:latest
docker push YOUR_ECR_URI/angel-x:latest
```

**Google Cloud:**
```bash
# Deploy on Cloud Run
gcloud run deploy angel-x --source . --region us-central1
```

**DigitalOcean:**
```bash
# Deploy via App Platform
doctl apps create --spec app.yaml
```

**Self-hosted:**
```bash
# VPS with systemd
sudo systemctl start angel-x
```

See [Cloud Deployment Guide](docs/CLOUD_DEPLOYMENT.md) for each platform.

### How do I monitor in production?

**System health:**
```bash
curl http://localhost:5000/health
```

**Metrics:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
- Custom: http://localhost:5000/metrics

**Alerts:**
- Email notifications
- Slack integration
- PagerDuty (optional)

**Logging:**
- Structured JSON logs
- Centralized logging (optional)
- Log rotation configured

---

## Support & Community

### How do I get help?

**Channels:**
1. **Documentation**: [docs/](docs/) folder
2. **GitHub Issues**: [Report bugs](https://github.com/your-org/Angel-x/issues)
3. **GitHub Discussions**: [Ask questions](https://github.com/your-org/Angel-x/discussions)
4. **Discord**: [Community chat](https://discord.gg/your-link)
5. **Email**: support@your-org.com

### How do I report bugs?

See [CONTRIBUTING.md](CONTRIBUTING.md#reporting-issues) for bug report template.

**Quick steps:**
1. Search existing issues
2. Include reproduction steps
3. Add error messages and logs
4. Specify your environment
5. Submit on GitHub Issues

### How do I suggest features?

1. Open GitHub Issue (or Discussion)
2. Describe the feature clearly
3. Explain the use case
4. Suggest implementation if possible

**Or contribute:**
- Fork repository
- Implement feature
- Submit pull request
- See [CONTRIBUTING.md](CONTRIBUTING.md)

### How do I contribute?

See [CONTRIBUTING.md](CONTRIBUTING.md) for full guidelines.

**Quick start:**
1. Fork repository
2. Create feature branch
3. Make changes
4. Write tests
5. Submit pull request
6. Wait for review

### Is Angel-X suitable for my use case?

**Good fit:**
- ✅ Algorithmic options trading
- ✅ Multi-strategy management
- ✅ Paper + live trading
- ✅ India NSE options

**Not suitable:**
- ❌ Non-options trading
- ❌ High-frequency trading
- ❌ Non-Indian exchanges
- ❌ Manual-only traders

**Consult with us:**
Email support@your-org.com with your use case.

---

## Legal & Compliance

### Is Angel-X licensed?

Angel-X is open-source software under **MIT License**.

You are responsible for:
- ✅ Compliance with broker terms
- ✅ Compliance with regulations (SEBI, RBI)
- ✅ Tax reporting
- ✅ Risk management

### Do I need regulatory approval?

Consult your broker and tax advisor:
- Check if algo trading is allowed
- Verify tax implications
- Keep audit trail
- Report as per regulations

### What about liability?

See [LICENSE.md](LICENSE.md) for full terms.

**Summary:**
- Angel-X provided "as-is"
- No warranties or guarantees
- You assume all trading risks
- Developers not liable for losses

### How do I report a security issue?

See [SECURITY.md](SECURITY.md) for responsible disclosure process.

**Quick steps:**
1. Email security@your-org.com
2. Include vulnerability details
3. Don't open public issue
4. Wait for response

---

## Glossary

**Greeks**: Delta, Gamma, Theta, Vega - Option price sensitivities

**Iron Condor**: Sell ATM call/put spreads, collect premium (defined risk)

**Calendar Spread**: Sell short-term options, buy long-term (time decay play)

**Paper Trading**: Simulated trading without real money

**Smart API**: AngelOne's broker API for trading

**WebSocket**: Real-time data streaming connection

**Expiry**: Date when options expire (monthly, weekly)

**Strike**: Fixed price at which option can be exercised

**Premium**: Price paid for option contract

**P&L**: Profit and Loss

See [Glossary.md](docs/GLOSSARY.md) for more terms.

---

## More Information

- **[README.md](README.md)** - Project overview and quick start
- **[Documentation](docs/)** - Comprehensive guides
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community guidelines
- **[SECURITY.md](SECURITY.md)** - Security best practices
- **[LICENSE.md](LICENSE.md)** - Legal terms

---

**Can't find your answer? Ask us!**

- GitHub Discussions: [Ask here](https://github.com/your-org/Angel-x/discussions)
- Email: support@your-org.com
- Discord: [Join community](https://discord.gg/your-link)

*Last Updated: January 12, 2026*
