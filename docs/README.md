# Angel-X Docs

Minimal documentation set for the Angel-X trading system. Use this as the starting point for setup, integration, and daily operations.

## Files
- `docs/README.md` (this index)
- `docs/INTEGRATION.md` (broker/config setup and bringing the stack up)
- `docs/OPERATIONS.md` (health checks, common commands, endpoints)

## Snapshot
- WebSocket streaming with auto-reconnect and heartbeat
- Multi-leg strategies: Iron Condor, Straddle/Strangle, Bull/Bear/Calendar/Ratio spreads
- ML pipeline with fallbacks; dashboard publishes `ml` signals when data is available
- Docker-first deployment; healthcheck served at `/health`

## Quick Links
- Integration steps: see `docs/INTEGRATION.md`
- Daily operations: see `docs/OPERATIONS.md`
- Code reference: `src/` (notably `integration_hub.py`, `ml/`, `integrations/websocket/`)

## Quick Start (Docker)
```bash
sudo docker-compose up -d --build
curl http://localhost:5000/health
```

If you update dependencies or configs, rebuild with:
```bash
sudo docker-compose up -d --build
```
