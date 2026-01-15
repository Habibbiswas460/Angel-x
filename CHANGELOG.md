# Changelog

All notable changes to Angel-X are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-12

### ✨ Added
- **Real Order Placement**: Direct SmartAPI integration for order placement (not placeholder)
- **Order Cancellation**: Cancel open orders via broker API
- **Order Modification**: Modify stop-loss prices dynamically
- **Order Status Tracking**: Query order fill status from broker orderbook
- **Option Chain Fetching**: Real broker API calls to fetch option strikes
- **WebSocket Binary Parsing**: Proper struct-based parsing of SmartAPI tick data
- **Instrument Master Loading**: Download and cache instrument master file
- **Symbol to Token Lookup**: Automatic symbol → exchange token conversion
- **Comprehensive README**: 570+ lines with enterprise documentation
- **MIT License**: Full legal documentation and compliance

### 🔧 Changed
- **Broker Integration**: Now uses real SmartAPI calls instead of placeholders
- **Token Lookup**: Improved from hardcoded to instrument master lookup
- **README Structure**: Reorganized for better navigation and clarity
- **Documentation**: Added deployment, operations, and integration guides

### 🐛 Fixed
- WebSocket binary parsing implementation (was TODO)
- Option chain data fetching (was returning dummy data)
- Token lookup for option subscriptions (was placeholder)
- Order status retrieval (was not implemented)

### 📦 Dependencies
- smartapi-python >= 1.3.0
- flask >= 2.3.0
- pandas >= 2.2.0
- scikit-learn >= 1.3.0
- websocket-client >= 1.6.0
- psycopg2-binary >= 2.9.9

### ⚠️ Breaking Changes
- Removed deprecated placeholder order placement methods
- Modified stream_manager constructor to accept instrument dict
- Changed option_chain_engine to require broker connection for real data

### 📖 Documentation
- Complete API reference documentation
- Deployment guides for Docker, Kubernetes, AWS, GCP, Azure
- Operations manual for daily trading
- Integration guide with 6 working examples
- Instrument master usage examples

### 🔒 Security
- Fixed potential credential exposure in logs
- Improved error handling for failed authentications
- Added security best practices section to README

---

## [1.5.0] - 2025-09-15

### ✨ Added
- ML signals integration with LSTM and RandomForest
- Dashboard UI for real-time monitoring
- Prometheus metrics export
- Telegram alert integration

### 🔧 Changed
- Improved Greeks calculation accuracy
- Enhanced risk management logic
- Optimized backtesting engine

### 🐛 Fixed
- Fixed WebSocket reconnection issues
- Resolved database connection pooling problems

---

## [1.0.0] - 2025-06-30

### ✨ Added
- Multi-leg strategy framework (Iron Condor, Straddle, Spreads)
- Real-time trade execution system
- Risk management engine
- Basic health monitoring

### 📦 Initial Release
- Core trading engine
- Broker integration framework
- Database persistence
- Basic API endpoints

---

## Legend

- **Added** - New features
- **Changed** - Changes in existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Now removed features
- **Fixed** - Bug fixes
- **Security** - Security fixes/improvements

---

## Version History

| Version | Date | Status | Notes |
|---------|------|--------|-------|
| 2.0.0 | 2026-01-12 | Current | Production ready with full API implementation |
| 1.5.0 | 2025-09-15 | Stable | ML signals and monitoring |
| 1.0.0 | 2025-06-30 | Legacy | Initial release |

---

## Upgrade Guide

### From 1.5.0 to 2.0.0

1. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   ```

2. **Database Migration** (if needed):
   ```bash
   # Backup existing database
   pg_dump angel_x_db > backup_$(date +%s).sql
   
   # Apply new schema
   psql angel_x_db < migrations/v2_0_0.sql
   ```

3. **Configuration Update**:
   - Update `config/config.py` with new options
   - Test in paper trading mode first

4. **Test**:
   ```bash
   pytest tests/ -v --cov=src
   ```

5. **Deploy**:
   ```bash
   docker-compose up -d --build
   ```

---

## Future Plans

### Q1 2026
- [ ] Kubernetes operator deployment
- [ ] Advanced backtesting engine v2
- [ ] Multi-broker support (NSE, NFO, BSE)

### Q2 2026
- [ ] Mobile monitoring app
- [ ] REST API v2 with OAuth2
- [ ] Advanced portfolio analytics

### Q3 2026
- [ ] Volatility surface modeling
- [ ] Portfolio optimization
- [ ] Advanced ML models (transformers, GANs)

### Q4 2026
- [ ] Distributed trading network
- [ ] Blockchain audit trail
- [ ] Regulatory reporting automation

---

For detailed information about each release, see the [GitHub Releases](https://github.com/your-org/Angel-x/releases) page.
