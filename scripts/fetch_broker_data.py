#!/usr/bin/env python3
"""
Broker Data Fetcher - Get all live market data from AngelOne
Fetches: LTP, Positions, Orders, Holdings, Profile, Market Status
Run: PYTHONPATH=. .venv/bin/python scripts/fetch_broker_data.py
"""
import os
import sys
import json
from datetime import datetime
from tabulate import tabulate

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.integrations.angelone.smartapi_integration import SmartAPIClient
from app.integrations.angelone.angelone_client import AngelOneClient

REQUIRED_ENVS = [
    "ANGELONE_API_KEY",
    "ANGELONE_CLIENT_CODE",
    "ANGELONE_PASSWORD",
    "ANGELONE_TOTP_SECRET",
]

def check_env() -> bool:
    missing = [k for k in REQUIRED_ENVS if not os.getenv(k)]
    if missing:
        print(f"❌ Missing env vars: {', '.join(missing)}")
        print("Set them in .env and run: source .env")
        return False
    return True

def print_section(title):
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}")

def fetch_ltp(client: AngelOneClient, symbols=None):
    """Fetch LTP for given symbols"""
    if symbols is None:
        symbols = ["NIFTY", "BANKNIFTY"]
    
    print_section("LIVE LTP DATA")
    ltp_data = []
    for symbol in symbols:
        tick = client.get_ltp(symbol, "NSE")
        if tick and tick.get("ltp"):
            ltp_data.append([
                symbol,
                f"₹{tick['ltp']:,.2f}",
                tick.get('source', 'N/A'),
                datetime.fromtimestamp(tick.get('timestamp', 0)).strftime('%H:%M:%S')
            ])
    
    if ltp_data:
        print(tabulate(ltp_data, headers=['Symbol', 'LTP', 'Source', 'Time'], tablefmt='grid'))
    else:
        print("No LTP data available")

def fetch_profile(smart: SmartAPIClient):
    """Fetch user profile"""
    print_section("USER PROFILE")
    profile = smart.get_profile()
    if profile and profile.get('status'):
        data = profile['data']
        print(f"Name:         {data.get('name', 'N/A')}")
        print(f"Client Code:  {data.get('clientcode', 'N/A')}")
        print(f"Email:        {data.get('email', 'N/A')}")
        print(f"Mobile:       {data.get('mobileno', 'N/A')}")
        print(f"Exchanges:    {', '.join(data.get('exchanges', []))}")
        print(f"Products:     {', '.join(data.get('products', []))}")
    else:
        print("❌ Failed to fetch profile")

def fetch_positions(smart: SmartAPIClient):
    """Fetch current positions"""
    print_section("CURRENT POSITIONS")
    positions = smart.get_position()
    if positions:
        pos_list = []
        net_positions = positions.get('net', [])
        if net_positions:
            for pos in net_positions:
                pos_list.append([
                    pos.get('tradingsymbol', 'N/A'),
                    pos.get('netqty', 0),
                    f"₹{float(pos.get('buyavgprice', 0)):,.2f}",
                    f"₹{float(pos.get('ltp', 0)):,.2f}",
                    f"₹{float(pos.get('pnl', 0)):,.2f}",
                    pos.get('producttype', 'N/A')
                ])
            print(tabulate(pos_list, headers=['Symbol', 'Qty', 'Avg Price', 'LTP', 'P&L', 'Product'], tablefmt='grid'))
        else:
            print("No open positions")
    else:
        print("❌ Failed to fetch positions")

def fetch_orders(smart: SmartAPIClient):
    """Fetch today's orders"""
    print_section("TODAY'S ORDERS")
    orders = smart.get_order_book()
    if orders:
        order_list = []
        for order in orders[:10]:  # Show last 10 orders
            order_list.append([
                order.get('orderid', 'N/A')[:12],
                order.get('tradingsymbol', 'N/A'),
                order.get('transactiontype', 'N/A'),
                order.get('quantity', 0),
                f"₹{float(order.get('price', 0)):,.2f}",
                order.get('status', 'N/A'),
                order.get('ordertag', 'N/A')
            ])
        if order_list:
            print(tabulate(order_list, headers=['Order ID', 'Symbol', 'Type', 'Qty', 'Price', 'Status', 'Tag'], tablefmt='grid'))
        else:
            print("No orders today")
    else:
        print("❌ Failed to fetch orders")

def fetch_option_chain(smart: SmartAPIClient, underlying="NIFTY", strikes=5):
    """Fetch option chain data"""
    print_section(f"OPTION CHAIN - {underlying} (ATM ±{strikes})")
    
    # This is a placeholder - would need proper option chain API
    print(f"⚠️  Option chain fetch not yet implemented in SmartAPI wrapper")
    print(f"Use AngelOne option chain API endpoints for detailed Greeks/OI data")

def main():
    if not check_env():
        sys.exit(1)

    api_key = os.getenv("ANGELONE_API_KEY")
    client_code = os.getenv("ANGELONE_CLIENT_CODE")
    password = os.getenv("ANGELONE_PASSWORD")
    totp_secret = os.getenv("ANGELONE_TOTP_SECRET")

    print_section("ANGELONE BROKER DATA FETCHER")
    print(f"Client Code: {client_code}")
    print(f"Timestamp:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Login
    print("\n🔐 Logging in to SmartAPI...")
    smart = SmartAPIClient(
        api_key=api_key,
        client_code=client_code,
        password=password,
        totp_secret=totp_secret
    )
    
    if not smart.login():
        print("❌ Login failed")
        sys.exit(2)
    
    print("✅ Login successful")

    # Create client for LTP
    client = AngelOneClient(api_key=api_key, client_id=client_code)
    client.smart_client = smart
    client.connected = True

    # Fetch all data
    try:
        # User profile
        fetch_profile(smart)
        
        # Live LTP
        symbols = sys.argv[1:] if len(sys.argv) > 1 else ["NIFTY", "BANKNIFTY"]
        fetch_ltp(client, symbols)
        
        # Positions
        fetch_positions(smart)
        
        # Orders
        fetch_orders(smart)
        
        # Option chain (placeholder)
        # fetch_option_chain(smart, "NIFTY", 5)
        
        print_section("DATA FETCH COMPLETE")
        print("✅ All broker data fetched successfully")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(3)
    
    finally:
        smart.logout()
        print("\n🔒 Logged out")

if __name__ == "__main__":
    main()
