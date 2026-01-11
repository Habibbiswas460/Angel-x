#!/usr/bin/env python3
"""Quick validation tests for WebSocket, strategies, ML"""

from src.integrations.websocket.websocket_client import WebSocketClient, SubscriptionMode
from src.ml.integration import MLIntegration
import pandas as pd
import numpy as np

print("=" * 60)
print("QUICK VALIDATION TESTS")
print("=" * 60)

# Test 1: WebSocket client initialization
try:
    client = WebSocketClient(api_key='test', client_code='test', feed_token='test')
    print("✓ Test 1: WebSocket client initialized")
except Exception as e:
    print(f"✗ Test 1 failed: {e}")
    exit(1)

# Test 2: Exchange code mapping
try:
    assert client._get_exchange_code('NSE') == 1
    assert client._get_exchange_code('NFO') == 2
    assert client._get_exchange_code('BSE') == 3
    print("✓ Test 2: Exchange code mapping works")
except Exception as e:
    print(f"✗ Test 2 failed: {e}")
    exit(1)

# Test 3: ML integration initialization
try:
    ml = MLIntegration()
    print("✓ Test 3: ML integration initialized")
except Exception as e:
    print(f"✗ Test 3 failed: {e}")
    exit(1)

# Test 4: ML train on empty data (should skip)
try:
    result = ml.train(pd.DataFrame())
    assert result.get('skipped') == True, "Train should skip on empty data"
    print("✓ Test 4: ML train skips on empty data")
except Exception as e:
    print(f"✗ Test 4 failed: {e}")
    exit(1)

# Test 5: ML infer with no models (should return empty)
try:
    result = ml.infer(pd.DataFrame())
    assert result.get('skipped') == True, "Infer should return empty when models missing"
    print("✓ Test 5: ML infer returns empty when models missing")
except Exception as e:
    print(f"✗ Test 5 failed: {e}")
    exit(1)

# Test 6: Subscription mode enum
try:
    assert SubscriptionMode.LTP.value == 1
    assert SubscriptionMode.QUOTE.value == 2
    assert SubscriptionMode.SNAP_QUOTE.value == 3
    print("✓ Test 6: SubscriptionMode enum values correct")
except Exception as e:
    print(f"✗ Test 6 failed: {e}")
    exit(1)

print("=" * 60)
print("✓ ALL TESTS PASSED")
print("=" * 60)
