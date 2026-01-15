# Testing Guide for Angel-X

**Comprehensive testing framework with pytest**

---

## 🧪 Testing Framework

Angel-X uses **pytest** for testing with the following structure:

```
tests/
├── conftest.py              # Shared fixtures and configuration
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_trade_model.py
│   ├── test_performance_model.py
│   ├── test_config.py
│   └── test_imports.py
├── integration/             # Integration tests (database, API)
│   └── test_database_operations.py
└── e2e/                     # End-to-end tests (full system)
```

---

## 🚀 Quick Start

### Install Test Dependencies

```bash
# Install testing requirements
pip install -r requirements-test.txt

# Or install individually
pip install pytest pytest-cov pytest-xdist
```

### Run All Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run with detailed output
pytest -v

# Run specific test file
pytest tests/unit/test_trade_model.py
```

---

## 📋 Test Categories

### Unit Tests (Fast)

```bash
# Run only unit tests
pytest -m unit

# Run specific unit test file
pytest tests/unit/test_trade_model.py

# Run specific test function
pytest tests/unit/test_trade_model.py::TestTradeModel::test_create_trade
```

**Unit test files:**
- `test_trade_model.py` - Trade model tests
- `test_performance_model.py` - Performance model tests
- `test_config.py` - Configuration tests
- `test_imports.py` - Module import tests

### Integration Tests (Slower)

```bash
# Run only integration tests
pytest -m integration

# Run database integration tests
pytest tests/integration/test_database_operations.py
```

**Integration test files:**
- `test_database_operations.py` - Complex database queries

### End-to-End Tests

```bash
# Run e2e tests
pytest -m e2e

# Run e2e tests (requires full system)
pytest tests/e2e/
```

---

## 🎯 Test Markers

Tests are organized with markers for selective execution:

```python
@pytest.mark.unit         # Unit tests
@pytest.mark.integration  # Integration tests
@pytest.mark.database     # Requires database
@pytest.mark.api          # Requires API
@pytest.mark.slow         # Slow tests
@pytest.mark.smoke        # Critical functionality
```

### Run Tests by Marker

```bash
# Run only database tests
pytest -m database

# Run everything except slow tests
pytest -m "not slow"

# Run unit and integration tests
pytest -m "unit or integration"

# Run smoke tests only
pytest -m smoke
```

---

## 📊 Coverage Reports

### Generate Coverage Report

```bash
# Run with coverage (terminal output)
pytest --cov=src --cov=app

# Generate HTML coverage report
pytest --cov=src --cov=app --cov-report=html

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Coverage Configuration

Coverage settings in `pytest.ini`:
```ini
[coverage:run]
source = src,app
omit = */tests/*, */venv/*

[coverage:report]
precision = 2
show_missing = True
```

---

## ⚙️ Pytest Configuration

Configuration in `pytest.ini`:

```ini
[pytest]
# Test discovery
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# Test paths
testpaths = tests

# Options
addopts =
    -v                    # Verbose
    --tb=short           # Short tracebacks
    --showlocals         # Show local variables
    --cov=src           # Coverage
    --strict-markers    # Strict marker checking
```

---

## 🔧 Test Fixtures

### Database Fixtures

```python
# Use in-memory database for tests
def test_example(db_session):
    # db_session is automatically created and cleaned up
    trade = Trade(symbol='NIFTY', strike_price=22000.0)
    db_session.add(trade)
    db_session.commit()
```

### Factory Fixtures

```python
# Create test data easily
def test_example(create_trade):
    # create_trade is a factory fixture
    trade = create_trade(symbol='BANKNIFTY', strike_price=48000.0)
    assert trade.id is not None
```

### Available Fixtures

From `conftest.py`:

**Database:**
- `test_db_engine` - Test database engine
- `db_session` - Database session
- `clean_db` - Clean database

**Factories:**
- `create_trade` - Create trade
- `create_performance` - Create performance
- `create_market_data` - Create market data
- `create_account_history` - Create account history

**Data:**
- `sample_trade_data` - Sample trade data
- `sample_performance_data` - Sample performance data
- `sample_market_data` - Sample market data
- `sample_account_data` - Sample account data

**Configuration:**
- `test_config` - Test configuration
- `mock_env` - Mock environment variables

---

## ✍️ Writing Tests

### Example Unit Test

```python
import pytest
from src.database.models.trade import Trade

@pytest.mark.unit
class TestTrade:
    def test_create_trade(self, create_trade):
        """Test creating a trade"""
        trade = create_trade(symbol='NIFTY', strike_price=22000.0)
        
        assert trade.id is not None
        assert trade.symbol == 'NIFTY'
        assert trade.strike_price == 22000.0
```

