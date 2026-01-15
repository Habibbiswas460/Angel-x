# Installation Guide

Complete step-by-step installation instructions for Angel-X.

## Prerequisites

### System Requirements

**Minimum:**
- OS: Linux (Ubuntu 20.04+), macOS, or Windows with WSL2
- Python: 3.8+
- RAM: 2 GB
- Disk: 5 GB free space
- Internet: Broadband (minimum 1 Mbps)

**Recommended:**
- OS: Ubuntu 22.04 LTS or macOS Ventura
- Python: 3.11+
- RAM: 4+ GB
- Disk: 20+ GB SSD
- Internet: Dedicated connection for reliable trading
- Server: Always-on Linux/Mac server (VPS recommended)

### Required Accounts

1. **AngelOne Broker Account**
   - Free account at https://www.angelbroking.com/
   - Complete KYC process
   - Enable API access
   - Get API credentials

2. **NSE Data Subscription**
   - Usually bundled with AngelOne account
   - Verify it's active in your account

---

## Step-by-Step Installation

### 1. Install Python

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3.11-dev git curl
python3.11 --version
```

#### macOS
```bash
# Using Homebrew
brew install python3@3.11 git curl

# Or download from python.org
https://www.python.org/downloads/

python3 --version
```

#### Windows (using WSL2)
```bash
# Install WSL2 first
# Then run Linux commands above
```

### 2. Clone Repository

```bash
# Choose a directory
mkdir ~/projects
cd ~/projects

# Clone repository
git clone https://github.com/your-org/Angel-x.git
cd Angel-x

# Verify
ls -la
```

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3.11 -m venv venv

# Activate it
source venv/bin/activate
# On Windows: venv\Scripts\activate

# Verify
which python  # Should show path in venv/
python --version
```

### 4. Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip setuptools wheel

# Install requirements
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-test.txt

# Verify
pip list
```

### 5. Configure Application

```bash
# Copy example config
cp config/config.example.py config/config.py

# Edit with your credentials
nano config/config.py  # or use your editor
```

Edit these values in `config/config.py`:

```python
# Broker Configuration
BROKER = {
    'name': 'angelone',
    'api_key': 'YOUR_API_KEY_HERE',           # From Angel Broking dashboard
    'client_code': 'YOUR_CLIENT_CODE_HERE',   # Your account code
    'password': 'YOUR_PASSWORD_HERE',         # API password
    'paper_trading': True,                    # Start with paper trading
}

# Database Configuration
DATABASE = {
    'url': 'postgresql://user:password@localhost:5432/angel_x',
    'echo': False,
}
```

### 6. Set Up Database (Optional but Recommended)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib  # Linux
# macOS: brew install postgresql

# Create database
sudo -u postgres createdb angel_x
sudo -u postgres createuser angel_user
sudo -u postgres psql -c "ALTER USER angel_user WITH PASSWORD 'secure_password';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE angel_x TO angel_user;"

# Or use SQLite (simpler, no setup needed)
# Modify config.py:
DATABASE = {
    'url': 'sqlite:///angel_x.db',
}
```

### 7. Verify Installation

```bash
# Test imports
python -c "from src.integrations.angelone import SmartAPIClient; print('✓ Broker integration imported')"
python -c "from src.strategies import IronCondor; print('✓ Strategies imported')"
python -c "from src.monitoring import HealthMonitor; print('✓ Monitoring imported')"

# Run health check
python main.py --health

# Expected output:
# ✓ Broker connection: OK
# ✓ Database: OK  
# ✓ WebSocket: Ready
# ✓ Strategies: 3 loaded
```

### 8. Test Broker Connection

```bash
# Create test script
cat > test_broker_connection.py << 'EOF'
from src.integrations.angelone import SmartAPIClient
from config import BROKER

try:
    client = SmartAPIClient(
        api_key=BROKER['api_key'],
        client_code=BROKER['client_code'],
        password=BROKER['password']
    )
    
    result = client.connect()
    if result:
        print("✓ Broker connection successful!")
        print(f"Account: {client.client_code}")
        profile = client.get_profile()
        print(f"Profile: {profile}")
    else:
        print("✗ Broker connection failed!")
        
except Exception as e:
    print(f"✗ Error: {e}")
EOF

# Run it
python test_broker_connection.py
```

