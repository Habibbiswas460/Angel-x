"""
Broker Integration Module
Connects real broker (AngelOne) with trading system via WebSocket
"""

from typing import Optional, Callable, Dict, List
import logging
from datetime import datetime

from config import config
from src.utils.logger import StrategyLogger
from .websocket.websocket_client import WebSocketClient, SubscriptionMode
from .websocket.stream_manager import StreamManager

logger = StrategyLogger.get_logger(__name__)


class BrokerIntegration:
    """Live broker connection manager"""

    def __init__(self):
        self.ws_client: Optional[WebSocketClient] = None
        self.stream_manager: Optional[StreamManager] = None
        self.is_connected = False
        self.api_key = getattr(config, "ANGELONE_API_KEY", None)
        self.client_code = getattr(config, "ANGELONE_CLIENT_CODE", None)
        self.feed_token = getattr(config, "ANGELONE_FEED_TOKEN", None)

        logger.info("BrokerIntegration initialized")

    def connect(self) -> bool:
        """Connect to broker WebSocket"""
        if not all([self.api_key, self.client_code, self.feed_token]):
            logger.warning("Broker credentials missing—running in fallback mode")
            return False

        try:
            logger.info("Connecting to AngelOne broker...")

            # Create WebSocket client
            self.ws_client = WebSocketClient(
                api_key=self.api_key, client_code=self.client_code, feed_token=self.feed_token
            )

            # Create stream manager
            self.stream_manager = StreamManager(self.ws_client)

            # Connect
            success = self.ws_client.connect()
            if success:
                self.is_connected = True
                logger.info("✓ Connected to broker WebSocket")
                return True
            else:
                logger.error("Failed to connect to broker")
                return False

        except Exception as e:
            logger.error(f"Broker connection error: {e}")
            return False

    def subscribe_nifty_banknifty(self):
        """Subscribe to index ticks"""
        if not self.stream_manager:
            logger.warning("Stream manager not initialized")
            return

        self.stream_manager.subscribe_nifty_banknifty(mode=SubscriptionMode.QUOTE)
        logger.info("Subscribed to NIFTY and BANKNIFTY")

    def subscribe_option_chain(self, underlying: str, expiry: str, strikes: List[int]):
        """Subscribe to option chain for a symbol"""
        if not self.stream_manager:
            logger.warning("Stream manager not initialized")
            return

        self.stream_manager.subscribe_option_chain(
            underlying=underlying, expiry=expiry, strikes=strikes, mode=SubscriptionMode.QUOTE
        )
        logger.info(f"Subscribed to {underlying} option chain")

    def on_tick(self, callback: Callable):
        """Register tick callback"""
        if self.stream_manager:
            self.stream_manager.on_tick(callback)

    def on_greeks(self, callback: Callable):
        """Register Greeks update callback"""
        if self.stream_manager:
            self.stream_manager.on_greeks_update(callback)

    def get_latest_price(self, token: str) -> Optional[float]:
        """Get latest price for token"""
        if self.stream_manager:
            return self.stream_manager.get_latest_price(token)
        return None

    def get_stats(self) -> Dict:
        """Get connection statistics"""
        if self.stream_manager:
            return self.stream_manager.get_statistics()
        return {"connected": self.is_connected}

    def disconnect(self):
        """Disconnect from broker"""
        if self.ws_client:
            self.ws_client.disconnect()
            self.is_connected = False
            logger.info("✓ Disconnected from broker")


# Global broker integration
_broker = None


def get_broker() -> BrokerIntegration:
    """Get or create global broker integration"""
    global _broker
    if _broker is None:
        _broker = BrokerIntegration()
    return _broker
