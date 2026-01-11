"""Phase 2: Real AngelOne SmartAPI Integration

Implements actual broker connectivity:
- REST authentication with TOTP
- Token refresh with expiry handling
- Real market data via API
- Order placement & management
- WebSocket streaming (optional)
"""
import os
import time
import requests
import json
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent.parent / '.env'
load_dotenv(env_path)

from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)

try:
    import pyotp
except ImportError:
    pyotp = None
    logger.warning("pyotp not installed — TOTP generation disabled")

# Try to import SmartAPI SDK
try:
    from SmartApi import SmartConnect
except ImportError:
    SmartConnect = None
    logger.warning("SmartAPI SDK not installed — using HTTP fallback")


class AngelOnePhase2:
    """Phase 2: Real AngelOne broker integration via SmartAPI SDK."""
    
    # API endpoints
    API_BASE = "https://api.angelone.in"
    AUTH_ENDPOINT = "/rest/secure/angelbroking/user/v1/loginWithOTP"
    LTP_ENDPOINT = "/rest/secure/angelbroking/market/v1/quote/"
    PLACE_ORDER_ENDPOINT = "/rest/secure/angelbroking/order/v1/placeOrder"
    CANCEL_ORDER_ENDPOINT = "/rest/secure/angelbroking/order/v1/cancelOrder"
    ORDER_STATUS_ENDPOINT = "/rest/secure/angelbroking/order/v1/details"
    
    # Instrument registry (will be populated from broker)
    INSTRUMENT_DB = {
        'NIFTY': {'token': '99926015', 'exchange': 'NSE', 'type': 'INDEX'},
        'BANKNIFTY': {'token': '99926056', 'exchange': 'NSE', 'type': 'INDEX'},
    }
    
    def __init__(self):
        """Initialize Phase 2 adapter with real broker connectivity."""
        self.api_key = os.getenv('ANGELONE_API_KEY', getattr(config, 'ANGELONE_API_KEY', ''))
        self.client_code = os.getenv('ANGELONE_CLIENT_CODE', getattr(config, 'ANGELONE_CLIENT_CODE', ''))
        self.password = os.getenv('ANGELONE_PASSWORD', getattr(config, 'ANGELONE_PASSWORD', ''))
        self.totp_secret = os.getenv('ANGELONE_TOTP_SECRET', getattr(config, 'ANGELONE_TOTP_SECRET', ''))
        
        self.paper_trading = getattr(config, 'PAPER_TRADING', True)
        
        # Session state
        self._token: Optional[str] = None
        self._refresh_token: Optional[str] = None
        self._token_expires_at = 0
        self._session_id: Optional[str] = None
        self._user_id: Optional[str] = None
        self._lock = threading.Lock()
        
        # Auto-refresh
        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_refresh = threading.Event()
        
        # SmartAPI client
        self._smartapi_client = None
        
        logger.info(f"AngelOnePhase2 initialized (PAPER_TRADING={self.paper_trading})")
    
    # =========================================================================
    # AUTH & SESSION (Real SmartAPI)
    # =========================================================================
    
    def _generate_totp_code(self) -> str:
        """Generate TOTP code from secret."""
        try:
            if not pyotp or not self.totp_secret:
                logger.warning("TOTP generation unavailable")
                return "000000"
            
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            logger.debug(f"TOTP code generated: {code}")
            return code
        except Exception as e:
            logger.error(f"TOTP generation failed: {e}")
            return "000000"
    
    def login(self) -> bool:
        """Real AngelOne login via SmartAPI."""
        with self._lock:
            try:
                if self.paper_trading:
                    logger.info("PAPER_TRADING: Simulating login")
                    self._token = f"PAPER_{int(time.time())}"
                    self._token_expires_at = time.time() + 3600
                    return True
                
                if not (self.api_key and self.client_code and self.password):
                    logger.error("Missing credentials for real login")
                    return False
                
                # Try SmartAPI SDK first
                if SmartConnect:
                    return self._login_smartapi()
                else:
                    # Fallback to HTTP
                    return self._login_rest_http()
                    
            except Exception as e:
                logger.error(f"Login failed: {e}")
                return False
    
    def _login_smartapi(self) -> bool:
        """Login using SmartAPI SDK."""
        try:
            totp_code = self._generate_totp_code()
            
            # Initialize SmartAPI client
            self._smartapi_client = SmartConnect(api_key=self.api_key)
            
            # Login with OTP
            session = self._smartapi_client.generateSession(
                self.client_code,
                self.password,
                totp_code
            )
            
            if session and session.get('status'):
                self._token = session.get('data', {}).get('jwtToken')
                self._refresh_token = session.get('data', {}).get('refreshToken')
                self._session_id = session.get('data', {}).get('sessionID')
                self._user_id = session.get('data', {}).get('userID')
                self._token_expires_at = time.time() + 86400  # 24 hours
                
                logger.info(f"SmartAPI login successful: {self.client_code}")
                return True
            else:
                logger.error(f"SmartAPI login failed: {session}")
                return False
                
        except Exception as e:
            logger.error(f"SmartAPI login error: {e}")
            return False
    
    def _login_rest_http(self) -> bool:
        """Login using REST HTTP (fallback if SDK unavailable)."""
        try:
            totp_code = self._generate_totp_code()
            
            url = f"{self.API_BASE}{self.AUTH_ENDPOINT}"
            payload = {
                'clientcode': self.client_code,
                'password': self.password,
                'totp': totp_code
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') == True and data.get('data'):
                auth_token = data['data'].get('authToken')
                self._token = auth_token
                self._session_id = data['data'].get('sessionID')
                self._user_id = data['data'].get('userID')
                self._token_expires_at = time.time() + 86400  # 24 hours
                
                logger.info(f"REST login successful: {self.client_code}")
                return True
            else:
                logger.error(f"REST login failed: {data.get('message')}")
                return False
                
        except Exception as e:
            logger.error(f"REST login error: {e}")
            return False
    
    def start_auto_refresh(self) -> None:
        """Start background token refresh thread."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return
        
        self._stop_refresh.clear()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        logger.info("Token auto-refresh thread started")
    
    def _refresh_loop(self):
        """Background loop for token refresh."""
        while not self._stop_refresh.is_set():
            try:
                now = time.time()
                to_sleep = max(1, int(self._token_expires_at - now - 300))  # Refresh 5 min before
                
                if to_sleep > 0:
                    time.sleep(min(to_sleep, 30))  # Check every 30s max
                else:
                    if not self.is_authenticated():
                        logger.warning("Token expired; attempting re-login")
                        self.login()
                    time.sleep(5)
            except Exception as e:
                logger.error(f"Refresh loop error: {e}")
                time.sleep(5)
    
    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh thread."""
        self._stop_refresh.set()
    
    def is_authenticated(self) -> bool:
        """Check if authenticated."""
        return bool(self._token and time.time() < self._token_expires_at)
    
    # =========================================================================
    # MARKET DATA
    # =========================================================================
    
    def get_ltp(self, symbol: str) -> Dict:
        """Get real LTP from broker."""
        try:
            if not self.is_authenticated():
                logger.error("Not authenticated for LTP query")
                return {'status': 'error', 'reason': 'Not authenticated'}
            
            if self.paper_trading:
                # Simulated LTP
                return {
                    'symbol': symbol,
                    'ltp': 20000.0,
                    'bid': 19995.0,
                    'ask': 20005.0,
                    'volume': 1000,
                    'oi': 10000
                }
            
            # Try SmartAPI first
            if self._smartapi_client:
                try:
                    token = self._symbol_to_token(symbol)
                    if not token:
                        return {'status': 'error', 'reason': f'Unknown symbol: {symbol}'}
                    
                    quote = self._smartapi_client.getQuote(
                        mode='LTP',
                        exchangeTokens={'NFO': [token]}
                    )
                    
                    if quote and quote.get('status'):
                        data = quote['data']['fetched'][0]
                        return {
                            'symbol': symbol,
                            'ltp': data.get('ltp'),
                            'bid': data.get('bid'),
                            'ask': data.get('ask'),
                            'volume': data.get('volume'),
                            'oi': data.get('oi')
                        }
                except Exception as e:
                    logger.debug(f"SmartAPI LTP failed: {e}, trying REST")
            
            # Fallback to REST
            return self._get_ltp_rest(symbol)
            
        except Exception as e:
            logger.error(f"get_ltp({symbol}): {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _get_ltp_rest(self, symbol: str) -> Dict:
        """Get LTP via REST API."""
        try:
            url = f"{self.API_BASE}{self.LTP_ENDPOINT}{symbol}"
            headers = {'Authorization': f'Bearer {self._token}'}
            
            response = requests.get(url, headers=headers, timeout=5)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status') and data.get('data'):
                quote = data['data']
                return {
                    'symbol': symbol,
                    'ltp': quote.get('ltp'),
                    'bid': quote.get('bid'),
                    'ask': quote.get('ask'),
                    'volume': quote.get('volume'),
                    'oi': quote.get('oi')
                }
            else:
                logger.warning(f"LTP REST response: {data}")
                return {'status': 'error', 'reason': data.get('message')}
                
        except Exception as e:
            logger.error(f"_get_ltp_rest({symbol}): {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _symbol_to_token(self, symbol: str) -> Optional[str]:
        """Convert symbol to broker token."""
        try:
            # For now, hardcoded mapping
            # TODO: Load from broker instrument file
            if symbol in self.INSTRUMENT_DB:
                return self.INSTRUMENT_DB[symbol]['token']
            
            # Try to extract token for options
            # Format: NIFTY08JAN2620000CE → need to lookup
            logger.warning(f"Token not found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"_symbol_to_token({symbol}): {e}")
            return None
    
    # =========================================================================
    # ORDER MANAGEMENT
    # =========================================================================
    
    def place_order(self, order_payload: Dict) -> Dict:
        """Place real order on broker."""
        try:
            logger.info(f"Placing real order: {order_payload}")
            
            # Paper mode
            if self.paper_trading:
                order_id = f"PAPER_{int(time.time())}_{int(time.time()%1000)}"
                return {
                    'status': 'success',
                    'orderid': order_id,
                    'message': 'Paper order simulated'
                }
            
            # Must be authenticated
            if not self.is_authenticated():
                if not self.login():
                    return {'status': 'failed', 'reason': 'Authentication failed'}
            
            symbol = order_payload.get('symbol')
            if not symbol:
                return {'status': 'failed', 'reason': 'Missing symbol'}
            
            # Try SmartAPI first
            if self._smartapi_client:
                return self._place_order_smartapi(order_payload)
            else:
                return self._place_order_rest(order_payload)
                
        except Exception as e:
            logger.error(f"place_order error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _place_order_smartapi(self, order_payload: Dict) -> Dict:
        """Place order via SmartAPI SDK."""
        try:
            # Build SmartAPI order
            smart_order = {
                'variety': 'regular',
                'tradingsymbol': order_payload['symbol'],
                'symboltoken': self._symbol_to_token(order_payload['symbol']) or '0',
                'transactiontype': order_payload['side'],  # BUY/SELL
                'exchange': order_payload.get('exchange', 'NFO'),
                'ordertype': order_payload.get('type', 'MARKET'),  # MARKET/LIMIT
                'producttype': 'MIS',  # Intraday
                'price': order_payload.get('price', 0),
                'quantity': str(order_payload['qty']),
                'pricetype': 'LTP' if order_payload.get('type') == 'MARKET' else 'LIMIT',
                'clientcode': self.client_code
            }
            
            response = self._smartapi_client.placeOrder(smart_order)
            
            if response and response.get('status'):
                order_id = response.get('data', {}).get('orderid')
                logger.info(f"Order placed: {order_id}")
                return {'status': 'success', 'orderid': order_id}
            else:
                logger.error(f"Order placement failed: {response}")
                return {'status': 'failed', 'reason': response.get('message')}
                
        except Exception as e:
            logger.error(f"_place_order_smartapi error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def _place_order_rest(self, order_payload: Dict) -> Dict:
        """Place order via REST API (with retry)."""
        try:
            url = f"{self.API_BASE}{self.PLACE_ORDER_ENDPOINT}"
            headers = {
                'Authorization': f'Bearer {self._token}',
                'Content-Type': 'application/json'
            }
            
            order_data = {
                'variety': 'regular',
                'tradingsymbol': order_payload['symbol'],
                'symboltoken': self._symbol_to_token(order_payload['symbol']) or '0',
                'transactiontype': order_payload['side'],
                'exchange': order_payload.get('exchange', 'NFO'),
                'ordertype': order_payload.get('type', 'MARKET'),
                'producttype': 'MIS',
                'price': order_payload.get('price', 0),
                'quantity': order_payload['qty'],
                'clientcode': self.client_code
            }
            
            # Retry logic
            for attempt in range(3):
                try:
                    response = requests.post(url, json=order_data, headers=headers, timeout=10)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if data.get('status') and data.get('data'):
                        order_id = data['data'].get('orderid')
                        logger.info(f"Order placed (REST): {order_id}")
                        return {'status': 'success', 'orderid': order_id}
                    else:
                        logger.error(f"Order failed: {data.get('message')}")
                        return {'status': 'failed', 'reason': data.get('message')}
                        
                except requests.exceptions.Timeout:
                    if attempt < 2:
                        logger.warning(f"Timeout, retrying ({attempt+1}/3)")
                        time.sleep(1)
                        continue
                    else:
                        return {'status': 'error', 'reason': 'Request timeout'}
                except Exception as e:
                    if attempt < 2:
                        logger.warning(f"Error, retrying ({attempt+1}/3): {e}")
                        time.sleep(1)
                        continue
                    else:
                        return {'status': 'error', 'reason': str(e)}
            
            return {'status': 'error', 'reason': 'Max retries exceeded'}
            
        except Exception as e:
            logger.error(f"_place_order_rest error: {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order."""
        try:
            logger.info(f"Cancelling order: {order_id}")
            
            if self.paper_trading:
                return {'status': 'success', 'orderid': order_id}
            
            if not self.is_authenticated():
                return {'status': 'failed', 'reason': 'Not authenticated'}
            
            if self._smartapi_client:
                response = self._smartapi_client.cancelOrder(
                    variety='regular',
                    orderid=order_id
                )
                
                if response and response.get('status'):
                    logger.info(f"Order cancelled: {order_id}")
                    return {'status': 'success', 'orderid': order_id}
                else:
                    return {'status': 'failed', 'reason': response.get('message')}
            
            # REST fallback
            return {'status': 'failed', 'reason': 'Cancel not implemented via REST'}
            
        except Exception as e:
            logger.error(f"cancel_order({order_id}): {e}")
            return {'status': 'error', 'reason': str(e)}
    
    def get_order_status(self, order_id: str) -> Dict:
        """Get order status."""
        try:
            if self.paper_trading:
                return {'orderid': order_id, 'status': 'filled', 'filled_qty': 1}
            
            if not self.is_authenticated():
                return {'status': 'error', 'reason': 'Not authenticated'}
            
            if self._smartapi_client:
                # Query order status
                pass  # TODO: Implement
            
            return {'orderid': order_id, 'status': 'unknown'}
            
        except Exception as e:
            logger.error(f"get_order_status({order_id}): {e}")
            return {'status': 'error'}


# Backward compatibility alias
AngelOneClient = AngelOnePhase2

__all__ = ["AngelOnePhase2", "AngelOneClient"]