---

## Alternative Installation Methods

### Using Docker (Recommended for Production)

```bash
# Clone repository
git clone https://github.com/your-org/Angel-x.git
cd Angel-x

# Create .env file with credentials
cat > .env << 'EOF'
ANGELONE_API_KEY=your-key
ANGELONE_CLIENT_CODE=your-code
ANGELONE_PASSWORD=your-password
DATABASE_URL=postgresql://user:pass@postgres:5432/angel_x
EOF

# Build image
docker build -t angel-x:latest .

# Run container
docker run -it \
  --env-file .env \
  -p 5000:5000 \
  -p 3000:3000 \
  -v $(pwd)/logs:/app/logs \
  angel-x:latest

# Or use Docker Compose (recommended)
docker-compose up -d
```

**docker-compose.yml** (if not present):
```yaml
version: '3.8'

services:
  angel-x:
    build: .
    ports:
      - "5000:5000"
      - "3000:3000"
    environment:
      - ANGELONE_API_KEY=${ANGELONE_API_KEY}
      - ANGELONE_CLIENT_CODE=${ANGELONE_CLIENT_CODE}
      - ANGELONE_PASSWORD=${ANGELONE_PASSWORD}
      - DATABASE_URL=postgresql://angel_user:password@postgres:5432/angel_x
    volumes:
      - ./logs:/app/logs
      - ./config:/app/config
    depends_on:
      - postgres
    networks:
      - angel-network

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=angel_user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=angel_x
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - angel-network

volumes:
  postgres_data:

networks:
  angel-network:
```

### Using Conda

```bash
# Create conda environment
conda create -n angel-x python=3.11

# Activate
conda activate angel-x

# Install dependencies
pip install -r requirements.txt

# Continue with steps 5-8 above
```

---

## Getting AngelOne Credentials

### Step-by-Step Guide

1. **Open AngelOne Account**
   - Visit https://www.angelbroking.com/
   - Click "Open Account"
   - Complete registration and KYC

2. **Login to Dashboard**
   - Go to https://web.angelbroking.com/
   - Login with credentials

3. **Get API Credentials**
   - Navigate to **Settings** → **Developer Console** (or **API**)
   - Click "Generate API Key"
   - You'll see:
     ```
     API Key: abc123def456...
     Client Code: ABC123
     ```

4. **Get API Password**
   - This is usually your trading password
   - If you don't know it, reset via dashboard

5. **Add to Angel-X**
   ```python
   # config/config.py
   BROKER = {
       'api_key': 'abc123def456...',
       'client_code': 'ABC123',
       'password': 'your_trading_password',
   }
   ```

### Verify Credentials Work

```bash
python test_broker_connection.py
```

---

## Environment Variables (Production Setup)

For security, use environment variables instead of hardcoding:

```bash
# Create .env file (never commit this!)
cat > .env << 'EOF'
ANGELONE_API_KEY=your-key
ANGELONE_CLIENT_CODE=your-code
ANGELONE_PASSWORD=your-password
DATABASE_URL=postgresql://user:pass@localhost:5432/angel_x
FLASK_ENV=production
LOG_LEVEL=INFO
EOF

# Add to .gitignore (if not already)
echo ".env" >> .gitignore

# Load in application
from dotenv import load_dotenv
import os
load_dotenv()

api_key = os.getenv('ANGELONE_API_KEY')
client_code = os.getenv('ANGELONE_CLIENT_CODE')
password = os.getenv('ANGELONE_PASSWORD')
```

---

## Troubleshooting Installation

### Python not found

```bash
# Check Python version
python3 --version

# Create alias if needed
alias python=python3

# Or add to ~/.bashrc
echo "alias python=python3" >> ~/.bashrc
source ~/.bashrc
```

### Module import errors

```bash
# Verify virtual environment is activated
which python  # Should show path in venv/

# Reinstall dependencies
pip install --force-reinstall -r requirements.txt

# Check for conflicts
pip check
```

### Broker connection fails

```bash
# Verify credentials
grep -A 3 "BROKER = {" config/config.py

# Check internet connection
ping api.angel.broking.com

# Check firewall
netstat -an | grep 443
```

### PostgreSQL connection error

