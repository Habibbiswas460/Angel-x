"""
AngelOne SmartAPI client adapter with polling-based tick delivery.

This implementation logs into SmartAPI (when credentials are present) and
publishes LTP ticks via a lightweight polling loop. If credentials are
missing, it falls back to a simulated feed so the rest of the stack keeps
running in paper/demo mode.
"""
import os
import time
import random
import threading
from datetime import datetime
from typing import Any, Dict, List, Optional

# SmartAPI WebSocket (best-effort import; falls back to REST polling if unavailable)
try:  # SmartAPI v2 (preferred)
    from SmartApi.smartWebSocketV2 import SmartWebSocketV2, Mode  # type: ignore
except Exception:  # pragma: no cover
    try:
        from smartapi.smartWebSocketV2 import SmartWebSocketV2, Mode  # type: ignore
    except Exception:  # pragma: no cover
        SmartWebSocketV2 = None  # type: ignore
        Mode = None  # type: ignore

from config import config
from src.utils.logger import StrategyLogger
from src.integrations.angelone.smartapi_integration import SmartAPIClient

logger = StrategyLogger.get_logger(__name__)


class AngelOneClient:
    """AngelOne client that provides LTP ticks via SmartAPI REST polling."""

    POLL_INTERVAL = 1.0  # seconds
    INDEX_TOKEN_MAP = {
        "NIFTY": {
            "token": "99926000",
            "exchange": "NSE",
            "exchange_type": 1,
            "tradingsymbol": "NIFTY",
        },
        "BANKNIFTY": {
            "token": "99926005",
            "exchange": "NSE",
            "exchange_type": 1,
            "tradingsymbol": "BANKNIFTY",
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        ws_url: Optional[str] = None,
        client_id: Optional[str] = None,
        config_obj: Optional[Any] = None,
        **_: Any,
    ):
        self.api_key = api_key or os.getenv("BROKER_API_KEY", "") or os.getenv("ANGELONE_API_KEY", "")
        self.ws_url = ws_url or os.getenv("BROKER_WS_URL", "")
        self.client_id = client_id or os.getenv("BROKER_CLIENT_ID", "") or os.getenv("ANGELONE_CLIENT_CODE", "")
        self.password = os.getenv("ANGELONE_PASSWORD", "")
        self.totp_secret = os.getenv("ANGELONE_TOTP_SECRET", "")
        self.paper_trading = getattr(config_obj, "PAPER_TRADING", getattr(config, "PAPER_TRADING", True))

        self.connected = False
        self._subscriptions: List[Dict[str, Any]] = []
        self._on_tick = None
        self._stop_poll = threading.Event()
        self._poll_thread: Optional[threading.Thread] = None
        self.smart_client: Optional[SmartAPIClient] = None
        self.ws_client = None
        self._ws_connected = False
        self._ws_tokens: Dict[str, str] = {}  # token -> symbol mapping

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    def _ensure_smart_client(self) -> bool:
        if self.smart_client:
            return True

        if not (self.api_key and self.client_id and self.password and self.totp_secret):
            logger.warning("AngelOne credentials missing → using simulated ticks")
            return False

        try:
            self.smart_client = SmartAPIClient(
                api_key=self.api_key,
                client_code=self.client_id,
                password=self.password,
                totp_secret=self.totp_secret,
            )
            return True
        except Exception as exc:
            logger.error(f"Failed to initialize SmartAPI client: {exc}")
            self.smart_client = None
            return False

    def login(self) -> bool:
        if not self._ensure_smart_client():
            self.connected = True  # Simulated path
            return True

        ok = self.smart_client.login()
        self.connected = bool(ok)
        return bool(ok)

    def connect_ws(self) -> bool:
        """Login to SmartAPI and prepare websocket; fallback to polling if unavailable."""
        try:
            if self.connected:
                return True

            ok = self.login()
            if not ok:
                logger.error("AngelOne SmartAPI login failed")
                return False

            # Attempt websocket init if SmartWebSocketV2 is available
            if SmartWebSocketV2 and Mode and self.smart_client and self.smart_client.feed_token:
                try:
                    self._init_websocket()
                    logger.info("AngelOne SmartAPI session ready (websocket preferred)")
                except Exception as ws_exc:  # pragma: no cover
                    logger.warning(f"WebSocket init failed, using REST polling fallback: {ws_exc}")
                    self.ws_client = None
            else:
                logger.info("SmartAPI WebSocket not available; using REST polling")

            self.connected = True
            return True
        except Exception as exc:
            logger.error(f"connect_ws failed: {exc}")
            return False

    def disconnect(self) -> None:
        self._stop_poll.set()
        if self._poll_thread and self._poll_thread.is_alive():
            self._poll_thread.join(timeout=1)
        try:
            if self.ws_client:
                self.ws_client.close_connection()
        except Exception as exc:  # pragma: no cover - network dependent
            logger.debug(f"WebSocket close ignored: {exc}")
        self.connected = False
        try:
            if self.smart_client:
                self.smart_client.logout()
        except Exception as exc:
            logger.debug(f"Logout ignored: {exc}")

    close = disconnect

    # ------------------------------------------------------------------
    # Subscriptions / data
    # ------------------------------------------------------------------
    def subscribe(self, symbols: List[str]) -> None:
        self._subscriptions = [{"symbol": s, "exchange": "NSE_INDEX"} for s in symbols]
        self.subscribe_ltp(self._subscriptions)

    def subscribe_ltp(self, instruments: List[Dict[str, Any]], on_data_received=None) -> None:
        if not self.connected:
            self.connect_ws()

        if on_data_received:
            self._on_tick = on_data_received

        self._subscriptions = instruments
        self._stop_poll.clear()

        # Prefer WebSocket if available
        if self.ws_client and self._ws_connected:
            self._subscribe_ws(instruments)
            return

        # Fallback to REST polling
        if self._poll_thread and self._poll_thread.is_alive():
            logger.debug("Polling thread already running")
            return

        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="AngelOne-Polling",
        )
        self._poll_thread.start()
        logger.info(f"Subscribed to {len(instruments)} instruments (SmartAPI REST polling)")

    def unsubscribe(self, symbols: List[str]) -> None:
        remaining = []
        for inst in self._subscriptions:
            if inst.get("symbol") not in symbols:
                remaining.append(inst)
        self._subscriptions = remaining
        if not remaining:
            self._stop_poll.set()

    def unsubscribe_ltp(self, instruments: List[Dict[str, Any]]) -> None:
        symbols = [inst.get("symbol") for inst in instruments]
        self.unsubscribe(symbols)

    # ------------------------------------------------------------------
    # WebSocket helpers (SmartAPI V2)
    # ------------------------------------------------------------------
    def _init_websocket(self) -> None:
        if not SmartWebSocketV2:
            raise RuntimeError("SmartWebSocketV2 not available")
        if not self.smart_client or not self.smart_client.feed_token:
            raise RuntimeError("Missing feed token for websocket")

        # Initialize websocket client
        self.ws_client = SmartWebSocketV2(
            api_key=self.api_key,
            client_code=self.client_id,
            feed_token=str(self.smart_client.feed_token),
        )

        # Register callbacks
        self.ws_client.on_open = self._ws_on_open
        self.ws_client.on_data = self._ws_on_data
        self.ws_client.on_error = self._ws_on_error
        self.ws_client.on_close = self._ws_on_close

        logger.info("SmartAPI WebSocket initialized (v2)")

        # Start websocket listener in background
        threading.Thread(target=self.ws_client.connect, daemon=True, name="AngelOne-WS").start()

    def _ws_on_open(self):
        self._ws_connected = True
        logger.info("SmartAPI WebSocket connected")
        if self._subscriptions:
            try:
                self._subscribe_ws(self._subscriptions)
            except Exception as exc:
                logger.warning(f"WebSocket subscribe on open failed: {exc}")

    def _ws_on_close(self, code=None, reason=None):  # pragma: no cover - network dependent
        self._ws_connected = False
        logger.warning(f"SmartAPI WebSocket closed (code={code}, reason={reason})")

    def _ws_on_error(self, error):  # pragma: no cover - network dependent
        logger.error(f"SmartAPI WebSocket error: {error}")

    def _ws_on_data(self, message: Dict[str, Any]):
        """Handle incoming WS ticks and forward to DataFeed."""
        try:
            if not message:
                return

            # SmartAPI V2 delivers dict with 'token' and market data fields
            token = str(message.get("token")) if message.get("token") is not None else None
            symbol = self._ws_tokens.get(token) if token else None
            if not symbol:
                return

            ltp = message.get("last_traded_price") or message.get("ltp")
            bid = message.get("best_bid_price") or message.get("bid_price")
            ask = message.get("best_ask_price") or message.get("ask_price")

            tick = {
                "symbol": symbol,
                "ltp": ltp,
                "bid": bid,
                "ask": ask,
                "timestamp": datetime.now(),
                "source": "SMARTAPI_WS",
            }

            if self._on_tick:
                self._on_tick(tick)
        except Exception as exc:
            logger.error(f"WebSocket tick handling failed: {exc}")

    def _prepare_ws_tokens(self, instruments: List[Dict[str, Any]]) -> List[str]:
        """Resolve instrument tokens into websocket token strings."""
        token_strings: List[str] = []
        self._ws_tokens.clear()

        exchange_type_map = {
            1: "nse_cm",   # cash
            2: "nse_fo",   # futures/options
            3: "bse_cm",
            4: "bse_fo",
        }

        for inst in instruments:
            symbol = inst.get("symbol")
            exchange = inst.get("exchange", "NSE")
            resolved = self._resolve_symbol(symbol, exchange)
            if not resolved:
                continue

            token = str(resolved.get("token"))
            exch_type = resolved.get("exchange_type", 1)
            exch_prefix = exchange_type_map.get(exch_type, "nse_cm")
            ws_token = f"{exch_prefix}|{token}"

            token_strings.append(ws_token)
            self._ws_tokens[token] = symbol

        return token_strings

    def _subscribe_ws(self, instruments: List[Dict[str, Any]]) -> None:
        if not self.ws_client or not self._ws_connected:
            logger.warning("WebSocket not connected; falling back to polling")
            self._start_polling()
            return

        tokens = self._prepare_ws_tokens(instruments)
        if not tokens:
            logger.warning("No tokens resolved for websocket; using polling")
            self._start_polling()
            return

        try:
            # Mode.LTP provides LTP ticks with best bid/ask
            self.ws_client.subscribe(correlation_id="angelx-ltp", mode=Mode.LTP, token_list=tokens)
            logger.info(f"Subscribed to {len(tokens)} tokens via SmartAPI WebSocket")
        except Exception as exc:  # pragma: no cover - network dependent
            logger.warning(f"WebSocket subscribe failed; switching to polling: {exc}")
            self._start_polling()

    def _start_polling(self) -> None:
        if self._poll_thread and self._poll_thread.is_alive():
            return
        self._poll_thread = threading.Thread(
            target=self._poll_loop,
            daemon=True,
            name="AngelOne-Polling",
        )
        self._poll_thread.start()

    # ------------------------------------------------------------------
    # Polling loop
    # ------------------------------------------------------------------
    def _poll_loop(self) -> None:
        while not self._stop_poll.is_set():
            for inst in list(self._subscriptions):
                tick = self._fetch_ltp_tick(inst)
                if tick and self._on_tick:
                    try:
                        self._on_tick(tick)
                    except Exception as exc:
                        logger.error(f"Tick callback error: {exc}")
            time.sleep(self.POLL_INTERVAL)

    def _fetch_ltp_tick(self, instrument: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        symbol = instrument.get("symbol")
        if not symbol:
            return None

        exchange = instrument.get("exchange", "NSE")
        ltp_info = self.get_ltp(symbol, exchange)
        if not ltp_info or ltp_info.get("ltp") is None:
            return None

        return {
            "symbol": symbol,
            "ltp": ltp_info.get("ltp"),
            "bid": ltp_info.get("bid"),
            "ask": ltp_info.get("ask"),
            "timestamp": datetime.now(),
            "source": ltp_info.get("source", "SMARTAPI_REST"),
        }

    # ------------------------------------------------------------------
    # REST helpers
    # ------------------------------------------------------------------
    def get_ltp(self, symbol: str, exchange: str = "NSE") -> Dict[str, Any]:
        """Fetch LTP via SmartAPI or return simulated data."""
        try:
            if not self._ensure_smart_client():
                ltp = 20000.0 + random.uniform(-5, 5)
                return {
                    "symbol": symbol,
                    "ltp": round(ltp, 2),
                    "timestamp": int(time.time()),
                    "source": "SIMULATED",
                }

            if not self.smart_client.auth_token:
                self.smart_client.login()

            resolved = self._resolve_symbol(symbol, exchange)
            if not resolved:
                logger.warning(f"Could not resolve token for {symbol}; using simulated tick")
                ltp = 20000.0 + random.uniform(-5, 5)
                return {
                    "symbol": symbol,
                    "ltp": round(ltp, 2),
                    "timestamp": int(time.time()),
                    "source": "SIMULATED",
                }

            data = self.smart_client.get_ltp_data(
                exchange=resolved.get("exchange", "NSE"),
                trading_symbol=resolved.get("tradingsymbol", symbol),
                token=resolved.get("token"),
            )

            if not data:
                return {}

            ltp = data.get("ltp") or data.get("last_price") or data.get("close")
            return {
                "symbol": symbol,
                "ltp": float(ltp) if ltp is not None else None,
                "bid": data.get("bid"),
                "ask": data.get("ask"),
                "timestamp": int(time.time()),
                "source": "SMARTAPI_REST",
            }
        except Exception as exc:
            logger.error(f"get_ltp({symbol}) failed: {exc}")
            return {}

    def _resolve_symbol(self, symbol: str, exchange: str) -> Optional[Dict[str, Any]]:
        try:
            sym = symbol.upper()
            if sym in self.INDEX_TOKEN_MAP:
                return self.INDEX_TOKEN_MAP[sym]

            if not self.smart_client:
                return None

            search_exchange = "NFO" if "NFO" in exchange or "FO" in exchange else "NSE"
            results = self.smart_client.search_scrip(exchange=search_exchange, searchtext=sym)
            if results:
                entry = results[0]
                return {
                    "token": entry.get("symboltoken") or entry.get("token"),
                    "exchange": entry.get("exchange", search_exchange),
                    "tradingsymbol": entry.get("tradingSymbol") or entry.get("tradingsymbol") or sym,
                    "exchange_type": entry.get("exchangeType", 1),
                }
            return None
        except Exception as exc:
            logger.error(f"Symbol resolve failed for {symbol}: {exc}")
            return None

    def get_option_chain(self, underlying: str) -> Dict[str, Any]:
        now = datetime.now()
        return {
            "underlying": underlying,
            "expiry_dates": [(now.strftime("%d%b%y"))],
            "strikes": [round(20000 + i * 50) for i in range(-3, 4)],
            "data": {},
        }

    # ------------------------------------------------------------------
    # Orders / execution (simulated unless extended)
    # ------------------------------------------------------------------
    def place_order(self, order_payload: Dict[str, Any]) -> Dict[str, Any]:
        if getattr(config, "PAPER_TRADING", True):
            oid = f"PAPER_{int(time.time())}_{random.randint(1000, 9999)}"
            return {"status": "success", "orderid": oid, "payload": order_payload}
        oid = f"LIVE_{int(time.time())}_{random.randint(1000, 9999)}"
        return {"status": "success", "orderid": oid, "payload": order_payload}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        return {"status": "success", "orderid": order_id}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        return {"orderid": order_id, "status": "filled", "filled_qty": 1}

    def get_all_orders(self) -> List[Dict[str, Any]]:
        return []

    def get_all_positions(self) -> List[Dict[str, Any]]:
        return []


__all__ = ["AngelOneClient"]
