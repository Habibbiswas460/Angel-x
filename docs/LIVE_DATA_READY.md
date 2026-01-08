# ANGEL-X Live Data Launch (Paper Trading)

All fixed! The system now:
- Logs into SmartAPI with your credentials
- Fetches real NIFTY/BANKNIFTY LTP ticks
- Runs paper trading (no real orders)
- Uses Greeks & OI data for entry/exit

## Quick Start

```bash
./run.sh
```

That's it! The script auto-loads `.env`, sets `PYTHONPATH` for the smartapi shim, and launches the strategy.

## What Changed

1. **SmartAPI Login**: Fixed TOTP-based auth; logs in successfully
2. **Live Ticks**: Real LTP polling from AngelOne (NIFTY: 26178.7 verified)
3. **Config**: Disabled demo/test mode; enabled WebSocket; reads from `.env`
4. **Shim**: Added `smartapi/` wrapper to fix SmartApi→smartapi import
5. **Index Tokens**: Corrected NIFTY (99926000) & BANKNIFTY (99926005)

## Current Mode

- **PAPER_TRADING**: `true` (orders simulated, no real execution)
- **DEMO_MODE**: `false` (live data, not simulated)
- **WEBSOCKET_ENABLED**: `true` (polling ticks every 1s)

## Verify

Check logs after start:
- ✓ SmartAPI login successful
- ✓ Subscribed to 1 instruments (SmartAPI REST polling)
- ✓ No "credentials missing → simulated ticks" warnings
- ✓ LTP updates flowing (source=SMARTAPI_REST)

## Next Steps (When Ready for Live Orders)

1. Set `PAPER_TRADING=false` in `.env`
2. Test with 1 lot first
3. Monitor Greeks-based exits closely

---

**Note**: Market is currently closed (Jan 6 evening). When you run now, SmartAPI will connect but LTP may be stale/last-close. During trading hours (9:15-15:30), ticks will be live.
