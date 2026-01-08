#!/usr/bin/env python3
"""
Live Strike Selection Tool
Selects optimal strikes ATM ±3 based on live Greeks and IV from AngelOne

Usage:
  PYTHONPATH=. .venv/bin/python scripts/live_strike_selector.py [NIFTY|BANKNIFTY] [BULLISH|BEARISH]
"""

import os
import sys
from datetime import datetime
from tabulate import tabulate

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.integrations.angelone.smartapi_integration import SmartAPIClient
from app.integrations.angelone.angelone_adapter import AngelOneAdapter
from app.engines.strike_selection.auto_selector import AutoStrikeSelector


def print_section(title):
    """Print section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def fetch_live_spot(client: SmartAPIClient, underlying: str) -> float:
    """Fetch live spot price"""
    # Token mapping
    tokens = {
        "NIFTY": "99926000",
        "BANKNIFTY": "99926009"
    }
    
    token = tokens.get(underlying)
    if not token:
        print(f"❌ Unknown underlying: {underlying}")
        return 0.0
    
    try:
        ltp_data = client.get_ltp_data(
            exchange="NSE",
            trading_symbol=f"Nifty 50" if underlying == "NIFTY" else f"Nifty Bank",
            symbol_token=token
        )
        
        if ltp_data:
            return float(ltp_data.get('ltp', 0))
    except Exception as e:
        print(f"⚠️ Could not fetch live spot: {e}")
    
    # Fallback to estimated spot
    return 26178.70 if underlying == "NIFTY" else 56000.0


def select_strikes_live(underlying: str = "NIFTY", bias: str = "BULLISH"):
    """Select optimal strikes using live data"""
    
    print_section(f"LIVE STRIKE SELECTION - {underlying}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Bias: {bias}")
    
    # Validate inputs
    if underlying not in ["NIFTY", "BANKNIFTY"]:
        print(f"❌ Invalid underlying. Use NIFTY or BANKNIFTY")
        return
    
    if bias not in ["BULLISH", "BEARISH"]:
        print(f"❌ Invalid bias. Use BULLISH or BEARISH")
        return
    
    # Check environment
    api_key = os.getenv("ANGELONE_API_KEY")
    if not api_key:
        print("❌ ANGELONE_API_KEY not set in environment")
        return
    
    # Initialize SmartAPI client
    try:
        client = SmartAPIClient(
            api_key=os.getenv("ANGELONE_API_KEY"),
            client_code=os.getenv("ANGELONE_CLIENT_CODE"),
            password=os.getenv("ANGELONE_PASSWORD"),
            totp_secret=os.getenv("ANGELONE_TOTP_SECRET")
        )
        
        print("\n🔐 Logging in to AngelOne...")
        if not client.login():
            print("❌ Login failed")
            return
        
        print("✓ Login successful")
        
    except Exception as e:
        print(f"❌ SmartAPI initialization failed: {e}")
        return
    
    # Fetch live spot price
    print(f"\n📊 Fetching live {underlying} spot...")
    spot = fetch_live_spot(client, underlying)
    
    if spot == 0:
        print("❌ Could not fetch spot price")
        return
    
    print(f"✓ Spot Price: ₹{spot:,.2f}")
    
    # Strike parameters
    strike_interval = 50 if underlying == "NIFTY" else 100
    
    # Initialize auto selector
    selector = AutoStrikeSelector(atm_range=3)
    
    # Calculate ATM
    atm = round(spot / strike_interval) * strike_interval
    print(f"✓ ATM Strike: {atm}")
    
    # Get nearest expiry
    adapter = AngelOneAdapter()
    expiry = adapter.get_nearest_weekly_expiry()
    days_to_expiry = (expiry - datetime.now()).days
    print(f"✓ DTE: {days_to_expiry} days (Expiry: {expiry.strftime('%d-%b-%Y')})")
    
    # Select optimal strike
    print_section("OPTIMAL STRIKE SELECTION")
    
    selected = selector.select_optimal_strike(
        spot_price=spot,
        bias=bias,
        strike_interval=strike_interval,
        days_to_expiry=float(days_to_expiry),
        min_delta=0.35,
        max_delta=0.75,
        min_gamma=0.0005,
        prefer_atm=True
    )
    
    if not selected:
        print("❌ No suitable strike found")
        return
    
    print(f"\n✓ RECOMMENDED STRIKE: {selected.strike} {selected.option_type}")
    print(f"  Moneyness: ATM{selected.atm_offset:+d}" if selected.atm_offset != 0 else "  Moneyness: ATM")
    print(f"  LTP Estimate: ₹{selected.ltp:.2f}")
    print()
    print("  Greeks:")
    print(f"    Delta:  {selected.delta:.3f}  {'(Bullish directional)' if selected.delta > 0.5 else '(Balanced)'}")
    print(f"    Gamma:  {selected.gamma:.5f}  {'(High sensitivity)' if selected.gamma > 0.001 else '(Moderate)'}")
    print(f"    Theta:  {selected.theta:.2f}   (Decay/day)")
    print(f"    Vega:   {selected.vega:.2f}   (IV sensitivity)")
    print(f"    IV:     {selected.iv*100:.1f}%")
    print()
    print(f"  Scores:")
    print(f"    Greeks:    {selected.greeks_score:.1f}/100")
    print(f"    Total:     {selected.total_score:.1f}/100")
    
    # Get full ladder
    print_section("COMPLETE STRIKE LADDER (ATM ±3)")
    
    ladder = selector.get_strike_ladder(
        spot_price=spot,
        bias=bias,
        strike_interval=strike_interval,
        days_to_expiry=float(days_to_expiry)
    )
    
    table_data = []
    for idx, s in enumerate(ladder):
        moneyness = "ATM" if s.atm_offset == 0 else f"ATM{s.atm_offset:+d}"
        
        # Determine position type
        if s.option_type == "CE":
            if s.atm_offset < 0:
                pos_type = "ITM"
            elif s.atm_offset == 0:
                pos_type = "ATM"
            else:
                pos_type = "OTM"
        else:  # PE
            if s.atm_offset > 0:
                pos_type = "ITM"
            elif s.atm_offset == 0:
                pos_type = "ATM"
            else:
                pos_type = "OTM"
        
        # Highlight selected
        rank = "⭐ BEST" if idx == 0 else f"#{idx + 1}"
        
        table_data.append([
            rank,
            f"{s.strike} {s.option_type}",
            pos_type,
            moneyness,
            f"₹{s.ltp:.1f}",
            f"{s.delta:.3f}",
            f"{s.gamma:.5f}",
            f"{s.theta:.1f}",
            f"{s.vega:.1f}",
            f"{s.iv*100:.1f}%",
            f"{s.total_score:.1f}"
        ])
    
    headers = ["Rank", "Strike", "Type", "Moneyness", "LTP", "Delta", "Gamma", "Theta", "Vega", "IV", "Score"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary
    print()
    print("=" * 80)
    print("  SELECTION CRITERIA")
    print("=" * 80)
    print()
    print("Greeks Scoring:")
    print("  ✓ Delta: 0.40-0.65 (balanced directional + gamma)")
    print("  ✓ Gamma: >0.001 (high sensitivity near ATM)")
    print("  ✓ Theta: <20/day (controlled decay)")
    print("  ✓ Vega: 5-15 (moderate IV sensitivity)")
    print()
    print("Strike Types:")
    print("  • ITM (In-The-Money): Strike favorable to current spot")
    print("  • ATM (At-The-Money): Strike nearest to spot")
    print("  • OTM (Out-The-Money): Strike away from spot")
    print()
    print("IV (Implied Volatility):")
    print("  • Higher IV → Higher premium, more expensive")
    print("  • OTM options typically have higher IV")
    print("  • ITM options typically have lower IV")
    print()
    print("✅ Selection complete")


def main():
    """Main entry point"""
    underlying = sys.argv[1] if len(sys.argv) > 1 else "NIFTY"
    bias = sys.argv[2] if len(sys.argv) > 2 else "BULLISH"
    
    select_strikes_live(underlying.upper(), bias.upper())


if __name__ == "__main__":
    main()
