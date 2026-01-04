# 🔗 PHASE 1: INTEGRATION GUIDE

**How to integrate AngelOneAdapter with ANGEL-X strategy**

---

## ✅ Current Status

- ✅ `AngelOneAdapter` fully implemented (`src/utils/angelone_adapter.py`)
- ✅ All Phase 1 features working (auth, symbols, chain, orders, errors)
- ✅ PAPER_TRADING safe by default
- ✅ Smoke test passing all 5 exit conditions
- ⏳ Ready to integrate into `data_feed.py` and `order_manager.py`

---

## 📂 Integration Points

### 1. Data Feed Integration
**File:** `src/utils/data_feed.py`

Current state: Already adapter-aware (DATA_SOURCE check)

```python
# Line ~30-50 (add if not present)
from src.utils.angelone_adapter import AngelOneAdapter

class DataFeed:
    def __init__(self, config):
        self.config = config
        
        # Use adapter if broker mode
        if getattr(config, 'DATA_SOURCE', 'broker') == 'broker':
            self.adapter = AngelOneAdapter()
        else:
            self.adapter = None
    
    def connect(self):
        """Connect using adapter"""
        if self.adapter:
            return self.adapter.login()
        return False
    
    def get_ltp(self, symbol):
        """Get LTP using adapter"""
        if self.adapter:
            # TODO: Call broker LTP API via adapter
            pass
    
    def get_option_chain(self, underlying, spot=None):
        """Get option chain using adapter"""
        if self.adapter:
            return self.adapter.get_option_chain(underlying, spot)
        return {}
```

### 2. Order Manager Integration
**File:** `src/core/order_manager.py`

Current state: Already adapter-aware (place_order, cancel_order)

```python
# Line ~30-50 (add if not present)
from src.utils.angelone_adapter import AngelOneAdapter

class OrderManager:
    def __init__(self, config):
        self.config = config
        
        # Use adapter if broker mode
        if getattr(config, 'DATA_SOURCE', 'broker') == 'broker':
            self.adapter = AngelOneAdapter()
        else:
            self.adapter = None
    
    def place_order(self, order_payload):
        """Place order using adapter"""
        if self.adapter:
            return self.adapter.place_order(order_payload)
        # Fallback to paper simulation
        return self._simulate_response(order_payload)
    
    def cancel_order(self, order_id):
        """Cancel order using adapter"""
        if self.adapter:
            return self.adapter.cancel_order(order_id)
        return {'status': 'success'}
    
    def get_order_status(self, order_id):
        """Get order status"""
        if self.adapter:
            return self.adapter.get_order_status(order_id)
        return {'status': 'filled'}
```

### 3. Strategy Integration
**File:** `src/core/trade_manager.py` (or similar)

```python
# Example: Using adapter in strategy logic
from src.utils.angelone_adapter import AngelOneAdapter

class TradeManager:
    def __init__(self, config):
        self.adapter = AngelOneAdapter()
        self.adapter.login()
        self.adapter.start_auto_refresh()
    
    def find_tradeable_strikes(self, underlying='NIFTY', spot=20000):
        """Find ATM ±5 strikes"""
        chain = self.adapter.get_option_chain(underlying, spot, strikes_range=5)
        
        tradeable = []
        for strike, data in chain['strikes'].items():
            ce_sym = data['CE']['symbol']
            pe_sym = data['PE']['symbol']
            
            # Validate symbols
            if self.adapter.validate_symbol(ce_sym) and self.adapter.validate_symbol(pe_sym):
                tradeable.append({
                    'strike': strike,
                    'ce': ce_sym,
                    'pe': pe_sym,
                    'ce_ltp': data['CE']['ltp'],
                    'pe_ltp': data['PE']['ltp']
                })
        
        return tradeable
    
    def execute_trade(self, symbol, qty, side, price=None):
        """Execute trade using adapter"""
        # Validate market
        is_safe, reason = self.adapter.validate_market_conditions()
        if not is_safe:
            logger.warning(f"Cannot trade: {reason}")
            return None
        
        # Build order
        order_payload = {
            'symbol': symbol,
            'qty': qty,
            'side': side,
            'price': price or 0,
            'type': 'LIMIT' if price else 'MARKET',
            'exchange': 'NFO'
        }
        
        # Place via adapter
        resp = self.adapter.place_order(order_payload)
        
        if resp['status'] == 'success':
            order_id = resp['orderid']
            logger.info(f"Order placed: {order_id}")
            return order_id
        else:
            logger.error(f"Order failed: {resp.get('reason')}")
            return None
```

