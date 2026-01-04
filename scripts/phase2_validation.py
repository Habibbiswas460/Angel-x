#!/usr/bin/env python3
"""Phase 2 Validation Test - Real AngelOne SDK Integration

Tests real broker connectivity:
- SmartAPI authentication
- Real market data fetching
- Order placement & cancellation
- Error handling
"""
import sys
import logging
from src.utils.angelone_phase2 import AngelOnePhase2
from config import config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def print_header(title):
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}")

def test_phase2_auth():
    """Test real authentication."""
    print_header("PHASE 2 TEST: AUTHENTICATION")
    
    adapter = AngelOnePhase2()
    
    # Check credentials
    has_creds = bool(adapter.api_key and adapter.client_code)
    print(f"  ✓ Has credentials: {has_creds}")
    print(f"    - API Key: {adapter.api_key[:10]}..." if adapter.api_key else "    - API Key: None")
    print(f"    - Client Code: {adapter.client_code}")
    
    # Test login
    logger.info("Testing login...")
    ok = adapter.login()
    print(f"  ✓ Login: {'SUCCESS' if ok else 'FAILED'}")
    print(f"  ✓ Authenticated: {adapter.is_authenticated()}")
    print(f"  ✓ Token: {adapter._token[:20] if adapter._token else 'None'}...")
    
    # Test auto-refresh
    if not config.PAPER_TRADING:
        logger.info("Starting auto-refresh...")
        adapter.start_auto_refresh()
        print(f"  ✓ Auto-refresh started")
        adapter.stop_auto_refresh()
        print(f"  ✓ Auto-refresh stopped")
    
    return adapter

def test_phase2_ltp(adapter):
    """Test real LTP fetching."""
    print_header("PHASE 2 TEST: MARKET DATA (LTP)")
    
    symbols = ['NIFTY', 'NIFTY08JAN2620000CE', 'NIFTY08JAN2620000PE']
    
    for symbol in symbols:
        logger.info(f"Fetching LTP for {symbol}...")
        data = adapter.get_ltp(symbol)
        
        if data.get('status') == 'error':
            print(f"  ✗ {symbol}: ERROR - {data.get('reason')}")
        else:
            ltp = data.get('ltp', 0)
            bid = data.get('bid', 0)
            ask = data.get('ask', 0)
            print(f"  ✓ {symbol}:")
            print(f"    LTP: {ltp}, BID: {bid}, ASK: {ask}")

def test_phase2_orders(adapter):
    """Test order placement."""
    print_header("PHASE 2 TEST: ORDER PLACEMENT")
    
    # Build order
    order = {
        'symbol': 'NIFTY08JAN2620000CE',
        'qty': 75,
        'side': 'BUY',
        'price': 100.0,
        'type': 'LIMIT',
        'exchange': 'NFO'
    }
    
    logger.info(f"Placing order: {order}")
    resp = adapter.place_order(order)
    
    print(f"  ✓ Place order response:")
    print(f"    Status: {resp.get('status')}")
    print(f"    Order ID: {resp.get('orderid')}")
    print(f"    Message: {resp.get('message', 'OK')}")
    
    if resp.get('status') == 'success':
        order_id = resp['orderid']
        
        # Get status
        logger.info(f"Querying order status: {order_id}")
        status = adapter.get_order_status(order_id)
        print(f"  ✓ Order status: {status.get('status')}")
        
        # Cancel
        logger.info(f"Cancelling order: {order_id}")
        cancel = adapter.cancel_order(order_id)
        print(f"  ✓ Cancel response: {cancel.get('status')}")

def main():
    print("\n")
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  PHASE 2 VALIDATION TEST - Real AngelOne SDK Integration         ║")
    print("║  Testing SmartAPI connectivity and broker operations             ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    
    print(f"\nConfiguration:")
    print(f"  PAPER_TRADING: {config.PAPER_TRADING}")
    print(f"  DATA_SOURCE: {config.DATA_SOURCE}")
    print(f"  LOG_LEVEL: {getattr(config, 'LOG_LEVEL', 'INFO')}")
    
    try:
        # Test auth
        adapter = test_phase2_auth()
        
        if not adapter.is_authenticated():
            print("\n⚠️  WARNING: Not authenticated. Tests will use simulated data.")
            print("    Make sure credentials in .env are correct.")
        
        # Test market data
        test_phase2_ltp(adapter)
        
        # Test orders
        test_phase2_orders(adapter)
        
        # Summary
        print("\n╔══════════════════════════════════════════════════════════════════╗")
        if adapter.is_authenticated() and not config.PAPER_TRADING:
            print("║  PHASE 2 VALIDATION - REAL BROKER CONNECTED ✅                ║")
        else:
            print("║  PHASE 2 VALIDATION - SIMULATED MODE                            ║")
        print("╚══════════════════════════════════════════════════════════════════╝\n")
        
        return 0 if adapter.is_authenticated() or config.PAPER_TRADING else 1
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        print(f"\n✗ ERROR: {e}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())
