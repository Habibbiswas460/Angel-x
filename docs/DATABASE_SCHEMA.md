# Database Schema Documentation

**Angel-X Trading System Database Schema**

---

## 📊 Overview

The Angel-X database stores:
- **Trades:** Entry/exit records with P&L and Greeks
- **Performance:** Daily/weekly/monthly metrics
- **Market Data:** OHLC and Greeks snapshots
- **Account History:** Balance and transaction records

---

## 🗄️ Supported Databases

- **SQLite** (default) - Embedded database, no setup required
- **PostgreSQL** - Production-grade RDBMS

---

## 📋 Database Models

### 1. Trade Model (`trades` table)

Stores individual trade records.

**Key Fields:**
- `trade_id` - Unique identifier
- `status` - open/closed/cancelled/error
- `symbol` - NIFTY, BANKNIFTY, etc.
- `option_type` - call/put
- `strike_price` - Option strike
- `expiry_date` - Option expiry
- Entry details (time, price, quantity, order_id)
- Entry Greeks (delta, gamma, theta, vega, IV)
- Exit details (time, price, quantity, order_id)
- Exit Greeks (delta, gamma, theta, vega, IV)
- P&L (gross, net, brokerage, taxes)
- Risk metrics (stop loss, target, max loss/profit)
- Metadata (strategy, tags, notes)

**Indexes:**
- `trade_id` (unique)
- `status`
- `symbol`
- `entry_time`
- `strategy_name`
- Composite: (symbol, entry_time)
- Composite: (status, entry_time)

**Example:**
```python
from src.database.models import Trade
from datetime import datetime

trade = Trade(
    trade_id="NIFTY_CE_24000_20260115_001",
    status="open",
    symbol="NIFTY",
    option_type="call",
    strike_price=24000,
    expiry_date=datetime(2026, 1, 15),
    entry_time=datetime.now(),
    entry_price=150.50,
    entry_quantity=50,
    # ... more fields
)
```

---

### 2. Performance Model (`performance` table)

Stores aggregated performance metrics.

**Key Fields:**
- `period` - daily/weekly/monthly/yearly
- `period_date` - Date of the period
- Trade statistics (total, winning, losing, breakeven)
- P&L (gross, net, brokerage, taxes)
- Win/loss metrics (rate, avg, largest)
- Risk metrics (drawdown, Sharpe, Sortino)
- Capital metrics (starting, ending, peak)
- Trade duration stats
- Greeks exposure (delta, gamma, theta)
- Strategy breakdown

**Indexes:**
- Unique: (period, period_date)
- `period`
- `period_date`
- `is_paper_trading`

**Example:**
```python
from src.database.models import Performance
from datetime import date

perf = Performance(
    period="daily",
    period_date=date(2026, 1, 15),
    total_trades=10,
    winning_trades=7,
    losing_trades=3,
    net_pnl=5000.0,
    win_rate=70.0,
    # ... more fields
)
```

---

### 3. MarketData Model (`market_data` table)

Stores OHLC data and market snapshots.

**Key Fields:**
- `symbol` - Underlying symbol
- `option_type` - call/put or NULL for underlying
- `strike_price` - Option strike (if option)
- `expiry_date` - Option expiry (if option)
- `timestamp` - Data snapshot time
- `interval` - tick/1min/5min/15min/1hour/day
- OHLC (open, high, low, close)
- Volume and open interest
- Bid/ask prices and quantities
- Greeks (delta, gamma, theta, vega, IV)
- Underlying price
- Market metrics (LTP, LTQ, buy/sell qty)

**Indexes:**
- `symbol`
- `timestamp`
- `interval`
- Composite: (symbol, timestamp)
- Composite: (symbol, interval, timestamp)
- Composite: (symbol, strike_price, expiry_date, timestamp)

**Example:**
```python
from src.database.models import MarketData
from datetime import datetime

data = MarketData(
    symbol="NIFTY",
    option_type="call",
    strike_price=24000,
    timestamp=datetime.now(),
    interval="1min",
    close_price=150.50,
    delta=0.5,
    # ... more fields
)
```

---

### 4. AccountHistory Model (`account_history` table)

