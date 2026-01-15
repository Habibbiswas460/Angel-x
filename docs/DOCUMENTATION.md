# Documentation Index

Complete guide to all Angel-X documentation and resources.

## 📚 Core Documentation

### Getting Started
- **[README.md](README.md)** - Project overview, features, quick start, and architecture
- **[INSTALLATION.md](INSTALLATION.md)** - Step-by-step installation guide for all platforms
- **[FAQ](FAQ.md)** - Frequently asked questions and troubleshooting
- **[QUICKSTART.md](QUICKSTART.md)** *(coming soon)* - 10-minute setup guide

### Community & Contributing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute code, tests, and documentation
- **[CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)** - Community guidelines and enforcement
- **[CONTRIBUTORS](CONTRIBUTORS.md)** - Team members and contributors
- **[LICENSE](LICENSE)** - MIT License terms

### Security & Operations
- **[SECURITY.md](SECURITY.md)** - Security policy, best practices, and vulnerability reporting
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and release notes

---

## 📖 User Guides

### Configuration
- **[docs/CONFIGURATION.md](docs/CONFIGURATION.md)** - All configuration options explained
- **[config/config.example.py](config/config.example.py)** - Example configuration

### Trading
- **[docs/STRATEGIES.md](docs/STRATEGIES.md)** - Trading strategy guide
  - Iron Condor
  - Calendar Spreads
  - Short Straddles
  - Adaptive Strategies
- **[docs/RISK_MANAGEMENT.md](docs/RISK_MANAGEMENT.md)** - Risk controls and position limits
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - REST API endpoints

### Operations
- **[docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)** - Production deployment guide
  - Docker setup
  - Systemd service
  - Monitoring and alerts
- **[docs/OPERATIONS.md](docs/OPERATIONS.md)** - Daily operations and monitoring
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions

### Development
- **[docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)** - Developer guide
  - Architecture overview
  - Code style guide
  - Testing strategy
- **[docs/API_DEVELOPMENT.md](docs/API_DEVELOPMENT.md)** - Building custom integrations

---

## 🏗️ Architecture Documentation

### System Design
- **[docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md)** - System architecture
- **[docs/architecture/COMPONENTS.md](docs/architecture/COMPONENTS.md)** - Component breakdown
- **[docs/architecture/DATA_FLOW.md](docs/architecture/DATA_FLOW.md)** - Data flow diagrams
- **[docs/architecture/TRADING_ENGINE.md](docs/architecture/TRADING_ENGINE.md)** - Trading engine details

### Integration
- **[docs/BROKER_INTEGRATION.md](docs/BROKER_INTEGRATION.md)** - AngelOne broker integration
- **[docs/WEBSOCKET_INTEGRATION.md](docs/WEBSOCKET_INTEGRATION.md)** - Real-time data streaming
- **[docs/DATABASE.md](docs/DATABASE.md)** - Database schema and queries

---

## 🧠 Machine Learning

- **[docs/ml/OVERVIEW.md](docs/ml/OVERVIEW.md)** - ML system overview
- **[docs/ml/MODELS.md](docs/ml/MODELS.md)** - Supported ML models
- **[docs/ml/TRAINING.md](docs/ml/TRAINING.md)** - Model training process
- **[docs/ml/DEPLOYMENT.md](docs/ml/DEPLOYMENT.md)** - ML model deployment

---

## 🔧 Command Reference

### Running Angel-X

```bash
# Start application
python main.py

# Run tests
pytest tests/ -v

# Check health
curl http://localhost:5000/health

# View dashboard
open http://localhost:5000/dashboard

# Export metrics
curl http://localhost:5000/api/metrics > metrics.json
```

### Docker Commands

```bash
# Build image
docker build -t angel-x:latest .

# Run container
docker run -it angel-x:latest

# Using Docker Compose
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Development Commands

```bash
# Format code
black src/ tests/

# Check style
pylint src/
flake8 src/

# Type checking
mypy src/

# Run tests
pytest tests/ -v --cov=src

