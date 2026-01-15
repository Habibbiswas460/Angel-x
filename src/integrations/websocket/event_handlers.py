"""
Event Handlers for WebSocket Data

Handles different types of market events:
- Price updates
- Greeks changes
- Order book updates
- Trade executions
"""

from typing import Dict, Callable, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

from src.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


class EventHandler(ABC):
    """Base class for event handlers"""

    def __init__(self, name: str = "BaseHandler"):
        self.name = name
        self.event_count = 0
        self.last_event_time: Optional[datetime] = None

    @abstractmethod
    def handle(self, data: Dict):
        """Handle event data"""
        pass

    def _record_event(self):
        """Record event statistics"""
        self.event_count += 1
        self.last_event_time = datetime.now()


class PriceUpdateHandler(EventHandler):
    """
    Handles price update events

    Triggers:
    - Price threshold alerts
    - Moving average crossovers
    - Breakout detection
    """

    def __init__(self, on_price_change: Optional[Callable] = None, price_threshold: float = 0.5):  # % change threshold
        super().__init__("PriceUpdateHandler")
        self.on_price_change = on_price_change
        self.price_threshold = price_threshold
        self.last_prices: Dict[str, float] = {}

    def handle(self, data: Dict):
        """Handle price update"""
        try:
            token = data.get("token")
            ltp = data.get("ltp")

            if not token or ltp is None:
                return

            # Check for significant price change
            if token in self.last_prices:
                last_price = self.last_prices[token]
                change_pct = ((ltp - last_price) / last_price) * 100

                if abs(change_pct) >= self.price_threshold:
                    logger.info(f"Price alert: {token} changed {change_pct:.2f}% " f"({last_price:.2f} → {ltp:.2f})")

                    if self.on_price_change:
                        self.on_price_change(
                            {
                                "token": token,
                                "old_price": last_price,
                                "new_price": ltp,
                                "change_percent": change_pct,
                                "timestamp": data.get("timestamp"),
                            }
                        )

            # Update last price
            self.last_prices[token] = ltp
            self._record_event()

        except Exception as e:
            logger.error(f"PriceUpdateHandler error: {e}")


class GreeksUpdateHandler(EventHandler):
    """
    Handles Greeks update events

    Monitors:
    - Delta changes (directional risk)
    - Gamma exposure
    - Theta decay
    - Vega sensitivity
    """

    def __init__(
        self, on_greeks_alert: Optional[Callable] = None, delta_threshold: float = 0.1, gamma_threshold: float = 0.05
    ):
        super().__init__("GreeksUpdateHandler")
        self.on_greeks_alert = on_greeks_alert
        self.delta_threshold = delta_threshold
        self.gamma_threshold = gamma_threshold
        self.last_greeks: Dict[str, Dict] = {}

    def handle(self, data: Dict):
        """Handle Greeks update"""
        try:
            token = data.get("token")
            delta = data.get("delta")
            gamma = data.get("gamma")

            if not token:
                return

            # Check for significant Greeks changes
            if token in self.last_greeks:
                last = self.last_greeks[token]

                # Delta change alert
                if delta is not None and last.get("delta") is not None:
                    delta_change = abs(delta - last["delta"])
                    if delta_change >= self.delta_threshold:
                        logger.warning(f"Delta alert: {token} delta changed by {delta_change:.3f}")

                # Gamma change alert
                if gamma is not None and last.get("gamma") is not None:
                    gamma_change = abs(gamma - last["gamma"])
                    if gamma_change >= self.gamma_threshold:
                        logger.warning(f"Gamma alert: {token} gamma changed by {gamma_change:.4f}")

            # Update last Greeks
            self.last_greeks[token] = {
                "delta": delta,
                "gamma": gamma,
                "theta": data.get("theta"),
                "vega": data.get("vega"),
                "iv": data.get("iv"),
                "timestamp": datetime.now(),
            }

            self._record_event()

        except Exception as e:
            logger.error(f"GreeksUpdateHandler error: {e}")