### Example Integration Test

```python
import pytest
from sqlalchemy import func
from src.database.models.trade import Trade

@pytest.mark.integration
@pytest.mark.database
class TestTradeQueries:
    def test_total_pnl(self, create_trade, db_session):
        """Test calculating total P&L"""
        create_trade(net_pnl=700.0)
        create_trade(net_pnl=500.0)
        
        total = db_session.query(func.sum(Trade.net_pnl)).scalar()
        assert total == 1200.0
```

### Parametrized Tests

```python
@pytest.mark.parametrize('symbol,strike,expected', [
    ('NIFTY', 22000.0, 22000.0),
    ('BANKNIFTY', 48000.0, 48000.0),
])
def test_strikes(create_trade, symbol, strike, expected):
    trade = create_trade(symbol=symbol, strike_price=strike)
    assert trade.strike_price == expected
```

---

## 🔄 Continuous Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.12'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
```

### GitLab CI Example

```yaml
test:
  stage: test
  image: python:3.12
  script:
    - pip install -r requirements.txt
    - pip install -r requirements-test.txt
    - pytest --cov --cov-report=term
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

---

## 🐛 Debugging Tests

### Run Single Test with Debug

```bash
# Run single test with full output
pytest tests/unit/test_trade_model.py::TestTradeModel::test_create_trade -v -s

# Show local variables on failure
pytest --showlocals

# Drop into debugger on failure
pytest --pdb

# Drop into debugger at start
pytest --trace
```

### Using pytest fixtures for debugging

```python
def test_debug(create_trade, db_session):
    trade = create_trade()
    
    # Add breakpoint
    import pdb; pdb.set_trace()
    
    # Continue testing
    assert trade.id is not None
```

---

## 📈 Performance Testing

### Run Tests in Parallel

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (auto-detect CPUs)
pytest -n auto

# Run with 4 workers
pytest -n 4
```

### Show Test Durations

```bash
# Show 10 slowest tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

---

## ✅ Best Practices

### 1. Test Organization

- **Unit tests**: Test individual components in isolation
- **Integration tests**: Test component interactions
- **E2E tests**: Test complete workflows

### 2. Test Naming

```python
# Good
def test_trade_creation_with_valid_data():
    ...

def test_trade_creation_raises_error_with_negative_strike():
    ...

# Bad
def test_1():
    ...

def test_trade():
    ...
```

### 3. Use Fixtures

```python
# Good - reusable
def test_with_fixture(create_trade):
    trade = create_trade()
    ...

# Bad - duplicated setup
def test_without_fixture(db_session):
    trade = Trade(symbol='NIFTY', ...)
    db_session.add(trade)
    ...
```

### 4. Test One Thing

```python
# Good
def test_trade_creation():
    trade = create_trade()
    assert trade.id is not None

def test_trade_symbol():
    trade = create_trade(symbol='NIFTY')
    assert trade.symbol == 'NIFTY'

# Bad
def test_trade():
    trade = create_trade()
    assert trade.id is not None
    assert trade.symbol == 'NIFTY'
    assert trade.status == TradeStatus.OPEN
    # ... many more assertions
```

### 5. Use Markers

```python
@pytest.mark.slow
def test_heavy_computation():
    ...

@pytest.mark.database
def test_database_query():
    ...
```

---

## 🚦 Test Coverage Goals

**Target Coverage:** 80%+

**Priority Areas:**
- ✅ Models: 90%+ (critical business logic)
- ✅ Database operations: 85%+
- ✅ Configuration: 80%+
- ⚠️ API endpoints: 70%+ (when implemented)
- ⚠️ Trading logic: 95%+ (when implemented)

---

## 📚 Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/latest/fixture.html)
- [Pytest Markers](https://docs.pytest.org/en/latest/mark.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

## 🆘 Troubleshooting

### Tests Fail with Import Errors

```bash
# Ensure project root is in PYTHONPATH
export PYTHONPATH=$PWD:$PYTHONPATH
pytest
```

### Database Locked Errors

```bash
# Use in-memory database (default in tests)
# Or ensure only one test runs at a time
pytest -n 0
```

### Fixture Not Found

```bash
# Ensure conftest.py is in tests/ directory
ls tests/conftest.py

# Check fixture name matches
pytest --fixtures  # List all available fixtures
```

---

**Version:** 1.0  
**Last Updated:** January 15, 2026  
**Status:** ✅ Production Ready
