# Operations

Daily commands and checks for Angel-X.

## Health and Status
- Healthcheck: `curl http://localhost:5000/health`
- Container status: `sudo docker-compose ps`
- Logs (app): `sudo docker-compose logs -f angel-x-trading`
- Logs (db): `sudo docker-compose logs -f angel-x-postgres`

## Start/Stop
```bash
# start (build if needed)
sudo docker-compose up -d --build

# stop
sudo docker-compose down
```

## Rebuild and Refresh
```bash
sudo docker-compose down
sudo docker-compose up -d --build
```

## API Surface (common)
- `/api/dashboard`
- `/api/positions`
- `/api/portfolio`
- `/api/market`
- `/api/performance`
- `/api/trades`
- `/api/greeks-heatmap`
- `/health`

## Testing
- In-container (pytest bundled):
```bash
sudo docker-compose exec angel-x-trading python3 -m pytest tests -q --tb=short
```
- Local venv:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-test.txt
pytest tests -q --tb=short
```

## ML Signals Quick Check
- Ensure CSVs exist in `ticks/`.
- Call dashboard API and look for `ml` section:
```bash
curl http://localhost:5000/api/dashboard | jq '.ml'
```

## Troubleshooting
- If health fails: check logs, ensure config credentials are set, and rebuild.
- If WebSocket disconnects: client auto-reconnects; restart container if persistent.
- If ML missing: add tick data or install optional deps (`tensorflow-cpu`, `xgboost`) and rebuild.
