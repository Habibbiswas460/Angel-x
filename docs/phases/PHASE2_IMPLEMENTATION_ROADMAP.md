# 🔮 PHASE 1 TO PHASE 2 ROADMAP

**How to implement real AngelOne integration in Phase 2**

---

## 📋 Phase 1 Complete ✅

The adapter scaffolding and smoke tests are ready. Phase 2 requires implementing actual API calls.

---

## 🔧 Phase 2: Real AngelOne Integration

### Step 1: Install AngelOne SDK

```bash
# Install SmartAPI (Angel One's Python SDK)
pip install smartapi

# Also install TOTP library
pip install pyotp

# Update requirements.txt
smartapi>=1.3.0
pyotp>=2.8.0
```

### Step 2: Implement login() in AngelOneAdapter

**File:** `src/utils/angelone_adapter.py`

```python
def login(self) -> bool:
    """Implement real AngelOne REST login."""
    with self._lock:
        try:
            if not self.api_key or not self.client_code:
                logger.warning("No credentials — simulated mode")
                self._token = f"SIM_{int(time.time())}"
                self._token_expires_at = time.time() + 3600
                return True
            
            # Generate TOTP code
            totp_code = self._generate_totp_code()
            
            # REST login call
            import requests
            
            login_payload = {
                'apikey': self.api_key,
                'clientcode': self.client_code,
                'password': self.password,
                'totp': totp_code
            }
            
            # TODO: Replace with actual AngelOne endpoint
            endpoint = "https://api.angelone.in/v1/auth/login"
            
            response = requests.post(endpoint, json=login_payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == 'success':
                self._token = data['data']['token']
                self._session_id = data['data']['sessionID']
                self._token_expires_at = time.time() + 86400  # 24 hours
                logger.info(f"Login successful: {self.client_code}")
                return True
            else:
                logger.error(f"Login failed: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def _generate_totp_code(self) -> str:
        """Generate TOTP code from secret."""
        try:
            import pyotp
            totp = pyotp.TOTP(self.totp_secret)
            return totp.now()
        except Exception as e:
            logger.error(f"TOTP generation failed: {e}")
            return "000000"
```

### Step 3: Implement get_ltp() for real data

```python
def get_ltp(self, symbol: str) -> Dict:
    """Get real LTP from broker."""
    try:
        if not self.is_authenticated():
            return {'status': 'error', 'reason': 'Not authenticated'}
        
        # If using SmartAPI SDK
        if self._smartapi_client:
            quote = self._smartapi_client.ltpData(
                mode='LTP',
                exchangeTokens={'NFO': [self._symbol_to_token(symbol)]}
            )
            return {
                'symbol': symbol,
                'ltp': quote['ltp'],
                'bid': quote['bid'],
                'ask': quote['ask'],
                'volume': quote['volume'],
                'oi': quote['oi']
            }
        
        # Fallback: REST API call
        endpoint = f"https://api.angelone.in/v1/quote/ltp"
        headers = {'Authorization': f'Bearer {self._token}'}
        
        response = requests.get(
            endpoint,
            params={'symbol': symbol},
            headers=headers,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
        
    except Exception as e:
        logger.error(f"get_ltp({symbol}): {e}")
        return {'status': 'error', 'reason': str(e)}

def _symbol_to_token(self, symbol: str) -> str:
    """Convert symbol to broker token."""
    # Example: NIFTY08JAN2620000CE → token
    # Requires symbol registry or broker lookup
    pass
```

### Step 4: Implement place_order() with retry

```python
def place_order(self, order_payload: Dict) -> Dict:
    """Place real order with retry logic."""
    try:
        logger.info(f"Placing order: {order_payload}")
        
        # Validate
        if not self.is_authenticated():
            if not self.login():
                return {'status': 'failed', 'reason': 'Authentication failed'}
        
        symbol = order_payload.get('symbol')
        if not self.validate_symbol(symbol):
            return {'status': 'failed', 'reason': 'Invalid symbol'}
        
        # Skip market check in PAPER mode
        if not self.paper_trading:
            is_safe, reason = self.validate_market_conditions()
            if not is_safe:
                return {'status': 'failed', 'reason': reason}
        
        # Build broker-specific order
        broker_order = {
            'variety': 'regular',
            'tradingsymbol': symbol,
            'symboltoken': self._symbol_to_token(symbol),
            'transactiontype': 'BUY' if order_payload['side'] == 'BUY' else 'SELL',
            'exchange': 'NFO',
            'ordertype': order_payload['type'],  # MARKET, LIMIT
            'producttype': 'MIS',
            'price': order_payload.get('price', 0),
            'quantity': order_payload['qty'],
            'pricetype': 'LTP' if order_payload['type'] == 'MARKET' else 'LIMIT'
        }
        
        # REST API call with retry
        max_retries = 3
        for attempt in range(max_retries):
            try:
                endpoint = "https://api.angelone.in/v1/order/place"
                headers = {'Authorization': f'Bearer {self._token}'}
                
                response = requests.post(
                    endpoint,
                    json=broker_order,
                    headers=headers,
                    timeout=10
                )
                response.raise_for_status()
                
                data = response.json()
                if data.get('status') == 'success':
                    order_id = data['data']['orderid']
                    logger.info(f"Order placed: {order_id}")
                    return {
                        'status': 'success',
                        'orderid': order_id,
                        'message': 'Order placed successfully'
                    }
                else:
                    logger.error(f"Order placement failed: {data.get('message')}")
                    return {'status': 'failed', 'reason': data.get('message')}
                    
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    logger.warning(f"Timeout, retrying ({attempt+1}/{max_retries})")
                    time.sleep(1)
                    continue
                else:
                    return {'status': 'error', 'reason': 'Request timeout'}
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error, retrying ({attempt+1}/{max_retries}): {e}")
                    time.sleep(1)
                    continue
                else:
                    return {'status': 'error', 'reason': str(e)}
        
        return {'status': 'error', 'reason': 'Max retries exceeded'}
        
    except Exception as e:
        logger.error(f"place_order error: {e}")
        return {'status': 'error', 'reason': str(e)}
```

