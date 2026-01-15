"""
WebSocket Client for SmartAPI (AngelOne)

Features:
- Real-time tick-by-tick data streaming
- Auto-reconnection with exponential backoff
- Heartbeat monitoring
- Event-driven architecture
- Thread-safe operations
"""

import json
import time
import threading
import websocket
from typing import Callable, Dict, List, Optional, Any
from datetime import datetime
from enum import Enum
import logging
from collections import defaultdict

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class SubscriptionMode(Enum):
    """WebSocket subscription modes"""

    LTP = 1  # Last Traded Price
    QUOTE = 2  # Quote (LTP + Volume + OI)
    SNAP_QUOTE = 3  # Snapshot Quote (Full depth)


class WebSocketClient:
    """
    WebSocket client for real-time data streaming

    Handles:
    - Connection management
    - Automatic reconnection
    - Subscription management
    - Event callbacks
    - Heartbeat monitoring
    """

    # SmartAPI WebSocket endpoints
    WS_ENDPOINT = "wss://smartapisocket.angelone.in/smart-stream"

    def __init__(
        self,
        api_key: str,
        client_code: str,
        feed_token: str,
        on_message: Optional[Callable] = None,
        on_error: Optional[Callable] = None,
        on_close: Optional[Callable] = None,
        on_open: Optional[Callable] = None,
    ):
        """
        Initialize WebSocket client

        Args:
            api_key: API key from broker
            client_code: Client code
            feed_token: Feed token for authentication
            on_message: Callback for messages
            on_error: Callback for errors
            on_close: Callback for connection close
            on_open: Callback for connection open
        """
        self.api_key = api_key
        self.client_code = client_code
        self.feed_token = feed_token

        # Callbacks
        self._on_message = on_message
        self._on_error = on_error
        self._on_close = on_close
        self._on_open = on_open

        # Connection state
        self.ws: Optional[websocket.WebSocketApp] = None
        self.is_connected = False
        self.is_running = False

        # Subscription tracking
        self.subscriptions: Dict[str, List[str]] = defaultdict(list)  # mode -> tokens
        self.token_map: Dict[str, Dict] = {}  # token -> instrument details

        # Reconnection settings
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 1  # seconds
        self.reconnect_multiplier = 2
        self.max_reconnect_delay = 60

        # Threading
        self.ws_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()

        # Heartbeat monitoring
        self.last_heartbeat = None
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 90  # seconds

        logger.info("WebSocket client initialized")

    def connect(self) -> bool:
        """
        Establish WebSocket connection

        Returns:
            bool: True if connection successful
        """
        try:
            if self.is_connected:
                logger.warning("Already connected")
                return True

            logger.info("Connecting to WebSocket...")

            # Create WebSocket app
            self.ws = websocket.WebSocketApp(
                self.WS_ENDPOINT,
                on_open=self._handle_on_open,
                on_message=self._handle_on_message,
                on_error=self._handle_on_error,
                on_close=self._handle_on_close,
                header={
                    "Authorization": f"Bearer {self.feed_token}",
                    "x-api-key": self.api_key,
                    "x-client-code": self.client_code,
                },
            )

            # Start WebSocket in separate thread
            self.is_running = True
            self.ws_thread = threading.Thread(target=self._run_websocket, daemon=True)
            self.ws_thread.start()

            # Wait for connection (with timeout)
            timeout = 10
            start_time = time.time()
            while not self.is_connected and time.time() - start_time < timeout:
                time.sleep(0.1)

            if self.is_connected:
                logger.info("✅ WebSocket connected successfully")
                return True
            else:
                logger.error("❌ WebSocket connection timeout")
                return False

        except Exception as e:
            logger.error(f"Connection error: {e}")
            return False

    def disconnect(self):
        """Disconnect WebSocket"""
        try:
            logger.info("Disconnecting WebSocket...")
            self.is_running = False

            if self.ws:
                self.ws.close()

            if self.ws_thread and self.ws_thread.is_alive():
                self.ws_thread.join(timeout=5)

            self.is_connected = False
            logger.info("WebSocket disconnected")

        except Exception as e:
            logger.error(f"Disconnect error: {e}")

    def subscribe(self, tokens: List[str], mode: SubscriptionMode = SubscriptionMode.QUOTE, exchange: str = "NFO"):
        """
        Subscribe to instruments

        Args:
            tokens: List of instrument tokens
            mode: Subscription mode (LTP, QUOTE, SNAP_QUOTE)
            exchange: Exchange (NSE, BSE, NFO, etc.)
        """
        try:
            if not self.is_connected:
                logger.error("Not connected - cannot subscribe")
                return

            # Build subscription message
            subscription_msg = {"action": 1, "params": {"mode": mode.value, "tokenlist": tokens}}  # Subscribe

            # Send subscription
            if self.ws:
                self.ws.send(json.dumps(subscription_msg))

            # Track subscriptions
            mode_key = f"{exchange}_{mode.value}"
            with self.lock:
                self.subscriptions[mode_key].extend(tokens)
                for token in tokens:
                    self.token_map[token] = {"exchange": exchange, "mode": mode}

            logger.info(f"Subscribed to {len(tokens)} instruments ({mode.name})")

        except Exception as e:
            logger.error(f"Subscribe error: {e}")

    def unsubscribe(self, tokens: List[str], mode: SubscriptionMode = SubscriptionMode.QUOTE, exchange: str = "NFO"):
        """Unsubscribe from instruments"""
        try:
            if not self.is_connected:
                return

            # Build unsubscription message
            unsubscription_msg = {"action": 0, "params": {"mode": mode.value, "tokenlist": tokens}}  # Unsubscribe

            # Send unsubscription
            if self.ws:
                self.ws.send(json.dumps(unsubscription_msg))

            # Remove from tracking
            mode_key = f"{exchange}_{mode.value}"
            with self.lock:
                for token in tokens:
                    if token in self.subscriptions[mode_key]:
                        self.subscriptions[mode_key].remove(token)
                    if token in self.token_map:
                        del self.token_map[token]

            logger.info(f"Unsubscribed from {len(tokens)} instruments")

        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")

    def _run_websocket(self):
        """Run WebSocket connection with auto-reconnect"""
        reconnect_attempt = 0

        while self.is_running:
            try:
                # Run WebSocket (blocking call)
                if self.ws:
                    self.ws.run_forever(ping_interval=self.heartbeat_interval, ping_timeout=10)

                # If we reach here, connection was closed
                if self.is_running:
                    # Calculate reconnect delay
                    delay = min(
                        self.reconnect_delay * (self.reconnect_multiplier**reconnect_attempt), self.max_reconnect_delay
                    )

                    logger.warning(f"Connection lost. Reconnecting in {delay}s...")
                    time.sleep(delay)

                    reconnect_attempt += 1
                    if reconnect_attempt >= self.max_reconnect_attempts:
                        logger.error("Max reconnection attempts reached")
                        break

                    # Recreate WebSocket
                    self.connect()

            except Exception as e:
                logger.error(f"WebSocket run error: {e}")
                if self.is_running:
                    time.sleep(self.reconnect_delay)

    def _handle_on_open(self, ws):
        """Handle WebSocket open event"""
        self.is_connected = True
        self.last_heartbeat = time.time()
        logger.info("WebSocket connection opened")

        if self._on_open:
            try:
                self._on_open(ws)
            except Exception as e:
                logger.error(f"on_open callback error: {e}")

    def _handle_on_message(self, ws, message):
        """Handle incoming WebSocket message"""
        try:
            self.last_heartbeat = time.time()

            # Parse message
            if isinstance(message, bytes):
                # Binary data (tick data)
                data = self._parse_binary_message(message)
            else:
                # JSON data
                data = json.loads(message)

            # Call user callback
            if self._on_message:
                self._on_message(ws, data)

        except Exception as e:
            logger.error(f"Message handling error: {e}")

    def _handle_on_error(self, ws, error):
        """Handle WebSocket error"""
        logger.error(f"WebSocket error: {error}")

        if self._on_error:
            try:
                self._on_error(ws, error)
            except Exception as e:
                logger.error(f"on_error callback error: {e}")

    def _handle_on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close event"""
        self.is_connected = False
        logger.warning(f"WebSocket connection closed: {close_status_code} - {close_msg}")

        if self._on_close:
            try:
                self._on_close(ws, close_status_code, close_msg)
            except Exception as e:
                logger.error(f"on_close callback error: {e}")

    def _parse_binary_message(self, message: bytes) -> Dict:
        """
        Parse binary tick data from SmartAPI WebSocket.

        SmartAPI sends binary format with:
        - Token (4 bytes)
        - LTP (8 bytes)
        - Volume (8 bytes)
        - Greeks data (for options)
        """
        try:
            if len(message) < 20:
                logger.debug(f"Binary data too short: {len(message)} bytes")
                return {"type": "tick", "raw": message}

            import struct

            # Parse according to SmartAPI documentation
            offset = 0

            # Token (4 bytes, big-endian)
            token = struct.unpack(">I", message[offset : offset + 4])[0]
            offset += 4

            # LTP (8 bytes, double)
            ltp = struct.unpack(">d", message[offset : offset + 8])[0]
            offset += 8

            # High (8 bytes, double)
            high = struct.unpack(">d", message[offset : offset + 8])[0]
            offset += 8

            # Low (8 bytes, double)
            low = struct.unpack(">d", message[offset : offset + 8])[0]
            offset += 8

            # Close (8 bytes, double)
            close = struct.unpack(">d", message[offset : offset + 8])[0]
            offset += 8

            # Volume (8 bytes, long)
            volume = struct.unpack(">Q", message[offset : offset + 8])[0]
            offset += 8

            # IV (8 bytes, double) - for options
            iv = 0.0
            if len(message) >= offset + 8:
                iv = struct.unpack(">d", message[offset : offset + 8])[0]
                offset += 8

            # Greeks data if available
            delta, gamma, theta, vega = 0, 0, 0, 0
            if len(message) >= offset + 32:
                try:
                    delta = struct.unpack(">d", message[offset : offset + 8])[0]
                    offset += 8
                    gamma = struct.unpack(">d", message[offset : offset + 8])[0]
                    offset += 8
                    theta = struct.unpack(">d", message[offset : offset + 8])[0]
                    offset += 8
                    vega = struct.unpack(">d", message[offset : offset + 8])[0]
                except:
                    pass

            result = {
                "type": "tick",
                "token": token,
                "ltp": ltp,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
                "iv": iv,
                "delta": delta,
                "gamma": gamma,
                "theta": theta,
                "vega": vega,
            }

            logger.debug(f"Parsed binary: token={token}, ltp={ltp}, vol={volume}")
            return result

        except struct.error as e:
            logger.error(f"Binary parsing error: {e}")
            return {"type": "tick", "raw": message}
        except Exception as e:
            logger.error(f"Unexpected binary parsing error: {e}")
            return {"type": "tick", "raw": message}

    def _get_exchange_code(self, exchange: str) -> int:
        """Convert exchange name to code"""
        exchange_codes = {
            "NSE": 1,
            "NFO": 2,
            "BSE": 3,
            "BFO": 4,
            "MCX": 5,
            "NCDFEX": 7,
        }
        return exchange_codes.get(exchange, 1)

    def is_alive(self) -> bool:
        """Check if connection is alive based on heartbeat"""
        if not self.is_connected:
            return False

        if self.last_heartbeat is None:
            return False

        time_since_heartbeat = time.time() - self.last_heartbeat
        return time_since_heartbeat < self.heartbeat_timeout

    def get_subscription_count(self) -> int:
        """Get total number of active subscriptions"""
        with self.lock:
            return sum(len(tokens) for tokens in self.subscriptions.values())

    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()
