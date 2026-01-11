# ANGEL-X Professional Test Suite

## Test Structure

```
tests/
├── unit/              # Fast, isolated component tests (~1ms each)
├── integration/       # Component interaction tests (~50ms each)
├── e2e/              # Full system end-to-end tests (~200ms+)
├── fixtures/         # Test data and mock objects
├── mocks/            # Mock implementations of components
├── conftest.py       # Shared pytest configuration
└── README.md         # This file
```

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run specific test category
```bash
# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests
pytest tests/e2e/ -v
```

### Run with markers
```bash
# Fast tests only (unit + integration)
pytest -m "not slow" -v

# Smoke tests (quick validation)
pytest -m smoke -v

# Exclude E2E tests
pytest -m "not e2e" -v
```

### Run with coverage
```bash
pytest --cov=src --cov-report=html tests/
```

### Run with multiple workers (faster)
```bash
pytest -n auto tests/
```

## Test Organization

### Unit Tests
Fast, isolated tests for individual components:

- `test_position_sizing.py` - Position size calculation, risk limits
- `test_bias_engine.py` - Market bias detection logic
- `test_entry_engine.py` - Entry signal generation
- More coming: Greeks calculation, Order management, Trade management

**Run time:** ~5-10 seconds for all unit tests

### Integration Tests
Component interaction tests:

- `test_strategy_flow.py` - Bias + Entry Engine interaction
  - Bullish bias enables calls
  - Bearish bias enables puts
  - Trap detection blocks entries
  - Position sizing respects limits

**Run time:** ~10-20 seconds

### E2E Tests
Full system execution simulations:

- `test_full_execution.py` - Complete trade flows
  - Entry to exit scenarios
  - IV trap rejection
  - Stop loss execution
  - Daily loss limit enforcement
  - Full market day simulation

**Run time:** ~30-60 seconds

## Fixtures and Mocks

### Mock Objects (`tests/mocks/__init__.py`)
Pre-built mock implementations:
- `MockDataFeed` - Simulates WebSocket data
- `MockOrderManager` - Simulates order execution
- `MockTradeManager` - Simulates trade lifecycle
- `MockGreeksManager` - Simulates Greeks calculation
- `MockBiasEngine` - Simulates market bias detection
- `MockEntryEngine` - Simulates entry signals

### Test Data (`tests/fixtures/market_data.py`)
Reusable test data:
- `MockTick` - Market tick data
- `MockGreeks` - Greeks snapshot
- `MockPosition` - Trading position
- `tick_data_sequence` - Pre-configured tick sequences

## Test Development Guide

### Writing a Unit Test
```python
@pytest.mark.unit
class TestMyComponent:
    """Test MyComponent functionality"""
    
    def test_something_works(self, mock_config, sample_tick):
        """Test description"""
        # Arrange
        component = MyComponent(mock_config)
        
        # Act
        result = component.do_something(sample_tick)
        
        # Assert
        assert result == expected_value
```

### Writing an Integration Test
```python
@pytest.mark.integration
class TestComponentInteraction:
    """Test component A + B interaction"""
    
    def test_components_work_together(self, mock_config):
        """Test description"""
        engine_a = EngineA()
        engine_b = EngineB()
        
        result_a = engine_a.process(data)
        result_b = engine_b.process(result_a)
        
        assert result_b.is_valid()
```

### Writing an E2E Test
```python
@pytest.mark.e2e
class TestFullFlow:
    """Test complete trading flow"""
    
    def test_entry_to_exit(self, tick_data_sequence):
        """Simulate complete trade"""
        # Setup full system
        system = FullSystem()
        
        # Run through tick sequence
        for tick in tick_data_sequence:
            system.process_tick(tick)
        
        # Verify outcome
        assert system.trades_closed > 0
        assert system.pnl > 0
```

## Continuous Integration

### Pre-commit Checks
```bash
# Run unit tests before committing
pytest tests/unit/ -x
```

### CI/CD Pipeline
1. **Unit tests** (fast, always runs) ~10s
2. **Integration tests** (if unit pass) ~20s
3. **E2E tests** (if integration pass) ~60s
4. **Coverage report** (if all pass)

### Markers for CI
- Use `@pytest.mark.skip_ci` to skip in CI
- Use `@pytest.mark.slow` to skip in fast CI runs

## Coverage Goals

- **Unit tests:** 85%+ coverage
- **Integration tests:** 60%+ coverage
- **E2E tests:** Critical paths coverage

Current coverage: See `htmlcov/index.html` after running:
```bash
pytest --cov=src --cov-report=html
```

## Common Issues

### Imports failing in tests
- Ensure `tests/` is a package (has `__init__.py`)
- Ensure project root is in sys.path (conftest.py handles this)

### Fixtures not found
- Check fixture is in `conftest.py` or same test file
- Check fixture name matches exactly

### Mock objects not working
- Verify mock is imported from `tests.mocks`
- Check mock methods match real implementation

## Future Test Coverage

Areas needing tests:
- Greeks calculation engine
- Trade journal logging
- Expiry manager
- Network resilience
- Risk manager veto logic
- WebSocket data feed
- Order manager
- Exchange integration

Add these tests to respective unit/ or integration/ subdirectories.

## Tips

1. **Use markers** to categorize tests
2. **Use fixtures** to reduce test code
3. **Use mocks** to isolate components
4. **Keep unit tests fast** (<1ms each)
5. **Keep integration tests moderate** (<100ms each)
6. **Use parametrize** for multiple scenarios

Example parametrize:
```python
@pytest.mark.parametrize("input,expected", [
    (0.55, True),
    (0.35, False),
    (0.70, False),
])
def test_delta_zones(self, input, expected):
    assert engine.is_in_power_zone(input) == expected
```

## Contributing

When adding new tests:
1. Place in appropriate directory (unit/integration/e2e)
2. Use `@pytest.mark.xxx` decorator
3. Add to this README
4. Ensure coverage doesn't decrease
5. Keep tests independent (no ordering dependencies)

## Questions?

Refer to pytest documentation: https://docs.pytest.org
