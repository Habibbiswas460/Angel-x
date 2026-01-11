# Professional Paper Trading System

## Overview

ANGEL-X includes a production-grade paper trading system that simulates real trading with realistic market mechanics, comprehensive tracking, and detailed analytics.

## Features

✅ **Realistic Order Execution**
- Market order simulation
- Slippage modeling with market impact
- Limit order support

✅ **Position Management**
- Long position support
- Short position support
- Real-time P&L tracking
- Position monitoring

✅ **Margin Management**
- Margin requirement calculation
- Margin utilization tracking
- Available margin monitoring

✅ **Comprehensive Analytics**
- Trade statistics (win rate, P&L, etc.)
- Equity curve tracking
- Maximum drawdown calculation
- Performance metrics

✅ **Trade Journaling**
- Detailed trade logging
- CSV export
- JSON export
- Performance reports

## Components

### 1. PaperTradingEngine (`src/core/paper_trading.py`)

Main trading engine that simulates order execution and position management.

```python
from src.core.paper_trading import PaperTradingEngine

# Initialize engine
engine = PaperTradingEngine()

# Place an order
success, order, message = engine.place_order(
    symbol='NIFTY_25JAN26_19000CE',
    action='BUY',
    quantity=75,
    price=100.0,
    order_type='LIMIT'
)

# Update position price (for real-time P&L)
engine.update_position_price('NIFTY_25JAN26_19000CE', 105.0)

# Get statistics
stats = engine.get_statistics()
print(f"Capital: ₹{stats['current_capital']:,.2f}")
print(f"Net P&L: ₹{stats['net_pnl']:+,.2f}")
print(f"Win Rate: {stats['win_rate']:.2f}%")

# Get open positions
positions = engine.get_positions()

# Export session
engine.export_to_json('session.json')
```

### 2. PaperTradingJournal (`src/core/paper_trading_journal.py`)

Detailed trade journal with export capabilities.

```python
from src.core.paper_trading_journal import PaperTradingJournal

journal = PaperTradingJournal()

# Log a closed trade
journal.log_trade(
    trade_id='TRADE_001',
    symbol='NIFTY_25JAN26_19000CE',
    option_type='CE',
    strike=19000,
    entry_time=datetime.now(),
    entry_price=100.0,
    entry_delta=0.55,
    exit_time=datetime.now(),
    exit_price=107.0,
    exit_reason='Profit Target',
    quantity=75,
    pnl_amount=525.0,
    pnl_percent=7.0,
    time_in_trade_seconds=300
)

# Export trades
journal.export_csv()
journal.export_json()

# Generate performance report
journal.export_performance_report()

# Get summary
summary = journal.get_summary()
```

## Order Execution

### Flow

1. **Order Placement** → Order validated
2. **Margin Check** → Verify available margin
3. **Order Execution** → Simulate order fill
4. **Slippage Applied** → Add realistic slippage
5. **Position Updated** → Open/close position
6. **Margin Updated** → Adjust available margin

### Order Status

```
PENDING        → Order created, awaiting execution
FILLED         → Order fully executed
PARTIALLY_FILLED → Order partially executed
REJECTED       → Order rejected
CANCELLED      → Order cancelled
EXPIRED        → Order expired
```

### Slippage Calculation

Slippage is calculated based on:
- Base slippage percentage (configurable)
- Market impact (based on order size)
- Order direction (BUY/SELL)

```python
slippage = (base_slippage + market_impact) × direction
```

## Margin Management

### Margin Requirement

```
Margin Required = (Price × Quantity) × 15%  # Default 15% margin
```

### Margin Tracking

- **Utilized Margin**: Amount locked in open positions
- **Available Margin**: Remaining capital for new trades
- **Total Capital**: Utilized + Available

```python
# Check margin status
stats = engine.get_statistics()
utilized = stats['utilized_margin']
available = stats['available_margin']
```

## Position Tracking

### Open Position

```python
position = engine.positions[symbol]
pnl_rupees, pnl_percent = position.calculate_pnl()
print(f"Current P&L: ₹{pnl_rupees:+,.2f} ({pnl_percent:+.2f}%)")
```

### Closed Position

```python
for trade in engine.closed_trades:
    print(f"{trade.symbol}: ₹{trade.calculate_pnl()[0]:+,.2f}")
```

## Statistics

### Available Statistics

```python
stats = engine.get_statistics()

# Capital metrics
stats['initial_capital']      # Starting capital
stats['current_capital']      # Current capital
stats['net_pnl']              # Net profit/loss
stats['gross_pnl']            # Gross profit/loss
stats['return_percent']       # Return percentage

# Trade metrics
stats['total_trades']         # Total trades executed
stats['winning_trades']       # Number of winning trades
stats['losing_trades']        # Number of losing trades
stats['win_rate']             # Win rate percentage

# Risk metrics
stats['max_drawdown']         # Maximum drawdown in rupees
stats['drawdown_percent']     # Maximum drawdown percentage

# Position metrics
stats['open_positions']       # Number of open positions
stats['utilized_margin']      # Margin locked in positions
stats['available_margin']     # Available margin for new trades
```

## Trade Journal

### Logging Trades

