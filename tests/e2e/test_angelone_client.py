"""
Quick AngelOne client test:
- Checks required env vars
- Attempts SmartAPI login
- Fetches one LTP tick for NIFTY (or symbol from CLI)
Run: .venv/bin/python scripts/test_angelone_client.py [SYMBOL]
"""
import os
import sys
import time

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
        print(f"Missing env vars: {', '.join(missing)}")
        return False
    return True

def main():
    symbol = sys.argv[1].upper() if len(sys.argv) > 1 else "NIFTY"

    if not check_env():
        print("Set the required env vars and retry.")
        sys.exit(1)

    api_key = os.getenv("ANGELONE_API_KEY")
    client_code = os.getenv("ANGELONE_CLIENT_CODE")
    password = os.getenv("ANGELONE_PASSWORD")
    totp = os.getenv("ANGELONE_TOTP_SECRET")

    print(f"Logging in with client_code={client_code} ...")
    smart = SmartAPIClient(api_key=api_key, client_code=client_code, password=password, totp_secret=totp)
    if not smart.login():
        print("Login failed")
        sys.exit(2)
    print("Login OK")

    client = AngelOneClient(api_key=api_key, client_id=client_code)
    client.smart_client = smart  # reuse logged-in session
    client.connected = True

    print(f"Fetching LTP for {symbol} ...")
    tick = client.get_ltp(symbol)
    if tick and tick.get("ltp") is not None:
        print(f"LTP {symbol}: {tick['ltp']} (source={tick.get('source')})")
        sys.exit(0)
    else:
        print("Failed to fetch LTP")
        sys.exit(3)

if __name__ == "__main__":
    main()