---

## 🚀 Quick Start (PAPER TRADING)

### 1. Setup Environment

```bash
# Copy example env
cp .example.env .env

# Edit .env (NO real credentials needed for PAPER_TRADING)
PAPER_TRADING=true
DATA_SOURCE=broker
ANGELONE_API_KEY=test
ANGELONE_CLIENT_CODE=test
```

### 2. Run Smoke Test

```bash
cd /home/lora/git_clone_projects/OA
PYTHONPATH=. python3 scripts/adapter_smoke.py
```

**Expected Output:**
```
╔══════════════════════════════════════════════════════════════════╗
║  PHASE 1 EXIT CONDITIONS - ALL TESTS PASSED ✓                    ║
╠══════════════════════════════════════════════════════════════════╣
║  ✅ Bot auto login करते पारे                                     ║
║  ✅ NIFTY option symbol auto resolve हो                         ║
║  ✅ Option chain data आसे                                        ║
║  ✅ Dummy order place + cancel test OK                          ║
║  ✅ Error में bot crash ना करे                                  ║
╚══════════════════════════════════════════════════════════════════╝
```

### 3. Use in Code

```python
from src.utils.angelone_adapter import AngelOneAdapter

adapter = AngelOneAdapter()
adapter.login()  # Simulated in PAPER mode

# Get option chain
chain = adapter.get_option_chain('NIFTY', spot=20000, strikes_range=5)
print(f"Strikes: {list(chain['strikes'].keys())}")

# Place order
order = {
    'symbol': 'NIFTY08JAN2620000CE',
    'qty': 75,
    'side': 'BUY',
    'price': 100.0,
    'type': 'LIMIT'
}
resp = adapter.place_order(order)
print(f"Order ID: {resp['orderid']}")

# Cancel order
cancel = adapter.cancel_order(resp['orderid'])
print(f"Cancel: {cancel['status']}")
```

---

## 🔐 Live Trading Setup (Phase 2)

### 1. Get Angel One Credentials

1. **API Key**: SmartAPI → Settings → API
2. **Client Code**: Your trading account code
3. **Password**: Account password (encrypted)
4. **TOTP Secret**: Two-factor setup → Settings

### 2. Configure .env

```bash
# Real credentials (KEEP SECRET - use vault in production)
ANGELONE_API_KEY=your_real_api_key
ANGELONE_CLIENT_CODE=your_real_client_code
ANGELONE_PASSWORD=your_encrypted_password
ANGELONE_TOTP_SECRET=your_totp_secret

# Set live mode
PAPER_TRADING=false
DATA_SOURCE=broker
```

### 3. Install SDK

```bash
# Install SmartAPI (when available)
pip install smartapi

# Or use HTTP client (requests already in requirements.txt)
```

### 4. Implement Real Methods

In `src/utils/angelone_adapter.py`:

```python
# TODO: Implement these in Phase 2
def login(self) -> bool:
    """Real REST login with credentials + TOTP"""
    # POST /auth/login
    # Extract token from response
    # Set self._token and self._token_expires_at
    pass

def _generate_totp_code(self) -> str:
    """Generate TOTP code from secret"""
    import pyotp
    totp = pyotp.TOTP(self.totp_secret)
    return totp.now()

# Similar for: get_ltp, place_order, cancel_order, etc.
```

### 5. Validate Before Going Live

```bash
# Run full smoke test on demo account
PYTHONPATH=. python3 scripts/adapter_smoke.py

# Expected: All tests pass with real broker responses
```