```python
journal.log_trade(
    trade_id='TRADE_001',
    symbol='NIFTY_25JAN26_19000CE',
    option_type='CE',
    strike=19000,
    entry_time=datetime.now(),
    entry_price=100.0,
    entry_delta=0.55,
    entry_gamma=0.003,
    entry_theta=-0.02,
    entry_vega=0.05,
    entry_iv=25.0,
    exit_time=datetime.now(),
    exit_price=107.0,
    exit_delta=0.60,
    exit_gamma=0.003,
    exit_reason='Profit Target',
    quantity=75,
    pnl_amount=525.0,
    pnl_percent=7.0,
    time_in_trade_seconds=300,
    entry_spread=0.5,
    exit_spread=0.6,
    entry_reason_tags=['BULLISH_BIAS', 'GAMMA_RISING'],
    exit_reason_tags=['PROFIT_TARGET'],
    slippage=5.0
)
```

### Export Formats

#### CSV Export
```python
journal.export_csv('trades.csv')
```

Exports all trades with columns for:
- Trade ID, Symbol, Option Type, Strike, Quantity
- Entry/Exit prices, Greeks, Delta values
- P&L metrics, Time in trade
- Spreads, Slippage, Reason tags

#### JSON Export
```python
journal.export_json('trades.json')
```

Exports structured JSON with:
- Session metadata
- Array of trade objects
- Summary statistics

#### Performance Report
```python
journal.export_performance_report('report.txt')
```

Generates text report with:
- Trade count and win rate
- P&L summary
- Best/worst trades
- Trade duration analysis

## Configuration

### Paper Trading Config

```python
# In config/config.py
CAPITAL = 100000                           # Initial capital
BACKTEST_SLIPPAGE_PERCENT = 0.05          # Slippage percentage
MAX_POSITION_SIZE = 150                   # Max position quantity
MAX_CONCURRENT_POSITIONS = 1              # Max open positions
MAX_TRADES_PER_DAY = 5                    # Daily trade limit
JOURNAL_DIR = './journal'                 # Journal output directory
```

## Usage Examples

### Example 1: Simple Trading

```python
from src.core.paper_trading import PaperTradingEngine

engine = PaperTradingEngine()

# Entry trade
success, entry_order, msg = engine.place_order(
    symbol='NIFTY_25JAN26_19000CE',
    action='BUY',
    quantity=75,
    price=100.0
)

if success:
    print(f"Entry: {entry_order.average_price}")
    
    # Update position price
    engine.update_position_price('NIFTY_25JAN26_19000CE', 105.0)
    
    # Exit trade
    success, exit_order, msg = engine.place_order(
        symbol='NIFTY_25JAN26_19000CE',
        action='SELL',
        quantity=75,
        price=105.0
    )
    
    print(f"Exit: {exit_order.average_price}")
    print(f"P&L: ₹{engine.gross_pnl:+,.2f}")
```

### Example 2: Multiple Trades with Statistics

```python
from src.core.paper_trading import PaperTradingEngine

engine = PaperTradingEngine()

trades = [
    ('NIFTY_25JAN26_19000CE', 100.0, 107.0),
    ('NIFTY_25JAN26_19000PE', 50.0, 48.0),
    ('NIFTY_25JAN26_19100CE', 95.0, 92.0),
]

for symbol, entry, exit_price in trades:
    engine.place_order(symbol, 'BUY', 75, entry)
    engine.place_order(symbol, 'SELL', 75, exit_price)

stats = engine.get_statistics()
print(f"Total Trades: {stats['total_trades']}")
print(f"Win Rate: {stats['win_rate']:.2f}%")
print(f"Net P&L: ₹{stats['net_pnl']:+,.2f}")
print(f"Return: {stats['return_percent']:.2f}%")
```

### Example 3: Session Export

```python
from src.core.paper_trading import PaperTradingEngine
from src.core.paper_trading_journal import PaperTradingJournal

engine = PaperTradingEngine()
journal = PaperTradingJournal()

# Execute trades...

# Export results
engine.export_to_json('session.json')
journal.export_csv()
journal.export_performance_report()
```

## Testing

Unit tests are available in `tests/unit/test_paper_trading.py`:

```bash
# Run paper trading tests
pytest tests/unit/test_paper_trading.py -v

# Run all unit tests
pytest tests/unit/ -v
```

## Best Practices

1. **Initialize Engine**: Create fresh engine for each session
2. **Validate Orders**: Always check order success status
3. **Track Positions**: Monitor real-time P&L with price updates
4. **Export Regularly**: Save session data for analysis
5. **Review Reports**: Analyze performance metrics regularly

## Common Issues

### Issue: Orders Being Rejected

**Cause**: Insufficient margin
**Solution**: Check available margin, reduce position size, or add capital

### Issue: P&L Not Updating

**Cause**: Position prices not being updated
**Solution**: Call `update_position_price()` with current market price

### Issue: High Slippage

**Cause**: Large order size or volatile market
**Solution**: Reduce order quantity or adjust slippage configuration

## Future Enhancements

- [ ] Multiple concurrent positions
- [ ] Partial position closing
- [ ] Stop loss and take profit automation
- [ ] Real-time performance charts
- [ ] Advanced risk metrics (Sharpe ratio, Sortino ratio)
- [ ] Machine learning optimization

## Support

For issues or questions about paper trading, refer to:
- Test files: `tests/unit/test_paper_trading.py`
- Examples: See "Usage Examples" section above
- Configuration: `config/config.py`
