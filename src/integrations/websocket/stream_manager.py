"""
Stream Manager for Real-time Data

Manages multiple data streams:
- Price ticks (NIFTY/BANKNIFTY)
- Option chain updates
- Market depth (Order book)
- Greeks calculations
"""

import time
from typing import Dict, List, Callable, Optional, Any
from datetime import datetime
from collections import deque, defaultdict
import threading

from src.utils.logger import StrategyLogger
from .websocket_client import WebSocketClient, SubscriptionMode

logger = StrategyLogger.get_logger(__name__)


class StreamManager:
    """
    Manages real-time data streams
    
    Features:
    - Multi-instrument streaming
    - Data buffering and aggregation
    - Tick recording
    - Real-time callbacks
    """
    
    def __init__(
        self,
        websocket_client: WebSocketClient,
        buffer_size: int = 1000
    ):
        """
        Initialize stream manager
        
        Args:
            websocket_client: WebSocket client instance
            buffer_size: Max ticks to buffer per instrument
        """
        self.ws_client = websocket_client
        self.buffer_size = buffer_size
        
        # Data buffers
        self.tick_buffers: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=buffer_size)
        )
        self.latest_ticks: Dict[str, Dict] = {}
        
        # Callbacks
        self.tick_callbacks: List[Callable] = []
        self.greeks_callbacks: List[Callable] = []
        self.orderbook_callbacks: List[Callable] = []
        
        # Statistics
        self.tick_count = 0
        self.start_time = time.time()
        
        # Lock for thread safety
        self.lock = threading.Lock()
        
        logger.info("StreamManager initialized")
    
    def subscribe_instruments(
        self,
        instruments: List[Dict[str, Any]],
        mode: SubscriptionMode = SubscriptionMode.QUOTE
    ):
        """
        Subscribe to multiple instruments
        
        Args:
            instruments: List of instrument dicts with 'token' and 'exchange'
            mode: Subscription mode
        """
        try:
            # Group by exchange
            exchange_groups = defaultdict(list)
            for inst in instruments:
                exchange = inst.get('exchange', 'NFO')
                token = inst['token']
                exchange_groups[exchange].append(token)
            
            # Subscribe to each exchange group
            for exchange, tokens in exchange_groups.items():
                self.ws_client.subscribe(
                    tokens=tokens,
                    mode=mode,
                    exchange=exchange
                )
            
            logger.info(f"Subscribed to {len(instruments)} instruments")
            
        except Exception as e:
            logger.error(f"Subscribe instruments error: {e}")
    
    def subscribe_nifty_banknifty(self, mode: SubscriptionMode = SubscriptionMode.LTP):
        """Quick subscribe to NIFTY and BANKNIFTY indices"""
        instruments = [
            {"token": "99926000", "exchange": "NSE", "symbol": "NIFTY 50"},
            {"token": "99926009", "exchange": "NSE", "symbol": "NIFTY BANK"},
        ]
        self.subscribe_instruments(instruments, mode)
        logger.info("Subscribed to NIFTY & BANKNIFTY")
    
    def subscribe_option_chain(
        self,
        underlying: str,
        expiry: str,
        strikes: List[int],
        mode: SubscriptionMode = SubscriptionMode.QUOTE
    ):
        """
        Subscribe to complete option chain
        
        Args:
            underlying: Underlying symbol (NIFTY, BANKNIFTY)
            expiry: Expiry date (DDMMMYY format)
            strikes: List of strike prices
            mode: Subscription mode
        """
        try:
            instruments = []
            
            for strike in strikes:
                # Add CE
                instruments.append({
                    "token": self._get_option_token(underlying, expiry, strike, "CE"),
                    "exchange": "NFO",
                    "symbol": f"{underlying} {expiry} {strike} CE"
                })
                
                # Add PE
                instruments.append({
                    "token": self._get_option_token(underlying, expiry, strike, "PE"),
                    "exchange": "NFO",
                    "symbol": f"{underlying} {expiry} {strike} PE"
                })
            
            self.subscribe_instruments(instruments, mode)
            logger.info(f"Subscribed to {len(strikes)} strikes ({len(instruments)} options)")
            
        except Exception as e:
            logger.error(f"Subscribe option chain error: {e}")
    
    def on_tick(self, callback: Callable):
        """Register callback for price ticks"""
        self.tick_callbacks.append(callback)
        logger.debug(f"Registered tick callback: {callback.__name__}")
    
    def on_greeks_update(self, callback: Callable):
        """Register callback for Greeks updates"""
        self.greeks_callbacks.append(callback)
        logger.debug(f"Registered Greeks callback: {callback.__name__}")
    
    def on_orderbook_update(self, callback: Callable):
        """Register callback for order book updates"""
        self.orderbook_callbacks.append(callback)
        logger.debug(f"Registered orderbook callback: {callback.__name__}")
    
    def process_tick(self, tick_data: Dict):
        """
        Process incoming tick data
        
        Args:
            tick_data: Tick data from WebSocket
        """
        try:
            token = tick_data.get('token')
            if not token:
                return
            
            # Parse tick data
            tick = {
                'token': token,
                'timestamp': datetime.now(),
                'ltp': tick_data.get('last_traded_price'),
                'volume': tick_data.get('volume_trade_for_the_day'),
                'oi': tick_data.get('open_interest'),
                'bid': tick_data.get('best_5_buy_data'),
                'ask': tick_data.get('best_5_sell_data'),
                'change': tick_data.get('change'),
                'change_percent': tick_data.get('percentage_change'),
            }
            
            # Update buffers
            with self.lock:
                self.tick_buffers[token].append(tick)
                self.latest_ticks[token] = tick
                self.tick_count += 1
            
            # Trigger callbacks
            for callback in self.tick_callbacks:
                try:
                    callback(tick)
                except Exception as e:
                    logger.error(f"Tick callback error: {e}")
            
            # Check if Greeks update is needed
            if 'delta' in tick_data or 'gamma' in tick_data:
                self._process_greeks_update(tick_data)
            
        except Exception as e:
            logger.error(f"Process tick error: {e}")
    
    def _process_greeks_update(self, data: Dict):
        """Process Greeks data"""
        greeks = {
            'token': data.get('token'),
            'timestamp': datetime.now(),
            'delta': data.get('delta'),
            'gamma': data.get('gamma'),
            'theta': data.get('theta'),
            'vega': data.get('vega'),
            'iv': data.get('implied_volatility'),
        }
        
        # Trigger callbacks
        for callback in self.greeks_callbacks:
            try:
                callback(greeks)
            except Exception as e:
                logger.error(f"Greeks callback error: {e}")
    
    def get_latest_price(self, token: str) -> Optional[float]:
        """Get latest price for token"""
        with self.lock:
            tick = self.latest_ticks.get(token)
            return tick['ltp'] if tick else None
    
    def get_price_history(self, token: str, count: int = 100) -> List[Dict]:
        """Get recent price history"""
        with self.lock:
            buffer = self.tick_buffers.get(token, deque())
            return list(buffer)[-count:]
    
    def get_statistics(self) -> Dict:
        """Get streaming statistics"""
        uptime = time.time() - self.start_time
        
        return {
            'total_ticks': self.tick_count,
            'ticks_per_second': self.tick_count / uptime if uptime > 0 else 0,
            'active_instruments': len(self.latest_ticks),
            'uptime_seconds': uptime,
            'connected': self.ws_client.is_connected,
            'subscriptions': self.ws_client.get_subscription_count(),
        }
    
    def _get_option_token(
        self,
        underlying: str,
        expiry: str,
        strike: int,
        option_type: str
    ) -> str:
        """
        Get option token (placeholder - need actual token mapping)
        
        In production, use instrument master file from broker
        """
        # TODO: Implement actual token lookup from instrument master
        # For now, return placeholder
        return f"{underlying}_{expiry}_{strike}_{option_type}"
    
    def start(self):
        """Start streaming"""
        logger.info("StreamManager started")
    
    def stop(self):
        """Stop streaming"""
        self.ws_client.disconnect()
        logger.info("StreamManager stopped")
