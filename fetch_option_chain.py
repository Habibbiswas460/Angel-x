#!/usr/bin/env python3
"""
Fetch Live Option Chain Data
Retrieves and displays option chain with Greeks for NIFTY/BANKNIFTY
"""

import sys
import json
from datetime import datetime
from config import config
from src.integrations.angelone.angelone_adapter import AngelOneAdapter
from src.integrations.angelone.smartapi_integration import SmartAPIClient
from src.utils.logger import StrategyLogger
from src.utils.options_helper import OptionsHelper

logger = StrategyLogger.get_logger(__name__)


def fetch_and_display_option_chain(underlying='NIFTY', strikes_range=5):
    """Fetch and display option chain data"""
    
    print("=" * 80)
    print(f"📊 FETCHING OPTION CHAIN DATA FOR {underlying}")
    print("=" * 80)
    print()
    
    try:
        # Initialize SmartAPI client
        print("🔐 Connecting to broker...")
        client = SmartAPIClient()
        
        if not client.is_authenticated():
            print("❌ Authentication failed. Check your API credentials in .env file")
            print()
            print("Required in .env:")
            print("  BROKER_API_KEY=<your_api_key>")
            print("  BROKER_CLIENT_ID=<your_client_id>")
            print("  BROKER_PASSWORD=<your_password>")
            print("  BROKER_TOTP_SECRET=<your_totp_secret>")
            return
        
        print("✅ Connected to broker")
        print()
        
        # Initialize adapter
        adapter = AngelOneAdapter(client)
        
        # Get current spot price
        print(f"📈 Fetching {underlying} spot price...")
        spot_price = adapter.get_ltp(underlying)
        
        if not spot_price:
            print(f"❌ Could not fetch spot price for {underlying}")
            return
        
        print(f"✅ {underlying} Spot: ₹{spot_price:,.2f}")
        print()
        
        # Get option chain
        print(f"🔍 Fetching option chain (ATM ±{strikes_range} strikes)...")
        chain = adapter.get_option_chain(underlying, spot_price, strikes_range)
        
        if not chain or not chain.get('strikes'):
            print("❌ No option chain data available")
            return
        
        print(f"✅ Option chain fetched")
        print()
        
        # Display option chain
        print("=" * 80)
        print(f"OPTION CHAIN: {underlying} | Expiry: {chain['expiry']} | ATM: {chain['atm_strike']}")
        print("=" * 80)
        print()
        print(f"{'Strike':<10} {'CE Symbol':<25} {'CE LTP':<10} {'PE Symbol':<25} {'PE LTP':<10}")
        print("-" * 80)
        
        # Sort strikes
        strikes = sorted(chain['strikes'].keys())
        atm = chain['atm_strike']
        
        for strike in strikes:
            strike_data = chain['strikes'][strike]
            ce_data = strike_data.get('CE', {})
            pe_data = strike_data.get('PE', {})
            
            # Mark ATM
            marker = " (ATM)" if strike == atm else ""
            
            print(f"{strike:<10} "
                  f"{ce_data.get('symbol', 'N/A'):<25} "
                  f"₹{ce_data.get('ltp', 0):<9.2f} "
                  f"{pe_data.get('symbol', 'N/A'):<25} "
                  f"₹{pe_data.get('ltp', 0):<9.2f}"
                  f"{marker}")
        
        print()
        print("=" * 80)
        
        # Calculate and display Greeks for ATM options
        print()
        print("📊 GREEKS FOR ATM OPTIONS")
        print("=" * 80)
        
        if atm in chain['strikes']:
            atm_data = chain['strikes'][atm]
            
            # CE Greeks
            ce_symbol = atm_data['CE']['symbol']
            ce_ltp = atm_data['CE']['ltp']
            
            print(f"\nCALL Option: {ce_symbol}")
            print(f"  LTP: ₹{ce_ltp:.2f}")
            
            # Calculate Greeks using helper
            ce_greeks = OptionsHelper.calculate_greeks(
                spot=spot_price,
                strike=atm,
                option_type='CE',
                ltp=ce_ltp,
                expiry_days=7  # Assuming weekly
            )
            
            if ce_greeks:
                print(f"  Delta: {ce_greeks.get('delta', 0):.4f}")
                print(f"  Gamma: {ce_greeks.get('gamma', 0):.4f}")
                print(f"  Theta: {ce_greeks.get('theta', 0):.4f}")
                print(f"  Vega: {ce_greeks.get('vega', 0):.4f}")
                print(f"  IV: {ce_greeks.get('iv', 0):.2f}%")
            
            # PE Greeks
            pe_symbol = atm_data['PE']['symbol']
            pe_ltp = atm_data['PE']['ltp']
            
            print(f"\nPUT Option: {pe_symbol}")
            print(f"  LTP: ₹{pe_ltp:.2f}")
            
            pe_greeks = OptionsHelper.calculate_greeks(
                spot=spot_price,
                strike=atm,
                option_type='PE',
                ltp=pe_ltp,
                expiry_days=7
            )
            
            if pe_greeks:
                print(f"  Delta: {pe_greeks.get('delta', 0):.4f}")
                print(f"  Gamma: {pe_greeks.get('gamma', 0):.4f}")
                print(f"  Theta: {pe_greeks.get('theta', 0):.4f}")
                print(f"  Vega: {pe_greeks.get('vega', 0):.4f}")
                print(f"  IV: {pe_greeks.get('iv', 0):.2f}%")
        
        print()
        print("=" * 80)
        
        # Save to file
        filename = f"option_chain_{underlying}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(chain, f, indent=2, default=str)
        
        print(f"💾 Option chain data saved to: {filename}")
        print()
        
    except Exception as e:
        logger.error(f"Error fetching option chain: {e}")
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    underlying = sys.argv[1] if len(sys.argv) > 1 else 'NIFTY'
    strikes_range = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    fetch_and_display_option_chain(underlying, strikes_range)
