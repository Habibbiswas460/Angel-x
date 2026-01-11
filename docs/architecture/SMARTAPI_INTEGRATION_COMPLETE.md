# SmartAPI Integration Complete

## 📦 Angel One SmartAPI পূর্ণাঙ্গ Integration

### ✅ সম্পন্ন কাজ:

#### 1. **SmartAPI SDK Installation**
```bash
pip install smartapi-python==1.3.0
pip install pyotp websocket-client
```

#### 2. **Full Authentication Implementation** (`smartapi_integration.py`)
- ✅ TOTP-based 2FA authentication
- ✅ Session management (auth_token, refresh_token, feed_token)
- ✅ Auto re-login on token expiry
- ✅ Profile fetching
- ✅ Secure logout

```python
from src.integrations.angelone.smartapi_integration import SmartAPIClient

client = SmartAPIClient(api_key, client_code, password, totp_secret)
client.login()  # Real authentication with AngelOne
```

#### 3. **Market Data Integration**
- ✅ Real-time LTP (Last Traded Price) fetching
- ✅ Instrument search by symbol
- ✅ Market status validation
- ✅ Option chain data (ATM ±5 strikes)

```python
# Get LTP
ltp_data = client.get_ltp_data('NFO', 'NIFTY08JAN24000CE', 'token')

# Search instruments
instruments = client.search_scrip('NFO', 'NIFTY')
```

#### 4. **Order Management**
- ✅ Place Order (MARKET, LIMIT, STOPLOSS_LIMIT)
- ✅ Modify Order (price, quantity, trigger)
- ✅ Cancel Order
- ✅ Get Order Book
- ✅ Get Positions
- ✅ Get RMS Limits (funds/margin)

```python
# Place order
order = client.place_order(
    tradingsymbol='NIFTY08JAN24000CE',
    symboltoken='token',
    exchange='NFO',
    transactiontype='BUY',
    ordertype='MARKET',
    quantity=1
)

# Cancel order
client.cancel_order(orderid='12345', variety='NORMAL')
```

#### 5. **Updated AngelOneAdapter**
- ✅ Real SmartAPI client initialization
- ✅ Paper trading mode + Live trading mode
- ✅ Automatic fallback to simulation if credentials missing
- ✅ Market safety gates
- ✅ Symbol validation for NIFTY/BANKNIFTY options

```python
from src.integrations.angelone.angelone_adapter import AngelOneAdapter

adapter = AngelOneAdapter()
adapter.login()  # Uses real SmartAPI if credentials available

# Get option chain
chain = adapter.get_option_chain('NIFTY', spot=20000, strikes_range=5)

# Place order
order = adapter.place_order({
    'symbol': 'NIFTY08JAN24000CE',
    'qty': 1,
    'side': 'BUY',
    'type': 'MARKET'
})
```

#### 6. **Comprehensive Test Suite** (`test_smartapi_integration.py`)
- ✅ Test 1: Authentication
- ✅ Test 2: Market status checks
- ✅ Test 3: Symbol resolution & option chain
- ✅ Test 4: Order placement (paper mode)
- ✅ Test 5: Direct SmartAPI client test

```bash
# Run tests
./run_smartapi_test.sh
# or
python3 scripts/test_smartapi_integration.py
```

### 🔧 Configuration

#### Environment Variables (.env):
```bash
# AngelOne Credentials
ANGELONE_API_KEY=your_api_key_here
ANGELONE_CLIENT_CODE=your_client_code
ANGELONE_PASSWORD=your_password
ANGELONE_TOTP_SECRET=your_totp_secret

# Trading Mode
PAPER_TRADING=True  # False for live trading
```

#### Config File (config/config.py):
```python
# Market timing
MARKET_START_TIME = '09:15'
MARKET_END_TIME = '15:30'
SQUARE_OFF_TIME = '15:15'

# Option parameters
STRIKE_STEP = 50  # NIFTY strike step
```

### 📊 Architecture

```
src/integrations/angelone/
├── smartapi_integration.py    # Core SmartAPI SDK wrapper
├── angelone_adapter.py         # High-level adapter with safety gates
├── angelone_client.py          # Legacy client (fallback)
└── angelone_client.py          # AngelOne client integration
```

### 🚀 Usage Examples

