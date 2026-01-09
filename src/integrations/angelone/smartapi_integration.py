"""
Complete AngelOne SmartAPI Integration
Real authentication, market data, and order placement implementation
"""
import time
import pyotp
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime

# SmartAPI import (handles both smartapi and SmartApi package names)
try:
    from smartapi import SmartConnect
    from smartapi.smartExceptions import SmartAPIException
except ImportError:
    try:
        from SmartApi import SmartConnect  # type: ignore
        from SmartApi.smartExceptions import SmartAPIException  # type: ignore
    except ImportError as exc:  # pragma: no cover
        SmartConnect = None  # type: ignore
        SmartAPIException = Exception  # type: ignore
        _smartapi_import_error = exc
    else:
        _smartapi_import_error = None
else:
    _smartapi_import_error = None

from config import config
from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class SmartAPIClient:
    """Complete SmartAPI integration with real authentication and trading."""
    
    def __init__(self, api_key: str, client_code: str, password: str, totp_secret: str):
        """Initialize SmartAPI client.
        
        Args:
            api_key: Angel One API key
            client_code: Client/User ID  
            password: PIN/Password
            totp_secret: TOTP secret for 2FA
        """
        self.api_key = api_key
        self.client_code = client_code
        self.password = password
        self.totp_secret = totp_secret
        
        # SmartConnect instance
        self.smart_connect: Optional[SmartConnect] = None  # type: ignore
        self.auth_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.feed_token: Optional[str] = None
        
        logger.info("SmartAPIClient initialized")
    
    # ========================================================================
    # AUTHENTICATION
    # ========================================================================
    
    def generate_totp(self) -> str:
        """Generate TOTP code for 2FA authentication.
        
        Returns: 6-digit TOTP code
        """
        try:
            totp = pyotp.TOTP(self.totp_secret)
            code = totp.now()
            logger.debug(f"Generated TOTP code: {code}")
            return code
        except Exception as e:
            logger.error(f"TOTP generation failed: {e}")
            raise
    
    def login(self) -> bool:
        """Authenticate with Angel One SmartAPI.
        
        Returns: True if login successful, False otherwise
        """
        try:
            if SmartConnect is None:
                raise ImportError(f"SmartAPI SDK not importable: {_smartapi_import_error}")

            logger.info("Attempting SmartAPI login...")
            
            # Initialize SmartConnect
            self.smart_connect = SmartConnect(api_key=self.api_key)
            
            # Use low-level call to include TOTP explicitly
            totp_code = self.generate_totp()
            payload = {
                "clientcode": self.client_code,
                "password": self.password,
                "totp": totp_code,
            }
            data = self.smart_connect._postRequest("api.login", payload)

            if data and data.get('status'):
                jwt_token = data['data']['jwtToken']
                refresh_token = data['data']['refreshToken']
                feed_token = data['data'].get('feedToken') or data['data'].get('feedtoken')

                self.auth_token = jwt_token
                self.refresh_token = refresh_token
                self.feed_token = feed_token

                self.smart_connect.setAccessToken(jwt_token)
                self.smart_connect.setRefreshToken(refresh_token)
                if feed_token:
                    self.smart_connect.setFeedToken(feed_token)

                logger.info("✓ SmartAPI login successful")
                if self.feed_token:
                    logger.info(f"  Feed Token: {str(self.feed_token)[:20]}...")
                return True
            else:
                logger.error(f"Login failed: {data}")
                return False
                
        except SmartAPIException as e:
            logger.error(f"SmartAPI login exception: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected login error: {e}")
            return False
    
    def get_profile(self) -> Optional[Dict]:
        """Get user profile information.
        
        Returns: Profile dict or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            profile = self.smart_connect.getProfile(self.refresh_token)
            logger.info(f"Profile: {profile.get('data', {}).get('name', 'Unknown')}")
            return profile
            
        except Exception as e:
            logger.error(f"get_profile failed: {e}")
            return None
    
    def logout(self) -> bool:
        """Logout from SmartAPI.
        
        Returns: True if successful
        """
        try:
            if self.smart_connect:
                self.smart_connect.terminateSession(self.client_code)
                logger.info("Logged out from SmartAPI")
            return True
        except Exception as e:
            logger.error(f"Logout error: {e}")
            return False
    
    # ========================================================================
    # MARKET DATA
    # ========================================================================
    
    def get_ltp_data(self, exchange: str, trading_symbol: str, token: str) -> Optional[Dict]:
        """Get Last Traded Price (LTP) for a symbol.
        
        Args:
            exchange: 'NSE', 'NFO', 'BSE', etc.
            trading_symbol: Symbol name (e.g., 'NIFTY23JAN24000CE')
            token: Instrument token
        
        Returns: LTP data dict or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            ltp_data = self.smart_connect.ltpData(
                exchange=exchange,
                tradingsymbol=trading_symbol,
                symboltoken=token
            )
            
            if ltp_data and ltp_data.get('status'):
                return ltp_data['data']
            else:
                logger.warning(f"LTP fetch failed: {ltp_data}")
                return None
                
        except Exception as e:
            logger.error(f"get_ltp_data({trading_symbol}): {e}")
            return None
    
    def get_quote(self, exchange: str, trading_symbol: str, token: str = None) -> Optional[Dict]:
        """Get full quote data including Greeks for options.
        
        Args:
            exchange: 'NSE', 'NFO', 'BSE', etc.
            trading_symbol: Symbol name
            token: Instrument token (optional, will search if not provided)
        
        Returns: Quote data dict with Greeks or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            # If token not provided, search for it
            if not token:
                scrip = self.search_scrip(exchange, trading_symbol)
                if scrip and len(scrip) > 0:
                    token = scrip[0].get('symboltoken')
                else:
                    logger.warning(f"Could not find token for {trading_symbol}")
                    return None
            
            # Get quote data
            quote_data = self.smart_connect.getQuote(
                exchange=exchange,
                tradingsymbol=trading_symbol,
                symboltoken=token
            )
            
            if quote_data and quote_data.get('status'):
                return quote_data
            else:
                logger.warning(f"Quote fetch failed: {quote_data}")
                return None
                
        except Exception as e:
            logger.error(f"get_quote({trading_symbol}): {e}")
            return None
    
    def search_scrip(self, exchange: str, searchtext: str) -> Optional[List[Dict]]:
        """Search for instruments by text.
        
        Args:
            exchange: 'NSE', 'NFO', etc.
            searchtext: Search query (e.g., 'NIFTY')
        
        Returns: List of matching instruments
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            results = self.smart_connect.searchScrip(
                exchange=exchange,
                searchtext=searchtext
            )
            
            if results and results.get('status'):
                return results['data']
            return []
            
        except Exception as e:
            logger.error(f"search_scrip({searchtext}): {e}")
            return None
    
    # ========================================================================
    # ORDER MANAGEMENT
    # ========================================================================
    
    def place_order(
        self,
        tradingsymbol: str,
        symboltoken: str,
        exchange: str,
        transactiontype: str,  # 'BUY' or 'SELL'
        ordertype: str,        # 'MARKET', 'LIMIT', 'STOPLOSS_LIMIT', etc.
        quantity: int,
        price: float = 0,
        triggerprice: float = 0,
        producttype: str = 'CARRYFORWARD',  # 'CARRYFORWARD', 'INTRADAY', 'DELIVERY'
        duration: str = 'DAY',              # 'DAY', 'IOC'
        variety: str = 'NORMAL'             # 'NORMAL', 'STOPLOSS', 'ROBO'
    ) -> Optional[Dict]:
        """Place an order.
        
        Args:
            tradingsymbol: Symbol name
            symboltoken: Instrument token
            exchange: Exchange (NSE, NFO, etc.)
            transactiontype: BUY or SELL
            ordertype: MARKET, LIMIT, STOPLOSS_LIMIT, etc.
            quantity: Order quantity
            price: Limit price (for LIMIT orders)
            triggerprice: Trigger price (for SL orders)
            producttype: CARRYFORWARD or INTRADAY
            duration: DAY, IOC
            variety: NORMAL, STOPLOSS, AMO
        
        Returns: Order response dict or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            # Build order params according to AngelOne documentation
            order_params = {
                "variety": variety,
                "tradingsymbol": tradingsymbol,
                "symboltoken": symboltoken,
                "transactiontype": transactiontype,
                "exchange": exchange,
                "ordertype": ordertype,
                "producttype": producttype,
                "duration": duration,
                "price": str(price),
                "squareoff": "0",
                "stoploss": "0",
                "quantity": str(quantity)
            }
            
            # Add triggerprice only for SL orders
            if ordertype in ['STOPLOSS_LIMIT', 'STOPLOSS_MARKET']:
                order_params["triggerprice"] = str(triggerprice)
            
            logger.info(f"Placing order: {transactiontype} {quantity} {tradingsymbol} @ {ordertype}")
            
            response = self.smart_connect.placeOrder(order_params)
            
            if response and response.get('status'):
                order_id = response['data']['orderid']
                logger.info(f"✓ Order placed successfully: {order_id}")
                return response['data']
            else:
                logger.error(f"Order placement failed: {response}")
                return None
                
        except SmartAPIException as e:
            logger.error(f"SmartAPI order error: {e}")
            return None
        except Exception as e:
            logger.error(f"place_order error: {e}")
            return None
    
    def modify_order(
        self,
        orderid: str,
        variety: str,
        ordertype: str,
        quantity: int,
        price: float = 0,
        triggerprice: float = 0
    ) -> Optional[Dict]:
        """Modify an existing order.
        
        Args:
            orderid: Order ID to modify
            variety: Order variety
            ordertype: Order type
            quantity: New quantity
            price: New price
            triggerprice: New trigger price
        
        Returns: Modification response or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            # Build modify params according to AngelOne documentation
            modify_params = {
                "variety": variety,
                "orderid": orderid,
                "ordertype": ordertype,
                "producttype": "CARRYFORWARD",
                "duration": "DAY",
                "price": str(price),
                "quantity": str(quantity),
                "tradingsymbol": "",  # Not required for modify
                "symboltoken": "",
                "exchange": "NFO"
            }
            
            # Add triggerprice only for SL orders
            if triggerprice > 0 and ordertype in ['STOPLOSS_LIMIT', 'STOPLOSS_MARKET']:
                modify_params['triggerprice'] = str(triggerprice)
            
            response = self.smart_connect.modifyOrder(modify_params)
            
            if response and response.get('status'):
                logger.info(f"✓ Order {orderid} modified successfully")
                return response['data']
            else:
                logger.error(f"Order modification failed: {response}")
                return None
                
        except Exception as e:
            logger.error(f"modify_order error: {e}")
            return None
    
    def cancel_order(self, orderid: str, variety: str = 'NORMAL') -> bool:
        """Cancel an order.
        
        Args:
            orderid: Order ID to cancel
            variety: Order variety
        
        Returns: True if successful
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return False
            
            response = self.smart_connect.cancelOrder(
                orderid=orderid,
                variety=variety
            )
            
            if response and response.get('status'):
                logger.info(f"✓ Order {orderid} cancelled")
                return True
            else:
                logger.error(f"Order cancellation failed: {response}")
                return False
                
        except Exception as e:
            logger.error(f"cancel_order error: {e}")
            return False
    
    def get_order_book(self) -> Optional[List[Dict]]:
        """Get all orders for the day.
        
        Returns: List of orders or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            response = self.smart_connect.orderBook()
            
            if response and response.get('status'):
                return response['data']
            return []
            
        except Exception as e:
            logger.error(f"get_order_book error: {e}")
            return None
    
    def get_position(self) -> Optional[Dict]:
        """Get current positions.
        
        Returns: Position data or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            response = self.smart_connect.position()
            
            if response and response.get('status'):
                return response['data']
            return None
            
        except Exception as e:
            logger.error(f"get_position error: {e}")
            return None
    
    # ========================================================================
    # FUNDS & MARGINS
    # ========================================================================
    
    def get_rms_limits(self) -> Optional[Dict]:
        """Get RMS (funds and margin) limits.
        
        Returns: RMS data or None
        """
        try:
            if not self.smart_connect:
                logger.error("Not authenticated")
                return None
            
            response = self.smart_connect.rmsLimit()
            
            if response and response.get('status'):
                return response['data']
            return None
            
        except Exception as e:
            logger.error(f"get_rms_limits error: {e}")
            return None


__all__ = ['SmartAPIClient']
