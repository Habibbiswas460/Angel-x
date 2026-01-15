# Contributing to Angel-X

Thank you for your interest in contributing to Angel-X! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project adheres to the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

### Our Pledge
We are committed to providing a welcoming and inspiring community for all. We expect everyone to show respect and courtesy to others.

## Getting Started

### Prerequisites
- Python 3.8+
- Git
- Docker (optional, for testing)
- Basic understanding of options trading

### Development Environment Setup

1. **Fork the Repository**
   ```bash
   # Visit https://github.com/your-org/Angel-x
   # Click "Fork" button
   ```

2. **Clone Your Fork**
   ```bash
   git clone https://github.com/habibbiswa460/Angel-x.git
   cd Angel-x
   ```

3. **Add Upstream Remote**
   ```bash
   git remote add upstream https://github.com/your-org/Angel-x.git
   ```

4. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

5. **Install Development Dependencies**
   ```bash
   pip install -r requirements-test.txt
   pip install -r requirements.txt
   ```

6. **Set Up Pre-commit Hooks**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Development Workflow

### Create a Feature Branch

Use conventional branch naming:
```bash
# Feature branch
git checkout -b feature/short-description

# Bug fix branch
git checkout -b fix/short-description

# Documentation branch
git checkout -b docs/short-description

# Examples
git checkout -b feature/broker-optimization
git checkout -b fix/websocket-reconnect
git checkout -b docs/api-reference
```

### Making Changes

1. **Write Code**
   - Follow PEP 8 style guide
   - Use meaningful variable names
   - Add comments for complex logic
   - Keep functions small and focused

2. **Format Code**
   ```bash
   # Auto-format with black
   black src/ tests/
   
   # Sort imports
   isort src/ tests/
   ```

3. **Lint Code**
   ```bash
   # Check code style
   pylint src/
   flake8 src/
   
   # Type checking
   mypy src/
   ```

4. **Run Tests**
   ```bash
   # Run all tests
   pytest tests/ -v
   
   # Run with coverage
   pytest tests/ --cov=src --cov-report=html
   
   # Run specific test file
   pytest tests/unit/test_broker.py -v
   ```

5. **Write Tests**
   - Add unit tests for new functions
   - Add integration tests for broker interactions
   - Aim for 80%+ code coverage
   - Use descriptive test names

   ```python
   # Good test name
   def test_place_order_returns_order_id_on_success():
       """Test that place_order returns a valid order ID"""
       
   # Bad test name
   def test_order():
       """Order test"""
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation changes
- `style` - Code style changes (formatting, semicolons, etc.)
- `refactor` - Code refactoring without feature changes
- `perf` - Performance improvements
- `test` - Adding/updating tests
- `chore` - Build, CI, dependencies, etc.

**Scopes:**
- `broker` - Broker integration
- `trading` - Trading engine
- `ml` - Machine learning
- `monitoring` - Health monitoring
- `api` - API endpoints
- `database` - Database layer
- `docker` - Docker configuration

**Examples:**

```bash
# Good commit messages
git commit -m "feat(broker): implement real order placement

- Replace placeholder with actual SmartAPI call
- Handle order response parsing
- Add proper error handling

Fixes #123"

git commit -m "fix(websocket): improve reconnection logic

- Add exponential backoff for retries
- Handle connection timeout gracefully
- Log reconnection attempts

Closes #456"

git commit -m "docs: add deployment guide for Kubernetes"

git commit -m "test: add unit tests for Greeks calculation"
```

### Push and Create Pull Request

1. **Update with Latest Changes**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Push to Your Fork**
   ```bash
   git push origin feature/short-description
   ```

3. **Create Pull Request**
   - Visit https://github.com/your-org/Angel-x
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template (below)

### Pull Request Template

```markdown
## Description
Brief description of the changes

## Related Issue
Fixes #123

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Breaking change

## Changes
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed
- [ ] No new warnings

## Checklist
- [ ] Code follows style guide
- [ ] Self-review completed
- [ ] Comments added for complex logic
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
- [ ] Tested with paper trading

## Screenshots (if applicable)
[Add screenshots for UI changes]

## Additional Notes
Any additional information for reviewers
```

## Testing Guidelines

### Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Specific test file
pytest tests/unit/test_broker.py -v

# Specific test function
pytest tests/unit/test_broker.py::test_connect -v

# With coverage
pytest tests/ --cov=src --cov-report=html

# Fast tests only (skip slow markers)
pytest -m "not slow" -v

# Run tests matching pattern
pytest -k "broker" -v
```

### Writing Tests

**Test File Structure:**
```
tests/
├── unit/
│   ├── test_broker.py
│   ├── test_trading.py
│   └── test_ml.py
├── integration/
│   └── test_broker_integration.py
└── e2e/
    └── test_trading_flow.py
```