### Step 5: Implement WebSocket for streaming

```python
import websocket
import json
import threading

def connect_ws(self) -> bool:
    """Connect to broker WebSocket for streaming quotes."""
    try:
        if not self.is_authenticated():
            logger.error("Cannot connect WS: not authenticated")
            return False
        
        # WebSocket URL and parameters
        ws_params = {
            'token': self._token,
            'user': self.client_code,
            'session': self._session_id
        }
        
        url = f"{self.ws_url}?{urlencode(ws_params)}"
        
        # Start WS thread
        self._ws_thread = threading.Thread(
            target=self._ws_loop,
            args=(url,),
            daemon=True
        )
        self._ws_thread.start()
        
        logger.info("WebSocket connect initiated")
        return True
        
    except Exception as e:
        logger.error(f"connect_ws error: {e}")
        return False

def _ws_loop(self, url):
    """WebSocket read loop."""
    try:
        def on_message(ws, message):
            try:
                data = json.loads(message)
                # Process incoming tick data
                self._on_tick(data)
            except Exception as e:
                logger.error(f"WS message parse error: {e}")
        
        def on_error(ws, error):
            logger.error(f"WS error: {error}")
            # Reconnect logic
            time.sleep(5)
            self.connect_ws()
        
        def on_close(ws, *args):
            logger.warning("WS closed, will reconnect")
            time.sleep(5)
            self.connect_ws()
        
        def on_open(ws):
            logger.info("WS connected")
        
        ws = websocket.WebSocketApp(
            url,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            on_open=on_open
        )
        
        ws.run_forever()
        
    except Exception as e:
        logger.error(f"WS loop error: {e}")

def _on_tick(self, tick_data):
    """Handle incoming tick data."""
    symbol = tick_data.get('symbol')
    ltp = tick_data.get('ltp')
    
    logger.debug(f"Tick: {symbol} @ {ltp}")
    
    # Store for later retrieval
    # self._last_ticks[symbol] = tick_data
```

### Step 6: Implement cancel_order()

```python
def cancel_order(self, order_id: str) -> Dict:
    """Cancel real order."""
    try:
        if not self.is_authenticated():
            return {'status': 'failed', 'reason': 'Not authenticated'}
        
        endpoint = f"https://api.angelone.in/v1/order/cancel"
        headers = {'Authorization': f'Bearer {self._token}'}
        
        payload = {
            'orderid': order_id,
            'variety': 'regular'
        }
        
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('status') == 'success':
            logger.info(f"Order cancelled: {order_id}")
            return {'status': 'success', 'orderid': order_id}
        else:
            logger.error(f"Cancel failed: {data.get('message')}")
            return {'status': 'failed', 'reason': data.get('message')}
            
    except Exception as e:
        logger.error(f"cancel_order({order_id}): {e}")
        return {'status': 'error', 'reason': str(e)}
```

---

## 📊 Implementation Checklist

- [ ] Install smartapi + pyotp
- [ ] Implement `login()` with real REST call
- [ ] Implement `_generate_totp_code()`
- [ ] Implement `get_ltp()` for streaming
- [ ] Implement `place_order()` with retry
- [ ] Implement `cancel_order()`
- [ ] Implement `modify_order()`
- [ ] Implement `get_order_status()`
- [ ] Implement WebSocket connect/subscribe
- [ ] Test with demo account
- [ ] Test with real account (small positions)

---

## 🧪 Phase 2 Testing Plan

### 1. Unit Tests
```bash
# Test each method independently
python3 -m pytest tests/test_angelone_adapter.py -v
```

### 2. Integration Tests
```bash
# Test with real broker (demo account)
PYTHONPATH=. python3 scripts/phase2_integration_test.py
```

### 3. Live Trading Validation
```bash
# Small position test on real account
PYTHONPATH=. python3 scripts/live_validation.py
```

---

## ⚠️ Important Notes

### Security
- Never commit real credentials to git
- Use `.env` file (in `.gitignore`)
- Encrypt credentials in production
- Use environment variables for CI/CD

### Error Handling
- All API calls should have retry logic
- Network timeouts are common
- Graceful degradation to paper mode
- Comprehensive logging for debugging

### Testing
- Always test on demo account first
- Start with small position sizes
- Monitor logs carefully
- Have kill-switch ready

### Production Readiness
- [ ] All unit tests pass
- [ ] Integration tests pass
- [ ] Demo account validation complete
- [ ] Real account testing (small positions)
- [ ] Monitoring + alerting set up
- [ ] Kill-switch + circuit breaker tested

---

## 📞 Reference

- **AngelOne Docs:** https://www.angelone.in/api
- **SmartAPI GitHub:** https://github.com/shoonya/SmartApi
- **TOTP Library:** https://github.com/pyauth/pyotp

---

**Ready for Phase 2? Follow the implementation plan above and test thoroughly!**