```bash
# Check PostgreSQL is running
sudo systemctl status postgresql  # Linux
brew services list | grep postgres  # macOS

# Verify connection string
grep DATABASE_URL .env

# Test connection
psql postgresql://user:password@localhost:5432/angel_x
```

### Permission denied errors

```bash
# Fix file permissions
chmod 755 venv/bin/activate
chmod 600 config/config.py
chmod 600 .env

# Or on entire directory
chmod -R 755 Angel-x/
```

---

## Post-Installation Setup

### 1. Start Paper Trading

```bash
# Ensure paper trading is enabled
grep "paper_trading" config/config.py
# Should show: 'paper_trading': True

# Start application
python main.py

# Visit dashboard
open http://localhost:5000/dashboard
```

### 2. Run First Test

```bash
# Run quick test
python quick_test.py

# Should output:
# ✓ Broker connection OK
# ✓ Paper trading active
# ✓ All strategies loaded
# Ready to trade!
```

### 3. Configure Risk Settings

Edit `config/config.py`:

```python
RISK = {
    'max_daily_loss': 50000,      # Stop if lose ₹50k/day
    'max_position_loss': 10000,   # Close if position loses ₹10k
    'max_positions': 10,           # Max 10 open positions
    'max_leverage': 2.0,           # Use max 2x leverage
    'max_per_expiry': 5,           # Max 5 per expiry date
}
```

### 4. Test With Paper Trading

```bash
# Paper trading mode (enabled by default)
# Run for at least 1-2 weeks before real trading
# Monitor logs and dashboard daily

tail -f logs/$(date +%Y-%m-%d)/trading_*.log
```

### 5. Enable Real Trading (When Ready)

```python
# ONLY after successful paper trading testing!
BROKER = {
    'paper_trading': False,  # Enable real trading
}
```

---

## Advanced Setup

### Running as Service (Linux)

Create systemd service file:

```bash
sudo nano /etc/systemd/system/angel-x.service
```

Content:
```ini
[Unit]
Description=Angel-X Trading Platform
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=trader
WorkingDirectory=/home/trader/Angel-x
Environment="PATH=/home/trader/Angel-x/venv/bin"
ExecStart=/home/trader/Angel-x/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable angel-x
sudo systemctl start angel-x
sudo systemctl status angel-x
```

### Running on VPS

```bash
# SSH into server
ssh user@your-vps.com

# Follow installation steps 1-8

# Use Docker Compose (recommended)
docker-compose up -d

# Or use systemd service
sudo systemctl start angel-x

# Verify
curl http://localhost:5000/health
```

### Monitoring & Logging

```bash
# View logs
tail -f logs/$(date +%Y-%m-%d)/trading_*.log

# Set up log rotation
cat > /etc/logrotate.d/angel-x << 'EOF'
/home/trader/Angel-x/logs/*.log {
    daily
    rotate 30
    compress
    missingok
    notifempty
}
EOF

# Set up monitoring
# Use Prometheus, Grafana, or other tools
# Endpoints:
# - http://localhost:5000/health
# - http://localhost:5000/metrics
```

---

## Next Steps

1. ✅ Installation complete!
2. 📖 Read [README.md](README.md) for overview
3. ⚙️ Review [config/config.example.py](config/config.example.py) for all options
4. 📊 Start paper trading
5. 📚 Read [docs/STRATEGIES.md](docs/STRATEGIES.md) to understand strategies
6. 🚀 When ready, enable real trading

---

## Getting Help

- **FAQ**: [FAQ](docs/FAQ.md)
- **Documentation**: [docs/](docs/)
- **GitHub Issues**: [Report problems](https://github.com/your-org/Angel-x/issues)
- **Email**: support@your-org.com
- **Discord**: [Join community](https://discord.gg/your-link)

---

## Verification Checklist

After installation, verify:

- [ ] Python 3.8+ installed
- [ ] Virtual environment activated
- [ ] All dependencies installed (`pip list`)
- [ ] AngelOne credentials configured
- [ ] Broker connection test passed
- [ ] Database connection working (if using PostgreSQL)
- [ ] Paper trading enabled by default
- [ ] Application starts without errors
- [ ] Dashboard accessible at http://localhost:5000/dashboard
- [ ] First test trade executed in paper mode

---

*Last Updated: January 12, 2026*
