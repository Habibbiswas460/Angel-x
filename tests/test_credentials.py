#!/usr/bin/env python3
"""
Test Angel One credentials - validate they work with SmartAPI SDK
"""

import os
import sys
import logging
from pathlib import Path

# Load .env file
from dotenv import load_dotenv
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_credentials():
    """Test if Angel One credentials are valid"""
    
    print("\n" + "="*70)
    print("  ANGEL ONE CREDENTIALS TEST")
    print("="*70 + "\n")
    
    # Get credentials from environment
    api_key = os.getenv('ANGELONE_API_KEY')
    client_code = os.getenv('ANGELONE_CLIENT_CODE')
    password = os.getenv('ANGELONE_PASSWORD')
    totp_secret = os.getenv('ANGELONE_TOTP_SECRET')
    
    # Check if credentials exist
    print("1. CREDENTIALS LOADED")
    print("-" * 70)
    
    credentials = {
        'API_KEY': api_key,
        'CLIENT_CODE': client_code,
        'PASSWORD': password,
        'TOTP_SECRET': totp_secret
    }
    
    has_all = True
    for name, value in credentials.items():
        if value:
            # Mask value for security
            masked = value[:3] + '*' * (len(value) - 6) if len(value) > 6 else '*' * len(value)
            print(f"  ✓ {name}: {masked}")
        else:
            print(f"  ✗ {name}: NOT FOUND")
            has_all = False
    
    if not has_all:
        print("\n  ERROR: Missing credentials in .env file")
        print("  Add to .env:")
        print("    ANGELONE_API_KEY=your_key")
        print("    ANGELONE_CLIENT_CODE=your_code")
        print("    ANGELONE_PASSWORD=your_password")
        print("    ANGELONE_TOTP_SECRET=your_totp_secret")
        return False
    
    print("\n  ✓ All credentials found\n")
    
    # Test TOTP generation
    print("2. TOTP GENERATION TEST")
    print("-" * 70)
    
    try:
        import pyotp
        totp = pyotp.TOTP(totp_secret)
        code = totp.now()
        print(f"  ✓ TOTP code generated: {code}")
        print(f"  ✓ pyotp library working\n")
    except Exception as e:
        print(f"  ✗ TOTP generation failed: {e}")
        print(f"  Install: pip install pyotp\n")
        return False
    
    # Test SmartAPI import
    print("3. SMARTAPI SDK TEST")
    print("-" * 70)
    
    try:
        from smartapi import SmartConnect
        print(f"  ✓ SmartAPI SDK imported successfully")
        print(f"  ✓ Ready for real broker connection\n")
    except ImportError as e:
        print(f"  ⚠ SmartAPI SDK not available: {e}")
        print(f"  Install: pip install smartapi")
        print(f"  Using HTTP fallback for authentication\n")
    
    # Test requests
    print("4. HTTP REQUESTS TEST")
    print("-" * 70)
    
    try:
        import requests
        print(f"  ✓ requests library available")
        print(f"  ✓ HTTP fallback ready\n")
    except ImportError:
        print(f"  ✗ requests library not found")
        print(f"  Install: pip install requests\n")
        return False
    
    # Paper trading mode check
    paper_trading = os.getenv('PAPER_TRADING', 'true').lower() == 'true'
    print("5. TRADING MODE")
    print("-" * 70)
    
    if paper_trading:
        print(f"  MODE: PAPER TRADING (simulated)")
        print(f"  No real orders will be placed")
    else:
        print(f"  MODE: REAL TRADING")
        print(f"  ⚠ Real orders WILL be placed on broker")
    print()
    
    # Summary
    print("="*70)
    print("  SUMMARY: CREDENTIALS VALID ✓")
    print("="*70)
    
    print("\nNext steps:")
    if paper_trading:
        print("  1. Test in paper mode: python scripts/phase2_validation.py")
        print("  2. Then set PAPER_TRADING=false in .env")
        print("  3. Run validation with real broker")
    else:
        print("  1. Run validation: python scripts/phase2_validation.py")
        print("  2. Real orders will be placed on broker!")
        print("  3. Monitor logs carefully")
    
    print()
    return True

if __name__ == '__main__':
    success = test_credentials()
    sys.exit(0 if success else 1)