class OrderBookHandler(EventHandler):
    """
    Handles order book (market depth) events

    Monitors:
    - Bid/ask spread changes
    - Liquidity conditions
    - Order imbalances
    """

    def __init__(self, on_spread_alert: Optional[Callable] = None, spread_threshold: float = 1.0):  # % spread threshold
        super().__init__("OrderBookHandler")
        self.on_spread_alert = on_spread_alert
        self.spread_threshold = spread_threshold

    def handle(self, data: Dict):
        """Handle order book update"""
        try:
            token = data.get("token")
            bid = data.get("bid", [])
            ask = data.get("ask", [])

            if not token or not bid or not ask:
                return

            # Calculate best bid/ask
            best_bid = bid[0]["price"] if bid else 0
            best_ask = ask[0]["price"] if ask else 0

            if best_bid > 0 and best_ask > 0:
                # Calculate spread
                spread = ((best_ask - best_bid) / best_bid) * 100

                if spread >= self.spread_threshold:
                    logger.warning(
                        f"Wide spread alert: {token} spread = {spread:.2f}% " f"(Bid: {best_bid}, Ask: {best_ask})"
                    )

                    if self.on_spread_alert:
                        self.on_spread_alert(
                            {
                                "token": token,
                                "bid": best_bid,
                                "ask": best_ask,
                                "spread_percent": spread,
                                "timestamp": datetime.now(),
                            }
                        )

            self._record_event()

        except Exception as e:
            logger.error(f"OrderBookHandler error: {e}")


class VolumeHandler(EventHandler):
    """
    Handles volume spike events

    Detects:
    - Unusual volume activity
    - Volume breakouts
    - Smart money flows
    """

    def __init__(
        self, on_volume_spike: Optional[Callable] = None, spike_multiplier: float = 2.0  # Volume spike threshold
    ):
        super().__init__("VolumeHandler")
        self.on_volume_spike = on_volume_spike
        self.spike_multiplier = spike_multiplier
        self.avg_volumes: Dict[str, float] = {}
        self.volume_history: Dict[str, List[int]] = {}

    def handle(self, data: Dict):
        """Handle volume update"""
        try:
            token = data.get("token")
            volume = data.get("volume")

            if not token or volume is None:
                return

            # Track volume history
            if token not in self.volume_history:
                self.volume_history[token] = []

            self.volume_history[token].append(volume)

            # Keep last 100 data points
            if len(self.volume_history[token]) > 100:
                self.volume_history[token].pop(0)

            # Calculate average volume
            if len(self.volume_history[token]) >= 20:
                avg_volume = sum(self.volume_history[token][-20:]) / 20
                self.avg_volumes[token] = avg_volume

                # Check for volume spike
                if volume > avg_volume * self.spike_multiplier:
                    logger.info(f"Volume spike: {token} volume {volume} " f"({volume/avg_volume:.1f}x average)")

                    if self.on_volume_spike:
                        self.on_volume_spike(
                            {
                                "token": token,
                                "volume": volume,
                                "avg_volume": avg_volume,
                                "multiplier": volume / avg_volume,
                                "timestamp": datetime.now(),
                            }
                        )

            self._record_event()

        except Exception as e:
            logger.error(f"VolumeHandler error: {e}")


class CompositeEventHandler:
    """
    Composite handler that manages multiple event handlers
    """

    def __init__(self):
        self.handlers: List[EventHandler] = []

    def add_handler(self, handler: EventHandler):
        """Add an event handler"""
        self.handlers.append(handler)
        logger.info(f"Added handler: {handler.name}")

    def remove_handler(self, handler: EventHandler):
        """Remove an event handler"""
        if handler in self.handlers:
            self.handlers.remove(handler)
            logger.info(f"Removed handler: {handler.name}")

    def handle(self, data: Dict):
        """Dispatch event to all handlers"""
        for handler in self.handlers:
            try:
                handler.handle(data)
            except Exception as e:
                logger.error(f"Handler {handler.name} error: {e}")

    def get_statistics(self) -> Dict:
        """Get statistics from all handlers"""
        stats = {}
        for handler in self.handlers:
            stats[handler.name] = {"event_count": handler.event_count, "last_event_time": handler.last_event_time}
        return stats
