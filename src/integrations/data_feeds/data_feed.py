"""
Data Feed Module
Handles WebSocket connections, LTP updates, quote data, and market depth using OpenAlgo
Optimized for local network resilience with auto-reconnection and retry logic
"""

import json
import time
from threading import Thread, Lock, Event
from datetime import datetime
from src.utils.network_resilience import get_network_monitor
from config import config
from src.utils.logger import StrategyLogger

try:
    from src.integrations.angelone.angelone_client import AngelOneClient

    _angelone_import_error = None
except Exception as exc:
    AngelOneClient = None
    _angelone_import_error = exc
logger = StrategyLogger.get_logger(__name__)


class DataFeed:
    """Manages real-time market data feed via WebSocket"""

    # Reconnection parameters
    MAX_RECONNECT_ATTEMPTS = 5
    RECONNECT_DELAY = 2  # seconds
    PING_INTERVAL = 30  # seconds
    PING_TIMEOUT = 5  # seconds

    def __init__(self):
        self.ws = None
        self.connected = False
        self.subscribed_symbols = set()
        self.subscribed_instruments = []  # Store for re-subscription

        # Thread-safe data storage
        self.data_lock = Lock()
        self.ltp_data = {}
        self.quote_data = {}
        self.depth_data = {}
        self.tick_data = []
        self.tick_csv_path = None
        self._csv_initialized = False

        # Callbacks
        self.on_tick_callbacks = []
        self.on_quote_callbacks = []
        self.on_depth_callbacks = []

        # Reconnection state
        self.reconnect_thread = None
        self.stop_reconnect = Event()
        self.last_tick_received = time.time()

        # REST API Polling fallback (when WebSocket not broadcasting)
        self.use_rest_polling = False
        self.polling_thread = None
        self.last_polled_time = {}
        self.polling_interval = 1.5  # Poll every 1.5 seconds

        # Network health tracking
        self.network_monitor = get_network_monitor()

        logger.info("DataFeed initialized with auto-reconnection + REST API polling fallback")

    def _init_csv(self):
        try:
            from pathlib import Path
            from datetime import datetime

            if not self._csv_initialized:
                ts = datetime.now().strftime("%Y%m%d")
                ticks_dir = Path("ticks")
                ticks_dir.mkdir(exist_ok=True)
                self.tick_csv_path = ticks_dir / f"ticks_{ts}.csv"
                if not self.tick_csv_path.exists():
                    with open(self.tick_csv_path, "w") as f:
                        f.write("timestamp,symbol,ltp,bid,ask,source\n")
                self._csv_initialized = True
        except Exception as e:
            logger.error(f"Error initializing tick CSV: {e}")

    def _write_tick_to_csv(self, tick):
        try:
            if not self._csv_initialized:
                self._init_csv()
            if not self.tick_csv_path:
                return
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            line = f"{ts},{tick.get('symbol')},{tick.get('ltp')},{tick.get('bid')},{tick.get('ask')},{tick.get('source','WEBSOCKET')}\n"
            with open(self.tick_csv_path, "a") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Error writing tick to CSV: {e}")

    def connect(self, retry_count=0):
        """Establish WebSocket connection using OpenAlgo with retry logic"""
        try:
            if retry_count > self.MAX_RECONNECT_ATTEMPTS:
                logger.error("Max reconnection attempts exceeded")
                return False

            logger.info(f"Connecting to WebSocket (attempt {retry_count + 1}/{self.MAX_RECONNECT_ATTEMPTS})...")

            # Select data source: OpenAlgo or AngelOne (broker)
            data_src = getattr(config, "DATA_SOURCE", "openalgo")

            if data_src == "angelone":
                if AngelOneClient is None:
                    logger.error("AngelOne adapter not available", exc_info=_angelone_import_error)
                    return False
                # Initialize AngelOne client adapter
                self.client = AngelOneClient()

                # Try to connect if adapter implements a connect method
                if hasattr(self.client, "connect_ws"):
                    try:
                        result = self.client.connect_ws()
                        self.connected = bool(result) if result is not None else True
                        logger.info("AngelOne WebSocket connected (adapter)")
                    except NotImplementedError:
                        logger.info(
                            "AngelOne adapter connect_ws not implemented — running in offline/demo adapter mode"
                        )
                        self.connected = False
                elif hasattr(self.client, "connect"):
                    try:
                        result = self.client.connect()
                        self.connected = bool(result) if result is not None else True
                        logger.info("AngelOne client connected (adapter)")
                    except NotImplementedError:
                        logger.info("AngelOne adapter connect not implemented — running in offline/demo adapter mode")
                        self.connected = False
                else:
                    logger.info("AngelOne adapter created (no explicit connect method)")

                if self.connected:
                    self.stop_reconnect.clear()
                    self.network_monitor.start_monitoring()
                    logger.info("WebSocket connected successfully")

            else:
                logger.error("OpenAlgo support removed; only 'angelone' DATA_SOURCE is supported")
                return False

            # Start health check thread
            if self.reconnect_thread is None or not self.reconnect_thread.is_alive():
                self.reconnect_thread = Thread(
                    target=self._health_check_loop, daemon=True, name="WebSocket-HealthCheck"
                )
                self.reconnect_thread.start()

            return True

        except TimeoutError:
            logger.warning(f"Connection timeout (attempt {retry_count + 1})")
            time.sleep(self.RECONNECT_DELAY)
            return self.connect(retry_count + 1)

        except Exception as e:
            logger.error(f"WebSocket connection failed: {e} (attempt {retry_count + 1})")
            time.sleep(self.RECONNECT_DELAY)
            return self.connect(retry_count + 1)

    def _health_check_loop(self):
        """Periodically check WebSocket health and reconnect if needed"""
        no_data_count = 0
        fallback_threshold = getattr(config, 'WEBSOCKET_NO_DATA_FALLBACK', 120)
        check_interval = getattr(config, 'WEBSOCKET_TICK_TIMEOUT', 60)
        
        while not self.stop_reconnect.is_set():
            try:
                time.sleep(self.PING_INTERVAL)

                if not self.connected:
                    logger.warning("WebSocket disconnected, attempting reconnect...")
                    self.reconnect()

                # Check if ticks are being received
                time_since_last_tick = time.time() - self.last_tick_received
                if time_since_last_tick > check_interval and self.subscribed_symbols:
                    no_data_count += 1
                    logger.warning(f"No ticks for {time_since_last_tick:.0f}s (threshold: {fallback_threshold}s)")

                    # Activate REST polling fallback after threshold
                    if time_since_last_tick >= fallback_threshold:
                        if not self.use_rest_polling and self.subscribed_instruments:
                            logger.critical(f"🔴 WebSocket NOT broadcasting data for {time_since_last_tick:.0f}s! Starting REST API fallback...")
                            self.check_broker_connection()  # Check broker status
                            self.start_rest_polling(self.subscribed_instruments)

                    if not self._is_connection_alive():
                        logger.warning("Connection appears dead, reconnecting...")
                        self.reconnect()
                else:
                    no_data_count = 0  # Reset counter when data flows

            except Exception as e:
                logger.error(f"Health check error: {e}")
                time.sleep(self.RECONNECT_DELAY)

    def _is_connection_alive(self):
        """Check if WebSocket connection is alive"""
        try:
            if not hasattr(self, "client") or not self.client:
                return False
            # Adapter may expose different connected flags
            if hasattr(self.client, "_connected"):
                return getattr(self.client, "_connected", False)
            if hasattr(self.client, "connected"):
                return getattr(self.client, "connected", False)
            return False
        except:
            return False

    def reconnect(self):
        """Attempt to reconnect to WebSocket"""
        try:
            logger.info("Attempting to reconnect...")
            self.disconnect()
            time.sleep(self.RECONNECT_DELAY)
            self.network_monitor.record_websocket_reconnect()

            if self.connect():
                # Re-subscribe to all previously subscribed symbols
                if self.subscribed_symbols:
                    logger.info(f"Re-subscribing to {len(self.subscribed_symbols)} symbols...")
                    self._resubscribe_all()
                return True
            else:
                logger.error("Reconnection failed")
                return False

        except Exception as e:
            logger.error(f"Reconnection error: {e}")
            return False

    def _resubscribe_all(self):
        """Re-subscribe to all previously subscribed symbols"""
        try:
            if not self.subscribed_instruments:
                logger.warning("No instruments to re-subscribe")
                return

            logger.info(f"Re-subscribing to {len(self.subscribed_instruments)} instruments...")

            # Re-subscribe to LTP for stored instruments
            success = self.subscribe_ltp(self.subscribed_instruments, retry_count=0)
            if success:
                logger.info("Re-subscription successful")
            else:
                logger.warning("Re-subscription failed")

        except Exception as e:
            logger.error(f"Re-subscription error: {e}")

    def disconnect(self):
        """Close WebSocket connection gracefully"""
        try:
            self.stop_reconnect.set()

            if hasattr(self, "client") and self.client:
                self.client.disconnect()
            self.connected = False
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Error disconnecting WebSocket: {e}")

    def subscribe_ltp(self, instruments, callback=None, retry_count=0):
        """
        Subscribe to LTP updates with retry logic

        Args:
            instruments: List of dicts [{'exchange': 'NSE', 'symbol': 'RELIANCE'}, ...]
            callback: Callback function for LTP updates
            retry_count: Internal retry counter
        """
        try:
            if not self.connected:
                logger.warning("Not connected, attempting to connect first...")
                if not self.connect():
                    return False

            if callback:
                self.on_tick_callbacks.append(callback)

            # Support both OpenAlgo client (subscribe_ltp) and AngelOne adapter (subscribe)
            if hasattr(self.client, "subscribe_ltp"):
                self.client.subscribe_ltp(instruments, on_data_received=self._process_tick)
            elif hasattr(self.client, "subscribe"):
                # Convert instruments list to symbol strings expected by adapter
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.subscribe(symbols)
            else:
                raise RuntimeError("Connected client does not support LTP subscription")

            # Store instruments for re-subscription after reconnect
            self.subscribed_instruments = instruments

            for inst in instruments:
                self.subscribed_symbols.add(f"{inst['exchange']}:{inst['symbol']}")

            logger.info(f"Subscribed to LTP: {len(instruments)} symbols")
            return True

        except Exception as e:
            logger.error(f"LTP subscription failed: {e}")
            if retry_count < 3:
                logger.info(f"Retrying LTP subscription (attempt {retry_count + 1}/3)...")
                time.sleep(self.RECONNECT_DELAY)
                return self.subscribe_ltp(instruments, callback, retry_count + 1)
            return False

    def subscribe_quote(self, instruments, callback=None):
        """Subscribe to quote updates"""
        try:
            if callback:
                self.on_quote_callbacks.append(callback)

            if hasattr(self.client, "subscribe_quote"):
                self.client.subscribe_quote(instruments, on_data_received=self._process_tick)
            elif hasattr(self.client, "subscribe"):
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.subscribe(symbols)
            else:
                raise RuntimeError("Connected client does not support quote subscription")

            logger.info(f"Subscribed to quotes: {len(instruments)} symbols")
            return True

        except Exception as e:
            logger.error(f"Quote subscription failed: {e}")
            return False

    def subscribe_depth(self, instruments, callback=None):
        """Subscribe to market depth updates"""
        try:
            if callback:
                self.on_depth_callbacks.append(callback)

            if hasattr(self.client, "subscribe_depth"):
                self.client.subscribe_depth(instruments, on_data_received=self._process_tick)
            elif hasattr(self.client, "subscribe"):
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.subscribe(symbols)
            else:
                raise RuntimeError("Connected client does not support depth subscription")

            logger.info(f"Subscribed to depth: {len(instruments)} symbols")
            return True

        except Exception as e:
            logger.error(f"Depth subscription failed: {e}")
            return False

    def unsubscribe_ltp(self, instruments):
        """Unsubscribe from LTP updates"""
        try:
            if hasattr(self.client, "unsubscribe_ltp"):
                self.client.unsubscribe_ltp(instruments)
            elif hasattr(self.client, "unsubscribe"):
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.unsubscribe(symbols)
            else:
                logger.warning("Client does not support unsubscribe operation")

            for inst in instruments:
                self.subscribed_symbols.discard(f"{inst['exchange']}:{inst['symbol']}")

            logger.info(f"Unsubscribed from LTP: {len(instruments)} symbols")
            return True

        except Exception as e:
            logger.error(f"LTP unsubscription failed: {e}")
            return False

    def unsubscribe_quote(self, instruments):
        """Unsubscribe from quote updates"""
        try:
            if hasattr(self.client, "unsubscribe_quote"):
                self.client.unsubscribe_quote(instruments)
            elif hasattr(self.client, "unsubscribe"):
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.unsubscribe(symbols)
            else:
                logger.warning("Client does not support unsubscribe operation")
            logger.info(f"Unsubscribed from quotes: {len(instruments)} symbols")
            return True
        except Exception as e:
            logger.error(f"Quote unsubscription failed: {e}")
            return False

    def unsubscribe_depth(self, instruments):
        """Unsubscribe from depth updates"""
        try:
            if hasattr(self.client, "unsubscribe_depth"):
                self.client.unsubscribe_depth(instruments)
            elif hasattr(self.client, "unsubscribe"):
                symbols = [inst.get("symbol") for inst in instruments]
                self.client.unsubscribe(symbols)
            else:
                logger.warning("Client does not support unsubscribe operation")
            logger.info(f"Unsubscribed from depth: {len(instruments)} symbols")
            return True
        except Exception as e:
            logger.error(f"Depth unsubscription failed: {e}")
            return False

    def _on_connect(self, ws, response):
        """WebSocket connection callback"""
        logger.info("WebSocket connection established")
        self.connected = True

    def _on_message(self, ws, message):
        """WebSocket message callback"""
        try:
            data = json.loads(message)
            self._process_tick(data)
        except Exception as e:
            logger.error(f"Error processing message: {e}")

    def _on_error(self, ws, error):
        """WebSocket error callback"""
        logger.error(f"WebSocket error: {error}")

    def _on_close(self, ws):
        """WebSocket close callback"""
        logger.warning("WebSocket connection closed")
        self.connected = False

        if config.WEBSOCKET_ENABLED:
            logger.info(f"Reconnecting in {config.WEBSOCKET_RECONNECT_DELAY} seconds...")
            time.sleep(config.WEBSOCKET_RECONNECT_DELAY)
            self.connect()

    def _process_tick(self, tick):
        """Process incoming tick data"""
        try:
            symbol = tick.get("symbol")
            if not symbol:
                return

            # Record data flow for health monitoring
            self.last_tick_received = time.time()
            self.network_monitor.record_websocket_tick()

            with self.data_lock:
                # Update LTP
                if "ltp" in tick:
                    self.ltp_data[symbol] = {"price": tick["ltp"], "timestamp": datetime.now()}

                # Update quote
                if "bid" in tick or "ask" in tick:
                    self.quote_data[symbol] = {
                        "bid": tick.get("bid"),
                        "ask": tick.get("ask"),
                        "bid_qty": tick.get("bid_qty"),
                        "ask_qty": tick.get("ask_qty"),
                        "timestamp": datetime.now(),
                    }

                # Update depth
                if "depth" in tick:
                    self.depth_data[symbol] = tick["depth"]

                # Store tick
                self.tick_data.append(tick)
                if len(self.tick_data) > 1000:  # Keep last 1000 ticks
                    self.tick_data = self.tick_data[-1000:]

            # Call registered callbacks
            self._trigger_callbacks(tick)

            if "ltp" in tick:
                logger.debug(f"{tick.get('symbol')}: {tick.get('ltp')} [{tick.get('source', 'WEBSOCKET')}]")
                # Persist tick to CSV
                self._write_tick_to_csv(tick)

        except Exception as e:
            logger.error(f"Error processing tick: {e}")

    def _trigger_callbacks(self, tick):
        """Trigger registered callbacks"""
        try:
            for callback in self.on_tick_callbacks:
                callback(tick)

            if "bid" in tick or "ask" in tick:
                for callback in self.on_quote_callbacks:
                    callback(tick)

            if "depth" in tick:
                for callback in self.on_depth_callbacks:
                    callback(tick)

        except Exception as e:
            logger.error(f"Error triggering callbacks: {e}")

    def register_callback(self, callback_type, callback_func):
        """Register callback function for data updates"""
        if callback_type == "tick":
            self.on_tick_callbacks.append(callback_func)
        elif callback_type == "quote":
            self.on_quote_callbacks.append(callback_func)
        elif callback_type == "depth":
            self.on_depth_callbacks.append(callback_func)
        else:
            logger.warning(f"Unknown callback type: {callback_type}")

    def get_ltp(self, symbol):
        """Get last traded price for symbol"""
        with self.data_lock:
            return self.ltp_data.get(symbol, {}).get("price")

    def get_ltp_with_timestamp(self, symbol):
        """Get LTP with timestamp for freshness checking

        Returns:
            {'price': float, 'timestamp': datetime} or None
        """
        with self.data_lock:
            ltp_data = self.ltp_data.get(symbol)
            if not ltp_data:
                return None
            return {"price": ltp_data.get("price"), "timestamp": ltp_data.get("timestamp")}

    def get_quote(self, symbol):
        """Get quote data for symbol"""
        with self.data_lock:
            return self.quote_data.get(symbol)

    def get_depth(self, symbol):
        """Get market depth for symbol"""
        with self.data_lock:
            return self.depth_data.get(symbol)

    def is_connected(self):
        """Check if WebSocket is connected"""
        return self.connected

    def check_broker_connection(self):
        """Check if broker is connected in OpenAlgo"""
        try:
            if not hasattr(self, "client") or not self.client:
                logger.warning("Client not initialized")
                return False

            # Try to get analyzer status which includes broker info
            # Prefer analyzerstatus (OpenAlgo) if present
            if hasattr(self.client, "analyzerstatus"):
                try:
                    status = self.client.analyzerstatus()
                    self.network_monitor.record_api_call(success=True)
                    logger.info(f"OpenAlgo Status: {status}")
                    return True
                except Exception as e:
                    self.network_monitor.record_api_call(success=False)
                    logger.debug(f"Analyzer status check failed: {e}")

            # Try broker-specific quick checks: quotes() or get_ltp()
            try:
                if hasattr(self.client, "quotes"):
                    quotes = self.client.quotes(symbol="NIFTY", exchange="NSE_INDEX")
                    if quotes and quotes.get("status") == "success":
                        self.network_monitor.record_api_call(success=True)
                        logger.info("✅ Broker connection verified via REST API")
                        return True
                elif hasattr(self.client, "get_ltp"):
                    l = self.client.get_ltp("NIFTY")
                    if l and l.get("ltp") is not None:
                        self.network_monitor.record_api_call(success=True)
                        logger.info("✅ Broker connection verified via get_ltp()")
                        return True
            except Exception as e:
                self.network_monitor.record_api_call(success=False)
                logger.warning(f"Broker check failed: {e}")
                return False

        except Exception as e:
            logger.error(f"Error checking broker connection: {e}")
            return False

    def start_rest_polling(self, instruments):
        """Start REST API polling as fallback when WebSocket not broadcasting"""
        if self.use_rest_polling and self.polling_thread and self.polling_thread.is_alive():
            logger.info("REST API polling already active")
            return True

        logger.warning("⚠️ WebSocket not receiving data! Starting REST API polling fallback...")
        self.use_rest_polling = True

        # Store symbols for polling
        self.polling_symbols = instruments

        # Start polling thread
        self.polling_thread = Thread(target=self._polling_loop, daemon=True, name="REST-Polling")
        self.polling_thread.start()
        logger.info("✅ REST API polling started as fallback")
        return True

    def _polling_loop(self):
        """Continuously poll REST API for LTP updates"""
        try:
            while self.use_rest_polling and not self.stop_reconnect.is_set():
                try:
                    for inst in self.polling_symbols:
                        symbol = inst.get("symbol")
                        exchange = inst.get("exchange", "NSE_INDEX")

                        # Use NSE_INDEX for NIFTY/indices
                        if "NIFTY" in symbol or "BANK" in symbol:
                            exchange = "NSE_INDEX"

                        # Poll every 1.5 seconds per symbol
                        current_time = time.time()
                        if symbol not in self.last_polled_time:
                            self.last_polled_time[symbol] = 0

                        time_diff = current_time - self.last_polled_time[symbol]
                        if time_diff >= self.polling_interval:
                            try:
                                # Support multiple client implementations
                                if hasattr(self.client, "quotes"):
                                    response = self.client.quotes(symbol=symbol, exchange=exchange)
                                    if response and response.get("status") == "success":
                                        self.network_monitor.record_api_call(success=True)
                                        data = response.get("data", {})
                                        tick = {
                                            "symbol": symbol,
                                            "ltp": data.get("ltp"),
                                            "bid": data.get("bid"),
                                            "ask": data.get("ask"),
                                            "high": data.get("high"),
                                            "low": data.get("low"),
                                            "open": data.get("open"),
                                            "volume": data.get("volume"),
                                            "timestamp": datetime.now(),
                                            "source": "REST_POLLING",
                                        }
                                        self._process_tick(tick)
                                        self.last_polled_time[symbol] = current_time
                                elif hasattr(self.client, "get_ltp"):
                                    data = self.client.get_ltp(symbol)
                                    if data and data.get("ltp") is not None:
                                        self.network_monitor.record_api_call(success=True)
                                        tick = {
                                            "symbol": symbol,
                                            "ltp": data.get("ltp"),
                                            "bid": data.get("bid"),
                                            "ask": data.get("ask"),
                                            "timestamp": datetime.now(),
                                            "source": "REST_POLLING",
                                        }
                                        self._process_tick(tick)
                                        self.last_polled_time[symbol] = current_time
                                else:
                                    logger.error("Client does not provide polling API (quotes/get_ltp)")

                            except Exception as e:
                                self.network_monitor.record_api_call(success=False)
                                logger.error(f"Error polling {symbol}: {e}")

                    time.sleep(0.5)  # Small sleep to avoid busy waiting

                except Exception as e:
                    logger.error(f"Polling loop error: {e}")
                    time.sleep(self.RECONNECT_DELAY)

        except Exception as e:
            logger.error(f"REST polling stopped: {e}")
            self.use_rest_polling = False

    def stop_rest_polling(self):
        """Stop REST API polling"""
        self.use_rest_polling = False
        logger.info("REST API polling stopped")