#### Example 1: Real Authentication
```python
import os
from src.integrations.angelone.smartapi_integration import SmartAPIClient

client = SmartAPIClient(
    api_key=os.getenv('ANGELONE_API_KEY'),
    client_code=os.getenv('ANGELONE_CLIENT_CODE'),
    password=os.getenv('ANGELONE_PASSWORD'),
    totp_secret=os.getenv('ANGELONE_TOTP_SECRET')
)

if client.login():
    print("✓ Logged in successfully")
    
    # Get profile
    profile = client.get_profile()
    print(f"User: {profile['data']['name']}")
    
    # Get RMS limits
    rms = client.get_rms_limits()
    print(f"Available: ₹{rms['availablecash']}")
    
    client.logout()
```

#### Example 2: Market Data
```python
from src.integrations.angelone.angelone_adapter import AngelOneAdapter

adapter = AngelOneAdapter()
adapter.login()

# Check market status
if adapter.is_market_open():
    # Get option chain
    chain = adapter.get_option_chain('NIFTY', spot=20000)
    
    for strike, data in chain['strikes'].items():
        print(f"{strike}: CE={data['CE']['ltp']}, PE={data['PE']['ltp']}")
```

#### Example 3: Order Placement (Paper Trading)
```python
adapter = AngelOneAdapter()  # PAPER_TRADING=True
adapter.login()

# Build option symbol
expiry = adapter.get_nearest_weekly_expiry()
atm = adapter.calc_atm_strike(20000, 50)
symbol = adapter.build_option_symbol('NIFTY', expiry, atm, 'CE')

# Place order
result = adapter.place_order({
    'symbol': symbol,
    'qty': 1,
    'side': 'BUY',
    'price': 100,
    'type': 'MARKET'
})

print(f"Order ID: {result['orderid']}")
```

### ⚠️ Safety Features

1. **Market Safety Gates**
   - Market timing validation (9:15 AM - 3:30 PM)
   - Weekend/holiday detection
   - Authentication check before every trade

2. **Symbol Validation**
   - NIFTY/BANKNIFTY prefix check
   - Expiry format validation
   - CE/PE suffix validation

3. **Paper Trading Mode**
   - Safe testing without real orders
   - Simulated order responses
   - No broker API calls

4. **Error Handling**
   - SmartAPIException catching
   - Automatic retry on network errors
   - Detailed logging

### 📝 Testing

```bash
# Paper trading test (safe)
export PAPER_TRADING=True
python3 scripts/test_smartapi_integration.py

# Live trading test (requires credentials)
export PAPER_TRADING=False
export ANGELONE_API_KEY=...
export ANGELONE_CLIENT_CODE=...
export ANGELONE_PASSWORD=...
export ANGELONE_TOTP_SECRET=...
python3 scripts/test_smartapi_integration.py
```

### 🔗 Integration with Existing System

#### Risk Manager Integration:
```python
from src.core.risk_manager import RiskManager
from src.integrations.angelone.angelone_adapter import AngelOneAdapter

adapter = AngelOneAdapter()
risk_manager = RiskManager()

# Check if can take trade
if risk_manager.can_take_trade(trade_info):
    # Place order through adapter
    result = adapter.place_order(order_payload)
```

#### Adaptive Learning Integration:
```python
from src.engines.adaptive_controller import AdaptiveController
from src.integrations.angelone.angelone_adapter import AngelOneAdapter

adapter = AngelOneAdapter()
adaptive = AdaptiveController()

# Pre-entry decision
decision = adaptive.should_enter_trade(market_conditions, patterns)

if decision['enter']:
    # Execute through adapter
    result = adapter.place_order(decision['order_params'])
    
    # Record outcome for learning
    adaptive.record_trade_outcome({
        'orderid': result['orderid'],
        'success': result['status'] == 'success'
    })
```

### 📦 Dependencies Updated

```txt
# requirements.txt
smartapi-python==1.3.0    # AngelOne SmartAPI SDK
pyotp>=2.8.0              # TOTP 2FA
websocket-client>=1.6.0   # WebSocket for live data
requests>=2.31.0          # HTTP client
```

### ✅ Next Steps

1. **Instrument Master Download**: Fetch NSE/NFO instrument tokens
2. **WebSocket Integration**: Real-time market data streaming
3. **Historical Data**: OHLC data for backtesting
4. **GTT Orders**: Good Till Triggered order support
5. **Position Tracking**: Real-time P&L monitoring

---

## 🎯 Summary

✅ **SmartAPI পূর্ণাঙ্গ integration সম্পন্ন**
- Real authentication with TOTP
- Market data fetching (LTP, option chain)
- Order management (place, modify, cancel)
- Paper trading mode for safe testing
- Comprehensive error handling
- Full test suite

**Status**: Production-ready with paper trading fallback! 🚀
