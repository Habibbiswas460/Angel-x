import json
import pytest
from unittest.mock import MagicMock, patch

from src.integrations.websocket.websocket_client import WebSocketClient, SubscriptionMode


class MockWS:
    """Mock WebSocket for testing subscription payloads without network."""
    def __init__(self):
        self.sent = []
    
    def send(self, payload):
        self.sent.append(payload)


class TestWebSocketClient:
    
    def test_initialization(self):
        client = WebSocketClient(api_key="test_key", client_code="test_code", feed_token="test_token")
        assert client.api_key == "test_key"
        assert client.client_code == "test_code"
        assert client.feed_token == "test_token"
        assert not client.is_connected
    
    def test_exchange_code_mapping(self):
        client = WebSocketClient(api_key="k", client_code="c", feed_token="t")
        assert client._get_exchange_code("NSE") == 1
        assert client._get_exchange_code("NFO") == 2
        assert client._get_exchange_code("BSE") == 3
    
    def test_subscription_payload_structure(self):
        """Test that subscription payload is built correctly."""
        client = WebSocketClient(api_key="k", client_code="c", feed_token="t")
        client.is_connected = True
        client.ws = MockWS()
        
        tokens = ["99926000", "99926009"]
        client.subscribe(tokens=tokens, mode=SubscriptionMode.LTP, exchange="NFO")
        
        assert len(client.ws.sent) == 1
        payload = json.loads(client.ws.sent[0])
        
        assert payload["action"] == 1
        assert payload["params"]["mode"] == SubscriptionMode.LTP.value
        assert len(payload["params"]["tokenlist"]) == len(tokens)
    
    def test_subscription_count(self):
        """Test that subscription count is tracked correctly."""
        client = WebSocketClient(api_key="k", client_code="c", feed_token="t")
        client.is_connected = True
        client.ws = MockWS()
        
        client.subscribe(tokens=["99926000"], mode=SubscriptionMode.LTP, exchange="NSE")
        assert client.get_subscription_count() == 1
        
        client.subscribe(tokens=["99926009"], mode=SubscriptionMode.LTP, exchange="NSE")
        assert client.get_subscription_count() == 2


class TestSubscriptionMode:
    
    def test_subscription_mode_values(self):
        """Test SubscriptionMode enum values."""
        assert SubscriptionMode.LTP.value == 1
        assert SubscriptionMode.QUOTE.value == 2
        assert SubscriptionMode.SNAP_QUOTE.value == 3