# Create new virtual environment
python3 -m venv venv
```

---

## 📁 Directory Structure

```
Angel-x/
├── README.md                          # Project overview
├── INSTALLATION.md                    # Installation guide
├── CONTRIBUTING.md                    # Contributor guide
├── CODE_OF_CONDUCT.md                # Community guidelines
├── SECURITY.md                        # Security policy
├── FAQ.md                             # Frequently asked questions
├── CHANGELOG.md                       # Version history
├── LICENSE                            # MIT License
│
├── config/                            # Configuration
│   ├── config.example.py              # Example config
│   ├── config.py                      # Local config (gitignored)
│   ├── development.py                 # Dev settings
│   ├── production.py                  # Prod settings
│   └── test_config.py                 # Test settings
│
├── src/                               # Source code
│   ├── integrations/                  # Broker/data integrations
│   │   ├── angelone/                  # AngelOne broker
│   │   ├── websocket/                 # Real-time data
│   │   └── ...
│   ├── strategies/                    # Trading strategies
│   │   ├── iron_condor.py
│   │   ├── calendar_spread.py
│   │   └── ...
│   ├── ml/                            # Machine learning
│   ├── monitoring/                    # Health & monitoring
│   ├── database/                      # Database layer
│   ├── utils/                         # Utilities
│   └── ...
│
├── tests/                             # Tests
│   ├── unit/                          # Unit tests
│   ├── integration/                   # Integration tests
│   ├── e2e/                           # End-to-end tests
│   └── ...
│
├── docs/                              # Documentation
│   ├── CONFIGURATION.md               # Config guide
│   ├── STRATEGIES.md                  # Strategy guide
│   ├── DEPLOYMENT.md                  # Deployment guide
│   ├── API_REFERENCE.md               # API docs
│   ├── architecture/                  # Architecture docs
│   └── ml/                            # ML docs
│
├── logs/                              # Application logs
│   ├── 2026-01-10/                    # Daily logs
│   ├── metrics/                       # Metrics
│   ├── trades/                        # Trade execution logs
│   └── reports/                       # Daily reports
│
├── data/                              # Data files
│   ├── option_chain_*.csv             # Option chain data
│   └── instruments.csv                # Instrument master
│
├── app/                               # Flask API application
│   ├── api/                           # API routes
│   ├── web/                           # Web interface
│   ├── domains/                       # Domain models
│   └── ...
│
├── infra/                             # Infrastructure
│   ├── docker/                        # Docker config
│   ├── kubernetes/                    # K8s config
│   ├── database/                      # DB migrations
│   └── ...
│
├── scripts/                           # Utility scripts
│   ├── deploy.sh                      # Deployment
│   ├── validate.py                    # Validation
│   └── ...
│
├── docker-compose.yml                 # Docker Compose config
├── Dockerfile                         # Container image
├── pytest.ini                         # Test config
├── requirements.txt                   # Dependencies
└── .gitignore                         # Git ignore rules
```

---

## 🚀 Quick Navigation

### I want to...

#### Get Started
1. Read [README.md](README.md) - 5 minutes
2. Follow [INSTALLATION.md](INSTALLATION.md) - 15 minutes
3. Start [QUICKSTART.md](QUICKSTART.md) - 10 minutes

#### Understand Architecture
1. Read [docs/architecture/OVERVIEW.md](docs/architecture/OVERVIEW.md)
2. Review [docs/architecture/COMPONENTS.md](docs/architecture/COMPONENTS.md)
3. Study [docs/architecture/DATA_FLOW.md](docs/architecture/DATA_FLOW.md)

#### Set Up Trading
1. Review [docs/STRATEGIES.md](docs/STRATEGIES.md)
2. Configure [config/config.example.py](config/config.example.py)
3. Read [docs/RISK_MANAGEMENT.md](docs/RISK_MANAGEMENT.md)

#### Deploy to Production
1. Read [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
2. Follow [docs/OPERATIONS.md](docs/OPERATIONS.md)
3. Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)

#### Build Custom Strategy
1. Read [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)
2. Review [docs/API_DEVELOPMENT.md](docs/API_DEVELOPMENT.md)
3. Check [docs/architecture/TRADING_ENGINE.md](docs/architecture/TRADING_ENGINE.md)

#### Work With ML Models
1. Read [docs/ml/OVERVIEW.md](docs/ml/OVERVIEW.md)
2. Study [docs/ml/MODELS.md](docs/ml/MODELS.md)
3. Follow [docs/ml/TRAINING.md](docs/ml/TRAINING.md)

#### Contribute Code
1. Read [CONTRIBUTING.md](CONTRIBUTING.md)
2. Review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
3. Check [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

#### Report Issues
1. Review [SECURITY.md](SECURITY.md) (if security-related)
2. Check [FAQ](FAQ.md) and [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
3. Open [GitHub Issue](https://github.com/your-org/Angel-x/issues)

---

## 📊 Documentation Statistics

| Category | Documents | Pages (approx) | Time to Read |
|----------|-----------|-----------------|---|
| Getting Started | 4 | 50 | 30 min |
| User Guides | 6 | 100 | 2-3 hours |
| Architecture | 4 | 80 | 2 hours |
| ML | 4 | 50 | 1-2 hours |
| Community | 3 | 40 | 30 min |
| **Total** | **21** | **~310** | **~8 hours** |

---

## 🔍 Document Relationships

```
README.md (START HERE)
├── INSTALLATION.md
│   ├── QUICKSTART.md
│   └── FAQ.md
├── docs/CONFIGURATION.md
│   └── config/config.example.py
├── docs/STRATEGIES.md
│   └── docs/RISK_MANAGEMENT.md
├── docs/DEPLOYMENT.md
│   ├── docs/OPERATIONS.md
│   └── docs/TROUBLESHOOTING.md
├── CONTRIBUTING.md
│   ├── CODE_OF_CONDUCT.md
│   └── docs/DEVELOPMENT.md
└── SECURITY.md
```

---

## 📞 Getting Help

### Documentation Issues
- **Typos/clarity**: [Create GitHub issue](https://github.com/your-org/Angel-x/issues)
- **Missing sections**: [GitHub discussion](https://github.com/your-org/Angel-x/discussions)

### Usage Questions
- **FAQ**: Start with [FAQ](FAQ.md)
- **Troubleshooting**: Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- **Ask community**: [GitHub discussions](https://github.com/your-org/Angel-x/discussions)
- **Email**: support@your-org.com

### Security Issues
- **Vulnerabilities**: Follow [SECURITY.md](SECURITY.md)
- **Email**: security@your-org.com

### Contributing Questions
- **Process**: Read [CONTRIBUTING.md](CONTRIBUTING.md)
- **Standards**: Review [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)

---

## 📝 Documentation Maintenance

### Last Updated
- **This index**: January 12, 2026
- **README.md**: January 12, 2026
- **CHANGELOG.md**: January 12, 2026
- **Security.md**: January 12, 2026
- **Installation.md**: January 12, 2026

### Review Schedule
- ✅ Quarterly (every 3 months)
- ✅ After major releases
- ✅ When new features added
- ✅ When bugs fixed

### Version
- **Angel-X**: 2.0.0
- **Documentation**: v2.0
- **Last Review**: January 12, 2026

---

## 🎯 Common Documentation Paths

### For Developers
```
CONTRIBUTING.md
├── docs/DEVELOPMENT.md
├── docs/architecture/
└── docs/API_DEVELOPMENT.md
```

### For Operators
```
INSTALLATION.md
├── docs/CONFIGURATION.md
├── docs/DEPLOYMENT.md
├── docs/OPERATIONS.md
└── docs/TROUBLESHOOTING.md
```

### For Traders
```
README.md
├── docs/STRATEGIES.md
├── docs/RISK_MANAGEMENT.md
└── FAQ.md
```

### For Contributors
```
CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
└── docs/DEVELOPMENT.md
```

---

## 📚 External Resources

### Trading Knowledge
- [NSE - Options Trading](https://www.nseindia.com/products/content/derivatives/index/opt_index.htm)
- [Black-Scholes Model](https://en.wikipedia.org/wiki/Black%E2%80%93Scholes_model)
- [Options Greeks](https://www.investopedia.com/terms/g/greeks.asp)
- [Iron Condor Strategy](https://www.tastytrade.com/definitions/iron-condor)

### Technical
- [Python Async Programming](https://docs.python.org/3/library/asyncio.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Docker Documentation](https://docs.docker.com/)

### Brokers & APIs
- [AngelOne API Docs](https://www.angelbroking.com/api-docs)
- [NSE Data Standards](https://www.nseindia.com/)

### Community
- [Angel-X GitHub](https://github.com/your-org/Angel-x)
- [Discord Server](https://discord.gg/your-link)
- [Twitter](https://twitter.com/your-handle)

---

## 🏆 Best Practices

### Reading Documentation
1. Start with [README.md](README.md)
2. Follow links based on your needs
3. Search for keywords (Ctrl+F)
4. Check [FAQ](FAQ.md) for common issues
5. Ask in [GitHub discussions](https://github.com/your-org/Angel-x/discussions)

### Using Documentation
- ✅ Keep browser bookmarks to frequently used docs
- ✅ Use Ctrl+F to search within documents
- ✅ Check CHANGELOG for breaking changes
- ✅ Review examples before implementing
- ✅ Follow security guidelines (SECURITY.md)

### Updating Documentation
- ✅ Report issues via GitHub issues
- ✅ Suggest improvements in discussions
- ✅ Submit docs improvements as PRs
- ✅ Keep docs in sync with code
- ✅ Update examples when code changes

---

**Last Updated: January 12, 2026**

**Start here → [README.md](README.md)**