**Test Template:**
```python
import pytest
from unittest.mock import patch, MagicMock
from src.integrations.broker import BrokerClient

class TestBrokerClient:
    """Test suite for BrokerClient"""
    
    @pytest.fixture
    def broker(self):
        """Create broker instance for testing"""
        return BrokerClient(
            api_key="test-key",
            client_code="test-code"
        )
    
    def test_connect_success(self, broker):
        """Test successful broker connection"""
        result = broker.connect()
        assert result is True
    
    def test_connect_failure_invalid_credentials(self, broker):
        """Test connection failure with invalid credentials"""
        broker.api_key = "invalid"
        result = broker.connect()
        assert result is False
    
    @patch('src.integrations.broker.SmartConnect')
    def test_place_order_returns_order_id(self, mock_connect, broker):
        """Test that place_order returns order ID"""
        mock_connect.return_value.placeOrder.return_value = {
            'status': True,
            'data': {'orderid': '123'}
        }
        
        result = broker.place_order(symbol='NIFTY', qty=1)
        assert result['orderid'] == '123'
```

## Code Style

### Python Style Guide
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Max line length: 100 characters
- Use type hints
- Document complex functions

### Example:
```python
from typing import Optional, Dict, List

def calculate_greeks(
    spot: float,
    strike: float,
    rate: float,
    expiry_days: int,
    volatility: float
) -> Dict[str, float]:
    """
    Calculate option Greeks using Black-Scholes.
    
    Args:
        spot: Current spot price
        strike: Strike price
        rate: Risk-free rate
        expiry_days: Days to expiry
        volatility: Implied volatility
    
    Returns:
        Dictionary with delta, gamma, theta, vega
    
    Raises:
        ValueError: If inputs are invalid
    
    Example:
        >>> greeks = calculate_greeks(100, 105, 0.05, 30, 0.2)
        >>> greeks['delta']
        0.65
    """
    # Implementation
    pass
```

## Documentation

### Docstring Format
Use Google-style docstrings:

```python
def place_order(
    self,
    symbol: str,
    qty: int,
    side: str = "BUY"
) -> Dict:
    """Place an order with the broker.
    
    Args:
        symbol: Trading symbol (e.g., 'NIFTY23JAN2624000CE')
        qty: Order quantity
        side: 'BUY' or 'SELL', defaults to 'BUY'
    
    Returns:
        Order response dict with keys:
            - orderid: Broker order ID
            - status: 'success' or 'failed'
            - message: Status message
    
    Raises:
        ConnectionError: If broker connection fails
        ValueError: If symbol or qty is invalid
    
    Example:
        >>> order = broker.place_order('NIFTY23JAN2624000CE', 1)
        >>> print(order['orderid'])
        '12345'
    """
```

### README Updates
- Update README.md if adding new features
- Add examples for new functionality
- Update API docs if changing endpoints

### API Documentation
- Add docstrings to all public methods
- Document all parameters and return values
- Include usage examples

## Reporting Issues

### Bug Reports

Include:
- ✅ Clear title describing the issue
- ✅ Steps to reproduce
- ✅ Expected behavior
- ✅ Actual behavior
- ✅ Screenshots/logs if applicable
- ✅ Environment (Python version, OS, etc.)

**Example:**
```
Title: WebSocket disconnects after 5 minutes of inactivity

Steps to reproduce:
1. Connect to broker
2. Wait 5 minutes without sending data
3. Observe connection closes

Expected: Connection should remain active
Actual: Connection closes with error "Connection reset by peer"

Environment: Python 3.8, Ubuntu 20.04, Angel-X v2.0.0
```

### Feature Requests

Include:
- ✅ Clear description of desired feature
- ✅ Use case/motivation
- ✅ Example of how it would work
- ✅ Any implementation notes

## Review Process

1. **Automated Checks**
   - GitHub Actions runs tests
   - Linting and formatting checked
   - Code coverage verified

2. **Code Review**
   - At least 2 approvals required
   - Reviewers check logic, style, tests
   - Feedback provided on PR

3. **Merge**
   - All checks must pass
   - All conversations resolved
   - Branch auto-deleted after merge

## Release Process

1. **Version Bump**
   ```bash
   # Update version in src/__version__.py
   __version__ = "2.1.0"
   ```

2. **Update CHANGELOG.md**
   ```markdown
   ## [2.1.0] - 2026-02-01
   
   ### Added
   - New feature
   
   ### Fixed
   - Bug fix
   ```

3. **Create Release**
   ```bash
   git tag -a v2.1.0 -m "Release version 2.1.0"
   git push origin v2.1.0
   ```

## Communication

### Where to Ask Questions
- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and discussions
- **Discord** - Community chat and real-time help
- **Email** - Private concerns (contributors@your-org.com)

### Response Times
- Critical bugs: 24 hours
- Important issues: 48 hours
- Other issues: 1 week

## Becoming a Maintainer

Experienced contributors may be invited to become maintainers. This includes:
- ✅ Merge privileges
- ✅ Issue/PR management
- ✅ Release responsibilities
- ✅ Community support

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

- Read [FAQ](docs/FAQ.md)
- Check [Documentation](docs/)
- Join [Discord Community](https://discord.gg/your-link)
- Email: contributors@your-org.com

---

**Thank you for contributing to Angel-X! ❤️**

*Last Updated: January 12, 2026*