---

## 📊 Configuration Reference

### Environment Variables

```bash
# Authentication
ANGELONE_API_KEY              # SmartAPI key
ANGELONE_CLIENT_CODE          # Trading account code
ANGELONE_PASSWORD             # Account password
ANGELONE_TOTP_SECRET          # Google Authenticator secret

# Broker URLs
BROKER_WS_URL                 # WebSocket endpoint (Phase 2)
BROKER_API_KEY                # Broker API key (if needed)

# Modes
PAPER_TRADING=true/false      # Paper (true) vs Live (false)
DATA_SOURCE=broker            # Use broker adapter
WEBSOCKET_ENABLED=true/false  # WebSocket (Phase 2)

# Trading Hours
MARKET_START_TIME=09:15
MARKET_END_TIME=15:30
SQUARE_OFF_TIME=15:15

# Logging
LOG_LEVEL=INFO|DEBUG|WARNING|ERROR
```

### Python Config (config/config.py)

```python
# Defaults (can be overridden by .env)
PRIMARY_UNDERLYING = "NIFTY"
ALLOWED_STRIKES_RANGE = 5     # ATM ±5
STRIKE_STEP = 50              # Strike spacing
PAPER_TRADING = True          # Safe default
DATA_SOURCE = "broker"
MARKET_START_TIME = "09:15"
MARKET_END_TIME = "15:30"
SQUARE_OFF_TIME = "15:15"
```

---

## 🧪 Testing Checklist

### Before Going Live

- [ ] Smoke test passes (PAPER_TRADING=true)
- [ ] Market check working (NSE hours validation)
- [ ] Symbol generation correct (validate format)
- [ ] Option chain returns ATM ±5 strikes
- [ ] Order placement works (simulated)
- [ ] Order cancellation works (simulated)
- [ ] No crashes on error conditions
- [ ] Logging shows all actions
- [ ] Auto-refresh thread running
- [ ] Token expiry handled correctly

### With Real Credentials (Demo)

- [ ] Login succeeds with API key + TOTP
- [ ] Real token received + stored
- [ ] Market check works (live status)
- [ ] Real option chain fetched
- [ ] Symbols match broker format
- [ ] Dummy order placed (demo account)
- [ ] Order status retrieved
- [ ] Order cancelled successfully
- [ ] No errors with real data
- [ ] Session survives token refresh

---

## 🐛 Troubleshooting

### Issue: "Market is closed"
**Cause:** Running outside 09:15-15:30 IST or weekend
**Fix:** Test in paper mode or adjust MARKET_START_TIME for testing

### Issue: "Invalid symbol"
**Cause:** Underlying not in INSTRUMENT_DB
**Fix:** Add to INSTRUMENT_DB in adapter or verify underlying name

### Issue: Token not refreshing
**Cause:** Auto-refresh thread didn't start
**Fix:** Call `adapter.start_auto_refresh()` after login

### Issue: PAPER_TRADING orders failing
**Cause:** Market closed check enabled for paper orders
**Fix:** Ensure `PAPER_TRADING=true` in config

### Issue: Import error for AngelOneAdapter
**Cause:** PYTHONPATH not set or file in wrong location
**Fix:** Set `PYTHONPATH=.` before running

---

## 📚 Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `src/utils/angelone_adapter.py` | Main adapter | ✅ Complete |
| `scripts/adapter_smoke.py` | Smoke test | ✅ Complete |
| `.example.env` | Env template | ✅ Complete |
| `config/config.py` | Python config | ✅ Updated |
| `src/utils/data_feed.py` | Adapter-ready | ⏳ Ready |
| `src/core/order_manager.py` | Adapter-ready | ⏳ Ready |

---

## 🎯 Next Milestones

- **Phase 2:** Implement real AngelOne SDK auth + WebSocket
- **Phase 3:** Greeks calculation + OI analysis
- **Phase 4:** Full strategy integration + live trading validation
- **Phase 5:** Performance optimization + advanced features

---

*For questions or issues, see [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md)*
