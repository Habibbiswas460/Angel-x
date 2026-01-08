# Angel-X Ultra-Professional Architecture

## System Overview

Angel-X is a sophisticated, enterprise-grade options trading system featuring:

- **Adaptive Learning**: Self-correcting algorithms that improve over time
- **Market Bias Detection**: Real-time market sentiment analysis
- **Smart Money Tracking**: Institutional activity detection
- **Greeks-Based Analysis**: Comprehensive options analysis using Delta, Gamma, Theta, Vega, IV
- **Intelligent Risk Management**: Dynamic risk controls and position sizing
- **Production-Ready Infrastructure**: Enterprise-grade logging, monitoring, and deployment

## Architecture Layers

### 1. **Domain Layer** (`app/domains/`)

Business logic organized by domain:

#### Market Domain (`market/`)
- **bias_engine.py**: Market state detection (BULLISH/BEARISH/NEUTRAL)
- **smart_money_engine.py**: Institutional activity tracking via OI analysis
- **trap_detector.py**: False breakout detection

#### Options Domain (`options/`)
- **greeks_calculator.py**: Greeks computation (Delta, Gamma, Theta, Vega, IV)
- **greeks_engine.py**: Greeks trend analysis and anomaly detection
- **chain_analyzer.py**: Option chain structure analysis
- **strike_selector.py**: Optimal strike selection

#### Trading Domain (`trading/`)
- **entry_engine.py**: Multi-signal entry confirmation
- **exit_engine.py**: Greeks-based exit triggers
- **risk_manager.py**: Daily limits, Greeks exposure limits
- **sizing_engine.py**: Position sizing using Kelly Criterion
- **order_manager.py**: Order execution and tracking

#### Learning Domain (`learning/`)
- **regime_detector.py**: Market regime classification
- **pattern_learner.py**: Historical pattern analysis
- **weight_optimizer.py**: Rule weight optimization
- **confidence_scorer.py**: Signal quality assessment

### 2. **Services Layer** (`app/services/`)

Cross-cutting concerns and infrastructure:

#### Broker Service (`broker/`)
- AngelOne SmartAPI integration
- Order execution and validation
- Real-time market data fetching

#### Data Service (`data/`)
- Market data management
- Caching strategies
- Data persistence and cleanup

#### Database Service (`database/`)
- PostgreSQL connection pooling
- Schema management
- Data repositories for ML training

#### Monitoring Service (`monitoring/`)
- Metrics collection
- Health checking
- Performance monitoring
- Alert generation

### 3. **API Layer** (`app/api/`)

RESTful API endpoints for external integration:

- `/api/status`: System health and metrics
- `/api/trades`: Active trade information
- `/api/greeks-heatmap`: Greeks visualization data
- `/api/market-bias`: Current market state
- `/api/performance`: P&L and statistics

### 4. **Web UI** (`app/web/`)

Dashboard for real-time monitoring and analysis.

### 5. **Utilities** (`app/utils/`)

Cross-cutting utilities:
- Logging framework
- Decorators for common patterns
- Data validators
- Exception handlers

## Data Flow

```
Market Data (Real-time feeds)
    ↓
[Market Bias Engine]  ← Greeks Analysis
    ↓
[Smart Money Detection]
    ↓
[Trap Detection] ← Option Chain Analysis
    ↓
[Entry Engine]  ← Strike Selection
    ↓
[Position Sizing & Risk Checks]
    ↓
[Order Execution] → [Trade Management]
    ↓
[Greeks Monitoring] → [Exit Triggers]
    ↓
[Adaptive Learning] ← [Historical Analysis]
```

## Domain Separation

Each domain is independently:
- **Testable**: Mocks for dependencies
- **Deployable**: Can be updated without affecting others
- **Scalable**: Can handle increased load
- **Maintainable**: Clear responsibility boundaries

## Configuration Management

Three environments supported:

1. **Development** (`infra/config/development.py`): Debug enabled, paper trading
2. **Testing** (`infra/config/testing.py`): Isolated test database
3. **Production** (`infra/config/production.py`): Live trading enabled

Environment-specific variables:
- Database credentials
- API worker count
- Risk limits
- Logging levels

## Data Persistence

PostgreSQL database with 6 core tables:

1. **market_ticks**: Real-time price and volume data
2. **greeks_snapshots**: Greeks at regular intervals
3. **trades**: Complete trade lifecycle
4. **bias_history**: Market state snapshots
5. **oi_changes**: Smart money OI activity
6. **ml_features**: Extracted features for training

## Deployment

### Local Development
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Docker
```bash
docker build -t angel-x .
docker run -p 5000:5000 angel-x
```

### Kubernetes
```bash
kubectl apply -f infra/kubernetes/
```

### Systemd Service
```bash
sudo cp infra/systemd/angel-x.service /etc/systemd/system/
sudo systemctl enable angel-x
sudo systemctl start angel-x
```

## Monitoring

### Metrics Collected
- Trade win rate and P&L
- Entry signal accuracy
- Greeks exposure metrics
- System performance (latency, memory)

### Health Checks
- Broker connectivity
- Database connection
- Data feed latency
- API responsiveness

### Alerts
- Trade losses exceeding threshold
- Greeks exposure warnings
- System performance degradation
- Broker disconnections
