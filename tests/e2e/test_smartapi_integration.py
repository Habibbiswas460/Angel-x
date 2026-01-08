"""
Test SmartAPI Integration
Verify authentication, market data, and order placement
"""
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.integrations.angelone.angelone_adapter import AngelOneAdapter
from app.utils.logger import StrategyLogger

logger = StrategyLogger.get_logger(__name__)


def test_authentication():
    """Test 1: Authentication with SmartAPI."""
    print("\n" + "="*60)
    print("TEST 1: SmartAPI Authentication")
    print("="*60)
    
    try:
        # Initialize adapter
        adapter = AngelOneAdapter()
        
        # Login
        print("\n1. Attempting login...")
        if adapter.login():
            print("   ✓ Login successful!")
            
            # Check authentication
            if adapter.is_authenticated():
                print("   ✓ Session authenticated")
                print(f"   Token: {adapter._token[:20]}...")
            else:
                print("   ✗ Session NOT authenticated")
                return False
            
            # Start auto-refresh
            print("\n2. Starting auto-refresh...")
            adapter.start_auto_refresh()
            print("   ✓ Auto-refresh thread started")
            
            return True
        else:
            print("   ✗ Login failed")
            return False
            
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        return False


def test_market_checks():
    """Test 2: Market status checks."""
    print("\n" + "="*60)
    print("TEST 2: Market Status Checks")
    print("="*60)
    
    try:
        adapter = AngelOneAdapter()
        adapter.login()
        
        # Check market status
        print("\n1. Checking market status...")
        is_open = adapter.is_market_open()
        print(f"   Market open: {is_open}")
        
        is_trading_day = adapter.is_trading_day()
        print(f"   Trading day: {is_trading_day}")
        
        # Validate conditions
        print("\n2. Validating market conditions...")
        is_safe, reason = adapter.validate_market_conditions()
        print(f"   Safe to trade: {is_safe}")
        print(f"   Reason: {reason}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        return False


def test_symbol_resolution():
    """Test 3: Symbol resolution and option chain."""
    print("\n" + "="*60)
    print("TEST 3: Symbol Resolution & Option Chain")
    print("="*60)
    
    try:
        adapter = AngelOneAdapter()
        adapter.login()
        
        # Resolve underlying
        print("\n1. Resolving underlying token...")
        token = adapter.resolve_underlying_token('NIFTY')
        print(f"   NIFTY token: {token}")
        
        # Get expiry
        print("\n2. Calculating next expiry...")
        expiry = adapter.get_nearest_weekly_expiry()
        expiry_str = adapter.format_expiry(expiry)
        print(f"   Next expiry: {expiry_str}")
        
        # Calculate ATM
        print("\n3. Calculating ATM strike...")
        spot = 20000.0
        atm = adapter.calc_atm_strike(spot, 50)
        print(f"   Spot: {spot}, ATM: {atm}")
        
        # Build option symbol
        print("\n4. Building option symbol...")
        ce_symbol = adapter.build_option_symbol('NIFTY', expiry, atm, 'CE')
        pe_symbol = adapter.build_option_symbol('NIFTY', expiry, atm, 'PE')
        print(f"   CE: {ce_symbol}")
        print(f"   PE: {pe_symbol}")
        
        # Validate symbols
        print("\n5. Validating symbols...")
        ce_valid = adapter.validate_symbol(ce_symbol)
        pe_valid = adapter.validate_symbol(pe_symbol)
        print(f"   CE valid: {ce_valid}")
        print(f"   PE valid: {pe_valid}")
        
        # Get option chain
        print("\n6. Fetching option chain (ATM ±5)...")
        chain = adapter.get_option_chain('NIFTY', spot, strikes_range=5)
        print(f"   Underlying: {chain['underlying']}")
        print(f"   Expiry: {chain['expiry']}")
        print(f"   ATM: {chain['atm_strike']}")
        print(f"   Strikes count: {len(chain['strikes'])}")
        
        # Display strikes
        print("\n   Strike details:")
        for strike, data in sorted(chain['strikes'].items()):
            ce_ltp = data['CE']['ltp']
            pe_ltp = data['PE']['ltp']
            print(f"     {strike}: CE={ce_ltp:.2f}, PE={pe_ltp:.2f}")
        
        return True
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_order_placement():
    """Test 4: Order placement (PAPER mode)."""
    print("\n" + "="*60)
    print("TEST 4: Order Placement (PAPER MODE)")
    print("="*60)
    
    try:
        adapter = AngelOneAdapter()
        adapter.login()
        
        # Build test order
        print("\n1. Building test order...")
        expiry = adapter.get_nearest_weekly_expiry()
        spot = 20000.0
        atm = adapter.calc_atm_strike(spot, 50)
        symbol = adapter.build_option_symbol('NIFTY', expiry, atm, 'CE')
        
        order_payload = {
            'symbol': symbol,
            'qty': 1,
            'side': 'BUY',
            'price': 100.0,
            'type': 'MARKET',
            'product': 'INTRADAY'
        }
        
        print(f"   Order: {order_payload}")
        
        # Place order
        print("\n2. Placing order...")
        result = adapter.place_order(order_payload)
        print(f"   Status: {result.get('status')}")
        print(f"   Order ID: {result.get('orderid')}")
        
        if result.get('status') == 'success':
            order_id = result['orderid']
            
            # Get order status
            print("\n3. Checking order status...")
            status = adapter.get_order_status(order_id)
            print(f"   Status: {status.get('status')}")
            
            # Cancel order
            print("\n4. Cancelling order...")
            cancel_result = adapter.cancel_order(order_id)
            print(f"   Cancel status: {cancel_result.get('status')}")
            
            return True
        else:
            print(f"   ✗ Order placement failed")
            return False
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_smartapi_direct():
    """Test 5: Direct SmartAPI client test."""
    print("\n" + "="*60)
    print("TEST 5: Direct SmartAPI Client Test")
    print("="*60)
    
    try:
        from app.integrations.angelone.smartapi_integration import SmartAPIClient
        
        # Get credentials
        api_key = os.getenv('ANGELONE_API_KEY')
        client_code = os.getenv('ANGELONE_CLIENT_CODE')
        password = os.getenv('ANGELONE_PASSWORD')
        totp_secret = os.getenv('ANGELONE_TOTP_SECRET')
        
        if not all([api_key, client_code, password, totp_secret]):
            print("   ⚠ Credentials not found in environment")
            print("   Set ANGELONE_API_KEY, ANGELONE_CLIENT_CODE, ANGELONE_PASSWORD, ANGELONE_TOTP_SECRET")
            return False
        
        # Initialize client
        print("\n1. Initializing SmartAPI client...")
        client = SmartAPIClient(api_key, client_code, password, totp_secret)
        print("   ✓ Client initialized")
        
        # Login
        print("\n2. Logging in...")
        if client.login():
            print("   ✓ Login successful")
            print(f"   Auth Token: {client.auth_token[:20]}...")
            print(f"   Feed Token: {client.feed_token[:20]}...")
            
            # Get profile
            print("\n3. Getting profile...")
            profile = client.get_profile()
            if profile and 'data' in profile:
                print(f"   Name: {profile['data'].get('name')}")
                print(f"   Email: {profile['data'].get('email')}")
            
            # Get RMS limits
            print("\n4. Getting RMS limits...")
            rms = client.get_rms_limits()
            if rms:
                print(f"   Available Margin: ₹{rms.get('availablecash', 0)}")
            
            # Logout
            print("\n5. Logging out...")
            client.logout()
            print("   ✓ Logout successful")
            
            return True
        else:
            print("   ✗ Login failed")
            return False
        
    except Exception as e:
        print(f"   ✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("SmartAPI Integration Test Suite")
    print("="*60)
    
    # Check environment
    paper_trading = os.getenv('PAPER_TRADING', 'True').lower() == 'true'
    print(f"\nPAPER_TRADING: {paper_trading}")
    
    results = []
    
    # Run tests
    results.append(('Authentication', test_authentication()))
    results.append(('Market Checks', test_market_checks()))
    results.append(('Symbol Resolution', test_symbol_resolution()))
    results.append(('Order Placement', test_order_placement()))
    
    # Only run direct SmartAPI test if credentials available
    if not paper_trading:
        results.append(('SmartAPI Direct', test_smartapi_direct()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name:.<40} {status}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(r for _, r in results)


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