Stores account transactions and balance snapshots.

**Key Fields:**
- `transaction_id` - Unique identifier
- `transaction_date` - Transaction timestamp
- `transaction_type` - trade_profit/loss/brokerage/deposit/etc.
- `amount` - Transaction amount (+credit, -debit)
- Balance details (before, after, available, blocked)
- Margin details (used, available, percentage)
- Related IDs (trade_id, order_id)
- Broker details (reference, fees, taxes)
- Description and notes

**Indexes:**
- `transaction_id` (unique)
- `transaction_date`
- `transaction_type`
- `related_trade_id`
- Composite: (transaction_date, transaction_type)

**Example:**
```python
from src.database.models import AccountHistory
from datetime import datetime

txn = AccountHistory(
    transaction_id="TXN_20260115_001",
    transaction_date=datetime.now(),
    transaction_type="trade_profit",
    amount=5000.0,
    balance_before=100000.0,
    balance_after=105000.0,
    # ... more fields
)
```

---

## 🔧 Database Initialization

### Using init_db.py script:

```bash
# Initialize database (create tables)
python init_db.py

# Reset database (drop and recreate)
python init_db.py --reset

# Show database info
python init_db.py --info

# Test connection
python init_db.py --test-connection

# Show schema details
python init_db.py --schema
```

### Using Python code:

```python
from src.database import init_database, check_database_connection

# Test connection
if check_database_connection():
    # Initialize database
    init_database()
```

---

## 💾 Database Configuration

Configuration is in `.env` file:

```bash
# Database Type
DB_TYPE=sqlite  # or postgresql
DB_ENABLED=True

# SQLite Configuration
DB_PATH=data/angel_x.db

# PostgreSQL Configuration (if using PostgreSQL)
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_NAME=angel_x
DATABASE_USER=angel_x_user
DATABASE_PASSWORD=your_password

# Connection Pool (PostgreSQL only)
DATABASE_POOL_SIZE=5
DATABASE_MAX_OVERFLOW=10
DATABASE_POOL_RECYCLE=3600

# Debug
DATABASE_ECHO=False  # Set True to see SQL queries
```

---

## 📊 Usage Examples

### Create a Trade

```python
from src.database import get_db_session
from src.database.models import Trade
from datetime import datetime

with get_db_session() as session:
    trade = Trade(
        trade_id="NIFTY_CE_24000_20260115_001",
        status="open",
        symbol="NIFTY",
        exchange="NFO",
        option_type="call",
        strike_price=24000,
        expiry_date=datetime(2026, 1, 15),
        lot_size=50,
        entry_time=datetime.now(),
        entry_direction="buy",
        entry_price=150.50,
        entry_quantity=50,
        entry_delta=0.5,
        entry_gamma=0.05,
        strategy_name="Delta Neutral",
        is_paper_trade=True,
    )
    session.add(trade)
    # Auto-commits on context exit
```

### Query Trades

```python
from src.database import get_session
from src.database.models import Trade

session = get_session()

# Get all open trades
open_trades = session.query(Trade).filter(
    Trade.status == "open"
).all()

# Get trades for today
from datetime import date
today_trades = session.query(Trade).filter(
    Trade.entry_time >= datetime.combine(date.today(), datetime.min.time())
).all()

# Get trades by strategy
strategy_trades = session.query(Trade).filter(
    Trade.strategy_name == "Delta Neutral"
).all()

session.close()
```

### Save Performance Metrics

```python
from src.database import get_db_session
from src.database.models import Performance
from datetime import date

with get_db_session() as session:
    perf = Performance(
        period="daily",
        period_date=date.today(),
        total_trades=10,
        winning_trades=7,
        losing_trades=3,
        gross_pnl=6000.0,
        brokerage_total=500.0,
        taxes_total=500.0,
        net_pnl=5000.0,
        win_rate=70.0,
        avg_win=1200.0,
        avg_loss=-800.0,
        starting_capital=100000.0,
        ending_capital=105000.0,
    )
    session.add(perf)
```

### Store Market Data

```python
from src.database import get_db_session
from src.database.models import MarketData
from datetime import datetime

with get_db_session() as session:
    data = MarketData(
        symbol="NIFTY",
        exchange="NSE",
        timestamp=datetime.now(),
        interval="1min",
        open_price=24000.0,
        high_price=24050.0,
        low_price=23980.0,
        close_price=24025.0,
        volume=1000,
    )
    session.add(data)
```

### Track Account History

```python
from src.database import get_db_session
from src.database.models import AccountHistory
from datetime import datetime

with get_db_session() as session:
    txn = AccountHistory(
        transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        transaction_date=datetime.now(),
        transaction_type="trade_profit",
        amount=5000.0,
        balance_before=100000.0,
        balance_after=105000.0,
        available_balance=105000.0,
        related_trade_id="NIFTY_CE_24000_20260115_001",
        description="Profit from NIFTY 24000 CE trade",
    )
    session.add(txn)
```

---

## 🔍 Query Examples

### Get Today's P&L

```python
from src.database import get_session
from src.database.models import Trade
from datetime import date, datetime
from sqlalchemy import func

session = get_session()

today_start = datetime.combine(date.today(), datetime.min.time())
pnl = session.query(func.sum(Trade.net_pnl)).filter(
    Trade.entry_time >= today_start,
    Trade.status == "closed"
).scalar()

print(f"Today's P&L: ₹{pnl or 0:.2f}")
session.close()
```

### Get Win Rate

```python
from src.database import get_session
from src.database.models import Trade
from sqlalchemy import func

session = get_session()

total = session.query(func.count(Trade.id)).filter(
    Trade.status == "closed"
).scalar()

winners = session.query(func.count(Trade.id)).filter(
    Trade.status == "closed",
    Trade.net_pnl > 0
).scalar()

win_rate = (winners / total * 100) if total > 0 else 0
print(f"Win Rate: {win_rate:.1f}%")

session.close()
```

### Get Best and Worst Trades

```python
from src.database import get_session
from src.database.models import Trade
from sqlalchemy import desc

session = get_session()

# Best trade
best = session.query(Trade).filter(
    Trade.status == "closed"
).order_by(desc(Trade.net_pnl)).first()

# Worst trade
worst = session.query(Trade).filter(
    Trade.status == "closed"
).order_by(Trade.net_pnl).first()

if best:
    print(f"Best Trade: {best.trade_id} - ₹{best.net_pnl:.2f}")
if worst:
    print(f"Worst Trade: {worst.trade_id} - ₹{worst.net_pnl:.2f}")

session.close()
```

---

## 🔧 Migrations

For schema changes, you can:

1. **Drop and recreate (development only):**
```bash
python init_db.py --reset
```

2. **Use Alembic (recommended for production):**
```bash
# Install Alembic
pip install alembic

# Initialize
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add new column"

# Apply migration
alembic upgrade head
```

---

## 📈 Performance Tips

1. **Use indexes:** All models have appropriate indexes
2. **Batch inserts:** Use `session.bulk_insert_mappings()` for multiple records
3. **Connection pooling:** Configured for PostgreSQL
4. **Eager loading:** Use `.options(joinedload())` for relationships
5. **Query optimization:** Use `.filter()` instead of Python filtering

---

## 🔒 Security

1. **Never commit `.env`** with real credentials
2. **Use environment variables** for production
3. **Enable SSL** for PostgreSQL in production
4. **Limit database user permissions** to only what's needed
5. **Regular backups:** Automated backup strategy recommended

---

## 📊 Database Size Estimates

Approximate storage per record:

- Trade: ~500 bytes
- Performance: ~300 bytes
- MarketData: ~200 bytes
- AccountHistory: ~300 bytes

**Example:** 
- 1000 trades/month = ~500 KB/month
- 1 year = ~6 MB
- 10 years = ~60 MB

Very manageable for SQLite, trivial for PostgreSQL.

---

## 🎯 Next Steps

1. Initialize database: `python init_db.py`
2. Test connection: `python init_db.py --test-connection`
3. Start trading: `python main.py`
4. View schema: `python init_db.py --schema`

---

**Status:** ✅ Production Ready  
**Last Updated:** January 15, 2026  
**Version:** 1.0
